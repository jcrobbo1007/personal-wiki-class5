"""`wiki check`: review aid for generated notes.

Checks every note in vault/ for:
  - filename == first heading, and a readable (non machine-style) filename
  - every [[link]] resolving to exactly one file in the vault
  - a Sources section pointing at raw/
  - numbers in the note that do not appear in any cited original (likely invented)
  - notes on disk that are not in the plan (possible duplicates or strays)
"""
import json
import re
from collections import defaultdict

from .config import ROOT, p
from .ingest import load_plan, note_path, read_frontmatter

LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
NUM = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?")
MACHINE = re.compile(r"([0-9a-f]{8,}|\d{8}|--|_{2,}|chunk|task-\d)", re.I)


def run_check(cfg):
    vault = p(cfg, "vault_dir")
    files = [f for f in vault.rglob("*.md") if ".obsidian" not in f.parts]
    names = defaultdict(list)
    for f in files:
        names[f.stem].append(f)
    plan = load_plan(cfg)
    planned = {note_path(cfg, n).resolve() for n in plan["notes"]}
    catalog = json.loads(p(cfg, "catalog_file").read_text(encoding="utf-8")) if p(cfg, "catalog_file").exists() else []
    raw_text = {c["note_name"]: (ROOT / c["path"]).read_text(encoding="utf-8") for c in catalog}

    report = {"notes": [], "problems": 0}
    for f in sorted(p(cfg, "wiki_dir").rglob("*.md")):
        issues = []
        fm, txt = read_frontmatter(f)
        h1 = re.search(r"^# (.+)$", txt, re.M)
        if not h1 or h1.group(1).strip() != f.stem:
            issues.append(f"first heading does not match filename ('{h1.group(1) if h1 else None}')")
        if MACHINE.search(f.stem) or len(f.stem.split()) > 6:
            issues.append("filename looks machine-generated or too long")
        if f.resolve() not in planned and not f.stem.startswith("Source - "):
            issues.append("not in data/wiki_plan.json (duplicate or stray note?)")
        for target in LINK.findall(txt):
            hits = names.get(target.strip(), [])
            if len(hits) != 1:
                issues.append(f"link [[{target}]] resolves to {len(hits)} files")
        cited = [n for n in raw_text if f"[[{n}]]" in txt]
        if not cited:
            issues.append("no source reference to an original in raw/")
        body = txt.split("## Related notes")[0]
        body = body.split("---", 2)[-1]  # drop front matter
        evidence = " ".join(raw_text[n] for n in cited).replace(",", "")
        unsupported = sorted(
            {n for n in NUM.findall(body) if n.replace(",", "").rstrip("%") not in evidence and not re.fullmatch(r"\d", n)}
        )
        if unsupported:
            issues.append("numbers not found in cited sources: " + ", ".join(unsupported))
        report["notes"].append(
            {"note": f.relative_to(ROOT).as_posix(), "reviewed": fm.get("reviewed"), "issues": issues}
        )
        report["problems"] += len(issues)
    for n in plan["notes"]:
        if not note_path(cfg, n).exists():
            report["notes"].append({"note": note_path(cfg, n).relative_to(ROOT).as_posix(), "issues": ["planned but missing"]})
            report["problems"] += 1
    dupes = {k: [x.relative_to(ROOT).as_posix() for x in v] for k, v in names.items() if len(v) > 1}
    if dupes:
        report["duplicate_names"] = dupes
        report["problems"] += len(dupes)
    return report
