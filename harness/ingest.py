"""Ingestion: originals in vault/raw/ -> source catalog, retrieval index, wiki notes, index.md.

Flow for `wiki ingest ./vault/raw`:
  1. Catalogue every .md/.txt source (id, path, sha256). Originals are only read, never written.
  2. Rebuild the retrieval chunks from the originals (.index/chunks.json, outside the vault).
  3. For each note in data/wiki_plan.json: pull the listed source sections, send them with
     prompts/ingest-instructions.md to local Gemma, and assemble the note. The harness (not
     the model) writes the title, front matter, related links and source references, so links
     and filenames are always valid.
  4. Rewrite vault/index.md grouped by topic folder.

Re-ingesting is idempotent: filenames come from the plan, so a note is updated in place.
A note marked `reviewed: true` is never silently overwritten; the new draft goes to
.index/drafts/ for comparison unless --force is given.
"""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from .config import ROOT, p
from .retrieval import build_index, split_sections

SUPPORTED = {".md", ".txt"}


def load_plan(cfg):
    return json.loads(p(cfg, "plan_file").read_text(encoding="utf-8"))


def slug_id(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def build_catalog(cfg, raw_dir, plan):
    by_file = {v["file"]: (k, v) for k, v in plan["sources"].items()}
    catalog = []
    for f in sorted(Path(raw_dir).iterdir()):
        if f.suffix.lower() not in SUPPORTED or not f.is_file():
            continue
        data = f.read_bytes()
        sid, meta = by_file.get(f.name, (slug_id(f.stem), {}))
        catalog.append(
            {
                "id": sid,
                "path": f.relative_to(ROOT).as_posix(),
                "title": meta.get("title", f.stem),
                "origin": meta.get("origin", "added to vault/raw by hand"),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "note_name": f.stem,
            }
        )
    if not catalog:
        raise SystemExit(f"No .md or .txt sources found in {raw_dir}")
    out = p(cfg, "catalog_file")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    return catalog


def _match(spec, path):
    """Match a plan section spec against a heading path.

    'A > B' specs match the end of the full path; plain specs match the leaf heading only,
    so a document title does not pull in every subsection beneath it.
    """
    spec_l = spec.lower()
    if ">" in spec:
        return path.lower().endswith(spec_l)
    return spec_l in path.split(" > ")[-1].lower()


def gather_excerpts(note, catalog, max_chars):
    by_id = {c["id"]: c for c in catalog}
    picked = []  # (source_id, section_path, start, end, body)
    for sid, specs in note["excerpts"].items():
        src = by_id.get(sid)
        if not src:
            continue
        text = (ROOT / src["path"]).read_text(encoding="utf-8")
        for path, start, end, body in split_sections(text):
            if any(_match(s, path) for s in specs):
                picked.append((sid, src, path, start, end, body.strip()))
    if not picked:
        return [], ""
    budget = max_chars // len(picked)
    parts, refs = [], []
    for n, (sid, src, path, start, end, body) in enumerate(picked, 1):
        clipped = body if len(body) <= budget else body[:budget].rsplit("\n", 1)[0] + "\n[…excerpt clipped…]"
        label = f"E{n}"
        parts.append(f"[{label}] {src['note_name']} — {path.split(' > ')[-1]} (lines {start}-{end})\n{clipped}")
        refs.append({"label": label, "source": src, "section": path.split(" > ")[-1], "lines": f"{start}-{end}"})
    return refs, "\n\n".join(parts)


def read_frontmatter(path):
    txt = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    return fm, txt


def clean_model_output(text):
    """Keep only the two sections the model is asked for; drop titles or stray fences."""
    text = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", text.strip())
    start = text.find("## Summary")
    return (text[start:] if start >= 0 else "## Summary\n" + text).strip()


def render_note(note, refs, body, model_id, cfg):
    today = dt.date.today().isoformat()
    source_ids = sorted({r["source"]["id"] for r in refs})
    fm = [
        "---",
        f"title: {note['title']}",
        f"topic: {note['folder']}",
        f"source_ids: [{', '.join(source_ids)}]",
        f"note_id: {slug_id(note['title'])}",
        f"generated_by: {model_id}",
        f"generated_on: {today}",
        "reviewed: false",
        "---",
    ]
    lines = fm + [
        "",
        f"# {note['title']}",
        "",
        f"*{note['description']}* · Topic: {note['folder']} · Back to [[index]]",
        "",
        body,
        "",
        "## Related notes",
        "",
    ]
    for target, why in note["related"]:
        lines.append(f"- [[{target}]] — {why}")
    lines += ["", "## Sources", "", "Excerpt labels (E1, E2, …) in the details above refer to:", ""]
    for r in refs:
        lines.append(f"- {r['label']}: [[{r['source']['note_name']}]] — section \"{r['section']}\", lines {r['lines']}")
    return "\n".join(lines) + "\n"


def note_path(cfg, note):
    return p(cfg, "wiki_dir") / note["folder"] / f"{note['title']}.md"


def write_index(cfg, plan, catalog):
    lines = [
        "# Jack's AI Course Wiki",
        "",
        "Personal notes from *From Zero to AI Agents* (Berkeley Haas, fall 2026), built from my own",
        "project write-ups. Start with a project, follow its links into the concepts, and use",
        "each note's **Sources** list to get back to the original text in `raw/`.",
        "",
    ]
    for folder, blurb in plan["folders"].items():
        lines += [f"## {folder}", "", blurb, ""]
        for n in plan["notes"]:
            if n["folder"] == folder:
                lines.append(f"- [[{n['title']}]] — {n['description']}")
        lines.append("")
    planned_ids = set(plan["sources"])
    extra = [c for c in catalog if c["id"] not in planned_ids]
    if extra:
        lines += ["## Sources (unplanned)", "", "Added to raw/ but not yet mapped in the wiki plan:", ""]
        for c in extra:
            lines.append(f"- [[Source - {c['note_name']}]]")
        lines.append("")
    lines += ["## Original sources", "", "Unchanged originals. Every wiki note cites these.", ""]
    for c in catalog:
        lines.append(f"- [[{c['note_name']}]] — {c['title']}")
    lines.append("")
    p(cfg, "index_file").write_text("\n".join(lines), encoding="utf-8")


def unplanned_notes(catalog, plan):
    """A raw file with no plan entry still gets one summary note, so nothing is silently skipped."""
    planned = set(plan["sources"])
    out = []
    for c in catalog:
        if c["id"] in planned:
            continue
        out.append(
            {
                "title": f"Source - {c['note_name']}",
                "folder": "Sources",
                "description": f"Summary of {c['note_name']}, not yet linked into the topic notes.",
                "purpose": "Summarise this source so it can later be merged into topic notes.",
                "excerpts": {c["id"]: [""]},  # empty spec matches every section
                "related": [],
            }
        )
    return out


def ingest(cfg, client, raw_dir, only=None, source=None, force=False, dry_run=False, log=print):
    plan = load_plan(cfg)
    raw_dir = Path(raw_dir).resolve()
    if not raw_dir.exists():
        raise SystemExit(f"Source folder not found: {raw_dir}")
    catalog = build_catalog(cfg, raw_dir, plan)
    log(f"Catalogued {len(catalog)} original source(s): " + ", ".join(c["id"] for c in catalog))
    chunks = build_index(cfg, catalog)
    log(f"Retrieval index rebuilt: {len(chunks)} passages -> {p(cfg, 'chunks_file').relative_to(ROOT)}")

    instructions = (ROOT / "prompts" / "ingest-instructions.md").read_text(encoding="utf-8")
    notes = plan["notes"] + unplanned_notes(catalog, plan)
    if only:
        notes = [n for n in notes if n["title"].lower() == only.lower()]
        if not notes:
            raise SystemExit(f"No planned note titled '{only}'. See data/wiki_plan.json")
    if source:  # re-ingest one original: regenerate only the notes that draw on it
        notes = [n for n in notes if source in n["excerpts"]]
        if not notes:
            raise SystemExit(f"No notes use source id '{source}'. Ids: " + ", ".join(c["id"] for c in catalog))
    results = []
    for note in notes:
        refs, excerpt_text = gather_excerpts(note, catalog, cfg["ingest_max_source_chars"])
        target = note_path(cfg, note)
        rel = target.relative_to(ROOT).as_posix()
        if not refs:
            log(f"  skip {rel}: none of its source sections were found")
            results.append({"note": rel, "status": "skipped-no-sources"})
            continue
        if dry_run:
            log(f"  would write {rel} from {len(refs)} excerpt(s), {len(excerpt_text)} chars")
            continue
        user = (
            f"Page topic: {note['title']}\nPurpose: {note['purpose']}\n\n"
            f"Source excerpts:\n\n{excerpt_text}\n\nWrite the page now."
        )
        text, stats = client.chat(
            [{"role": "system", "content": instructions}, {"role": "user", "content": user}],
            temperature=cfg["ingest_temperature"],
        )
        content = render_note(note, refs, clean_model_output(text), stats.get("model", client.model), cfg)
        status = "created"
        if target.exists():
            fm, old = read_frontmatter(target)
            if fm.get("reviewed") == "true" and not force:
                draft = p(cfg, "drafts_dir") / f"{note['title']}.md"
                draft.parent.mkdir(parents=True, exist_ok=True)
                draft.write_text(content, encoding="utf-8")
                status = "kept-reviewed (new draft in .index/drafts/)"
            else:
                status = "updated"
        if status in ("created", "updated"):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        log(f"  {status:9s} {rel}  ({stats.get('wall_seconds')} s)")
        results.append({"note": rel, "status": status, "excerpts": len(refs), "input_chars": len(excerpt_text), **stats})
    if not dry_run and not only and not source:
        write_index(cfg, plan, catalog)
        log(f"Index written: {p(cfg, 'index_file').relative_to(ROOT)}")
    return {"catalog": catalog, "passages": len(chunks), "notes": results}
