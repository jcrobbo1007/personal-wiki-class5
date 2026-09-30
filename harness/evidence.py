"""Saving results: JSONL log of every run plus readable Markdown evidence cards."""
import datetime as dt
import json
import re

from .config import p


def _dir(cfg, *parts):
    d = p(cfg, "evidence_dir").joinpath(*parts)
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_record(cfg, record):
    """Append every search/ask/chat result to evidence/logs/<date>.jsonl."""
    record = dict(record, saved_at=dt.datetime.now().isoformat(timespec="seconds"))
    path = _dir(cfg, "logs") / f"{dt.date.today().isoformat()}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def _quote(text, limit=900):
    text = text.strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + " …"
    return "\n".join("> " + l if l.strip() else ">" for l in text.splitlines())


def passages_md(passages, label_key="label"):
    out = []
    for i, r in enumerate(passages, 1):
        label = r.get(label_key) or f"#{i}"
        out.append(
            f"**[{label}]** `{r['path']}` — {r['section']} — lines {r['line_start']}-{r['line_end']} — score {r['score']}\n\n{_quote(r['text'])}\n"
        )
    return "\n".join(out) or "_No passages cleared the retrieval threshold._"


def ask_card(record, test=None, run_info=None):
    run_info = run_info or {}
    lines = [f"# Ask-mode evidence — {test['id'] + ': ' if test else ''}{record['question']}", ""]
    lines += [
        "| | |",
        "|---|---|",
        f"| Mode | ask (standalone, no chat history) |",
        f"| Execution | {record['execution']} |",
        f"| Model | `{record['model']}` |",
        f"| Internet reachable during run | {run_info.get('internet_reachable', 'not recorded')} |",
        f"| Run at | {run_info.get('run_at', record.get('saved_at', ''))} |",
        f"| Model called | {record.get('model_called')} |",
    ]
    st = record.get("stats") or {}
    if st:
        lines.append(f"| Response time | {st.get('wall_seconds')} s wall ({st.get('prompt_tokens')} prompt tokens, {st.get('output_tokens')} output tokens) |")
    lines.append("")
    if test:
        lines += [
            "## Expectation (written before the run)",
            "",
            f"- Kind: {test['kind']}",
            f"- Expected source: `{test['expected_source']}`",
            f"- Expected passage: {test['expected_passage']}",
            "",
        ]
    lines += ["## Retrieved passages", "", passages_md(record["retrieved"]), ""]
    lines += ["## Gemma's answer (verbatim)", "", _quote(record["answer"], 4000), ""]
    lines += ["## Citations", ""]
    if record["citations"]:
        for c in record["citations"]:
            lines.append(f"- [{c['label']}] `{c['path']}` — {c['section']} — lines {c['lines']}")
    else:
        lines.append("- none")
    chk = record["check"]
    lines += ["", "## Automatic checks", "", f"- Citation check: **{chk['status']}**"]
    for n in chk["notes"]:
        lines.append(f"- {n}")
    if test:
        auto = auto_assess(record, test)
        for k, v in auto.items():
            lines.append(f"- {k}: **{v}**")
    lines += ["", "## Assessment", "", "_To be written after reading the cited passages against the answer._", ""]
    return "\n".join(lines)


def auto_assess(record, test):
    exp_src = test["expected_source"]
    got = {r["path"] for r in record["retrieved"]}
    if exp_src == "none":
        retrieval = "n/a (no source should contain the answer)"
    else:
        wanted = [s.strip() for s in exp_src.split("+")]
        retrieval = "yes" if all(w in got for w in wanted) else f"no (retrieved: {sorted(got)})"
    ans = record["answer"]
    contains = all(s.lower() in ans.lower() for s in test["expected_answer_contains"])
    return {"Expected source retrieved": retrieval, "Answer contains expected key terms": "yes" if contains else "no"}


def save_ask_card(cfg, record, test, run_info, folder):
    slug = test["id"] if test else re.sub(r"[^a-z0-9]+", "-", record["question"].lower())[:40]
    path = _dir(cfg, folder) / f"{slug}.md"
    path.write_text(ask_card(record, test, run_info), encoding="utf-8")
    (_dir(cfg, folder) / f"{slug}.json").write_text(json.dumps(dict(record, run_info=run_info), indent=2, ensure_ascii=False), encoding="utf-8")
    return path
