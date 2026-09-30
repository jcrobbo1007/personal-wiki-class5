#!/usr/bin/env python3
"""wiki — a personal-wiki CLI over local Gemma + RAG.

Run `python wiki.py --help` (or `wiki --help` via wiki.cmd on Windows).
Every command runs locally; there is no cloud fallback.
"""
import argparse
import datetime as dt
import json
import sys
import time

from harness.config import ROOT, load_config, p
from harness.llm import ModelUnavailable, make_client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HELP = """\
wiki — personal wiki CLI (local Gemma + RAG)

Commands
  wiki ingest ./vault/raw        Catalogue the originals, rebuild the retrieval index, have
                                 local Gemma write the linked wiki notes, refresh vault/index.md.
      --note "Title"             regenerate one planned note only
      --source ID                re-ingest one original (e.g. mnist): only notes built from it
      --force                    overwrite notes marked reviewed: true
      --dry-run                  show what would be written, no model calls
  wiki index                     Rebuild only the retrieval index (no model needed).
  wiki search "query"            Show original passages + file paths + line numbers.
                                 No answer is generated; works without the model running.
  wiki ask "question"            Standalone factual answer from retrieved evidence, with
                                 citations, or INSUFFICIENT EVIDENCE. Ignores chat history.
      --save                     also write an evidence card to evidence/ask/
  wiki chat                      Talk to Margin, the study-partner persona. Uses the conversation
                                 and looks up notes only when a message needs them.
                                 In chat: /notes <q>  /reset  /help  /exit
  wiki check                     Review aid: filenames, headings, links, sources, and numbers
                                 in notes that do not appear in the cited originals.
  wiki doctor                    Device specs, runtime and model identity, internet status.
  wiki eval --out NAME           Run the four fixed ask tests (tests/questions.json) and save
                                 evidence cards to evidence/NAME/.
  wiki modecheck --out NAME      Run the chat/search/ask boundary checks and save a transcript.

Options (any command)
  --mode local                   Execution setting. Only 'local' exists; it is the default.
  --model NAME                   Override the Ollama model (default from config.json).

Configuration: config.json (model, Ollama URL, context size, retrieval settings).
Instructions:  prompts/persona.md (chat), prompts/wiki-instructions.md (ask),
               prompts/ingest-instructions.md (ingest). The harness loads these; the
               model does not read files itself.
Requires:      Python 3.10+ (standard library only) and Ollama with the model pulled.
"""


def get_client(cfg):
    return make_client(cfg)


def cmd_ingest(cfg, a):
    from harness.ingest import ingest
    from harness.system import internet_reachable

    client = get_client(cfg)
    t0 = time.perf_counter()
    res = ingest(cfg, client, a.path, only=a.note, source=a.source, force=a.force, dry_run=a.dry_run)
    res["wall_seconds"] = round(time.perf_counter() - t0, 1)
    res["internet_reachable"] = internet_reachable()
    res["model"] = client.model
    res["run_at"] = dt.datetime.now().isoformat(timespec="seconds")
    out = p(cfg, "evidence_dir") / "logs" / f"ingest-{dt.datetime.now():%Y%m%d-%H%M%S}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Done in {res['wall_seconds']} s. Internet reachable: {res['internet_reachable']}. Log: {out.relative_to(ROOT)}")


def cmd_index(cfg, a):
    from harness.ingest import build_catalog, load_plan
    from harness.retrieval import build_index

    cat = build_catalog(cfg, p(cfg, "raw_dir"), load_plan(cfg))
    print(f"Indexed {len(build_index(cfg, cat))} passages from {len(cat)} sources.")


def print_passages(results):
    from harness.retrieval import format_passage

    if not results:
        print("No matching passages.")
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {format_passage(r)}  score {r['score']}")
        print("    " + r["text"].strip().replace("\n", "\n    "))


def cmd_search(cfg, a):
    from harness.evidence import log_record
    from harness.retrieval import load_index

    res = load_index(cfg).search(a.query, k=a.k or cfg["search_top_k"])
    print(f"search (no model call) — {len(res)} passage(s) for: {a.query}")
    print_passages(res)
    log_record(cfg, {"mode": "search", "execution": "local", "model_called": False, "query": a.query, "results": res})


def print_ask(rec):
    print(f"ask · {rec['execution']} · {rec['model']} · retrieved {len(rec['retrieved'])} passage(s)\n")
    print(rec["answer"])
    print("\nCitations:")
    for c in rec["citations"] or []:
        print(f"  [{c['label']}] {c['path']} — {c['section']} — lines {c['lines']}")
    if not rec["citations"]:
        print("  none")
    print(f"Check: {rec['check']['status']}" + ("".join(f"\n  - {n}" for n in rec["check"]["notes"])))
    if rec.get("stats"):
        print(f"Time: {rec['stats'].get('wall_seconds')} s")


def cmd_ask(cfg, a):
    from harness.evidence import log_record, save_ask_card
    from harness.modes import ask
    from harness.retrieval import load_index
    from harness.system import internet_reachable

    rec = ask(cfg, get_client(cfg), load_index(cfg), a.question)
    print_ask(rec)
    log_record(cfg, rec)
    if a.save:
        info = {"internet_reachable": internet_reachable(), "run_at": dt.datetime.now().isoformat(timespec="seconds")}
        print(f"Saved: {save_ask_card(cfg, rec, None, info, 'ask').relative_to(ROOT)}")


def cmd_chat(cfg, a):
    from harness.evidence import log_record
    from harness.modes import ChatSession
    from harness.retrieval import load_index

    s = ChatSession(cfg, get_client(cfg), load_index(cfg))
    print(f"Margin (chat · local · {s.client.model}). Type /help for commands, /exit to leave.")
    while True:
        try:
            msg = input("\nyou > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not msg:
            continue
        if msg in ("/exit", "/quit"):
            break
        if msg == "/help":
            print("/notes <question> look up notes for this turn · /reset clear the conversation · /exit leave")
            continue
        if msg == "/reset":
            s.reset()
            print("(conversation cleared)")
            continue
        force = msg.startswith("/notes ")
        if force:
            msg = msg[len("/notes "):]
        try:
            rec = s.turn(msg, force_notes=force)
        except ModelUnavailable as e:
            print(f"error: {e}")
            continue
        tag = "notes: " + ("used" if rec["retrieval"]["used"] else "not used") + f" ({rec['retrieval']['reason']})"
        print(f"\nmargin > {rec['reply']}\n\n  [{tag}]")
        log_record(cfg, rec)


def cmd_check(cfg, a):
    from harness.check import run_check

    rep = run_check(cfg)
    for n in rep["notes"]:
        mark = "OK " if not n["issues"] else "!! "
        print(f"{mark}{n['note']}  (reviewed: {n.get('reviewed')})")
        for i in n["issues"]:
            print(f"     - {i}")
    for k, v in rep.get("duplicate_names", {}).items():
        print(f"!! duplicate note name '{k}': {v}")
    print(f"\n{rep['problems']} issue(s).")
    if a.out:
        out = p(cfg, "evidence_dir") / a.out / "wiki-check.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=2), encoding="utf-8")


def runtime_info(cfg):
    from harness.system import ollama_process_memory_gb

    info = {}
    try:
        info = get_client(cfg).info()
    except ModelUnavailable as e:
        info = {"error": str(e)}
    info["ollama_process_memory_gb"] = ollama_process_memory_gb()
    return info


def cmd_doctor(cfg, a):
    from harness.system import device_specs, internet_reachable

    rep = {"device": device_specs(), "runtime": runtime_info(cfg), "internet_reachable": internet_reachable(),
           "config": {k: cfg[k] for k in ("model", "ollama_url", "num_ctx", "ask_top_k", "chunk_words")}}
    print(json.dumps(rep, indent=2))
    if a.out:
        out = p(cfg, "evidence_dir") / a.out / "doctor.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print(f"Saved: {out.relative_to(ROOT)}")


def cmd_eval(cfg, a):
    from harness.evidence import log_record, save_ask_card
    from harness.modes import ask
    from harness.retrieval import load_index
    from harness.system import internet_reachable

    tests = json.loads((ROOT / "tests" / "questions.json").read_text(encoding="utf-8"))["ask_tests"]
    client, index = get_client(cfg), load_index(cfg)
    online = internet_reachable()
    summary = []
    for t in tests:
        info = {"internet_reachable": online, "run_at": dt.datetime.now().isoformat(timespec="seconds")}
        rec = ask(cfg, client, index, t["question"])
        log_record(cfg, rec)
        path = save_ask_card(cfg, rec, t, info, a.out)
        from harness.evidence import auto_assess

        row = {"id": t["id"], "status": rec["check"]["status"], **auto_assess(rec, t),
               "seconds": (rec.get("stats") or {}).get("wall_seconds"), "card": path.relative_to(ROOT).as_posix()}
        summary.append(row)
        print(f"{t['id']}: {row['status']:24s} retrieved-expected={row['Expected source retrieved'][:3]:3s} "
              f"key-terms={row['Answer contains expected key terms']:3s} {row['seconds']} s  -> {row['card']}")
    rt = runtime_info(cfg)
    out = p(cfg, "evidence_dir") / a.out / "ask-tests-summary.json"
    out.write_text(json.dumps({"internet_reachable": online, "runtime_after_tests": rt, "tests": summary}, indent=2), encoding="utf-8")
    print(f"Internet reachable: {online}. Loaded model memory: {rt.get('loaded_memory_gb')} GB. Summary: {out.relative_to(ROOT)}")


def cmd_modecheck(cfg, a):
    from harness.evidence import log_record, passages_md
    from harness.modes import ChatSession, ask
    from harness.retrieval import load_index
    from harness.system import internet_reachable

    checks = json.loads((ROOT / "tests" / "questions.json").read_text(encoding="utf-8"))["mode_checks"]
    client, index = get_client(cfg), load_index(cfg)
    session = ChatSession(cfg, client, index)
    online = internet_reachable()
    md = [f"# Mode-boundary checks — {dt.datetime.now():%Y-%m-%d %H:%M}", "",
          f"Model `{client.model}` · execution {'local' if client.backend == 'ollama' else client.backend} · "
          f"internet reachable: **{online}**", "",
          "C1–C5 run in one chat session, in order. C6 is search. C7 is ask, run after the chat claim in C5.", ""]
    for c in checks:
        md += [f"## {c['id']} · {c['mode']} · `{c['input']}`", "", f"*Expected:* {c['expect']}", ""]
        if c["mode"] == "chat":
            rec = session.turn(c["input"])
            md += [f"*Notes lookup:* {'used' if rec['retrieval']['used'] else 'not used'} — {rec['retrieval']['reason']}  ",
                   f"*Earlier messages sent as context:* {rec['history_turns_sent']}  ",
                   f"*Citation check:* {rec['check']['status']} · *time:* {rec['stats'].get('wall_seconds')} s", "",
                   "**Margin:**", "", "> " + rec["reply"].replace("\n", "\n> "), ""]
            if rec["retrieval"]["used"]:
                md += ["<details><summary>Passages given to chat</summary>", "",
                       passages_md([dict(h, label=f"N{i}") for i, h in enumerate(rec["retrieval"]["passages"], 1)]), "</details>", ""]
        elif c["mode"] == "search":
            res = index.search(c["input"], k=cfg["search_top_k"])
            rec = {"mode": "search", "execution": "local", "model_called": False, "query": c["input"], "results": res}
            md += ["*Model called:* no", "", passages_md(res), ""]
        else:
            rec = ask(cfg, client, index, c["input"])
            md += [f"*Chat history sent to ask:* none (ask builds its prompt from research rules + passages only)  ",
                   f"*Citation check:* {rec['check']['status']}", "", "**Answer:**", "", "> " + rec["answer"].replace("\n", "\n> "), "",
                   "Citations: " + (", ".join(f"[{x['label']}] {x['path']} lines {x['lines']}" for x in rec["citations"]) or "none"), ""]
        log_record(cfg, rec)
        print(f"{c['id']} {c['mode']}: done")
        md += ["**Result:** _to be assessed_", ""]
    out = p(cfg, "evidence_dir") / a.out / "mode-checks.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"Saved: {out.relative_to(ROOT)}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wiki", add_help=False)
    ap.add_argument("-h", "--help", action="store_true")
    ap.add_argument("--mode", default="local", choices=["local"])
    ap.add_argument("--model")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("ingest"); s.add_argument("path", nargs="?", default="vault/raw")
    s.add_argument("--note"); s.add_argument("--source"); s.add_argument("--force", action="store_true"); s.add_argument("--dry-run", action="store_true")
    sub.add_parser("index")
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("-k", type=int)
    s = sub.add_parser("ask"); s.add_argument("question"); s.add_argument("--save", action="store_true")
    sub.add_parser("chat")
    s = sub.add_parser("check"); s.add_argument("--out")
    s = sub.add_parser("doctor"); s.add_argument("--out")
    s = sub.add_parser("eval"); s.add_argument("--out", required=True)
    s = sub.add_parser("modecheck"); s.add_argument("--out", required=True)
    for sp in sub.choices.values():  # allow --mode/--model after the subcommand too
        sp.add_argument("--mode", default="local", choices=["local"], dest="mode_sub")
        sp.add_argument("--model", dest="model_sub")
    a = ap.parse_args(argv)
    if a.help or not a.cmd:
        print(HELP)
        return 0
    cfg = load_config()
    model = getattr(a, "model_sub", None) or a.model
    if model:
        cfg["model"] = model
    handler = globals()[f"cmd_{a.cmd}"]
    try:
        handler(cfg, a)
    except ModelUnavailable as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
