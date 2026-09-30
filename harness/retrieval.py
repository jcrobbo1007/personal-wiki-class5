"""Retrieval tool: chunk the original sources and search them with BM25.

This is the only code that finds evidence. It needs no model and no network:
`wiki search` stops here, `wiki ask` passes its results to Gemma.

Evidence comes from vault/raw/ (the unchanged originals), so every citation
points at original text rather than at a generated wiki summary.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

from .config import ROOT, p

STOPWORDS = set(
    """a an and are as at be been but by can could did do does for from had has have how i if in
    into is it its itself me my of on or our so than that the their them then there these they this
    to was we were what when where which who why will with would you your about after before also
    any all each more most not no only other over same some such very just use used using up out""".split()
)


def tokenize(text):
    words = re.findall(r"[a-z0-9]+(?:[.,][0-9]+)*", text.lower())
    out = []
    for w in words:
        w = w.replace(",", "")
        if w in STOPWORDS or len(w) < 2 and not w.isdigit():
            continue
        out.append(stem(w))
    return out


def stem(w):
    """Very light suffix stripping so 'shifted'/'shifting'/'shifts' meet 'shift'."""
    if w[0].isdigit():
        return w
    for suf in ("ations", "ation", "ings", "ing", "edly", "ed", "ies", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            base = w[: -len(suf)]
            w = base + "y" if suf == "ies" else base
            break
    if len(w) >= 4 and w.endswith("e"):  # 'move' and 'moved' -> 'mov'
        w = w[:-1]
    return w


# ---------------------------------------------------------------- chunking

def split_sections(text):
    """Yield (heading_path, start_line, end_line, body) per markdown section.

    Headings inside ``` code fences are ignored.
    """
    lines = text.splitlines()
    stack = []  # [(level, title)]
    sections = []
    cur_start, cur_lines, in_fence = 1, [], False

    def flush(end_line):
        body = "\n".join(cur_lines)  # not stripped: line numbers must stay exact
        if body.strip():
            path = " > ".join(t for _, t in stack) or "(top)"
            sections.append((path, cur_start, end_line, body))

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush(i - 1)
            level, title = len(m.group(1)), m.group(2).strip()
            stack = [(l, t) for l, t in stack if l < level] + [(level, title)]
            cur_start, cur_lines = i, [line]
        else:
            cur_lines.append(line)
    flush(len(lines))
    return sections


def chunk_source(source_id, rel_path, text, words_per_chunk, overlap):
    """Split each section into overlapping word windows, keeping line numbers."""
    chunks = []
    for path, start, end, body in split_sections(text):
        # Keep line positions: walk the section line by line into windows.
        body_lines = body.splitlines()
        line_words = [(start + k, ln.split()) for k, ln in enumerate(body_lines)]
        total = sum(len(w) for _, w in line_words)
        if total == 0:
            continue
        step = max(1, words_per_chunk - overlap)
        flat = [(ln_no, w) for ln_no, ws in line_words for w in ws]
        n = 0
        for s in range(0, len(flat), step):
            window = flat[s : s + words_per_chunk]
            if not window:
                break
            first, last = window[0][0], window[-1][0]
            text_out = "\n".join(
                body_lines[k - start] for k in range(first, last + 1) if 0 <= k - start < len(body_lines)
            )
            n += 1
            chunks.append(
                {
                    "id": f"{source_id}:{first}-{last}",
                    "source_id": source_id,
                    "path": rel_path,
                    "section": path,
                    "line_start": first,
                    "line_end": last,
                    "text": text_out,
                }
            )
            if s + words_per_chunk >= len(flat):
                break
    return chunks


# ---------------------------------------------------------------- BM25 index

class Index:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs = [tokenize(c["section"] + " " + c["text"]) for c in chunks]
        self.df = Counter()
        for d in self.docs:
            self.df.update(set(d))
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / max(1, self.N)
        self.tf = [Counter(d) for d in self.docs]

    def idf(self, term):
        n = self.df.get(term, 0)
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    def search(self, query, k=5, k1=1.4, b=0.75, max_per_source=3):
        """BM25 over passages. At most `max_per_source` passages come from one file, so a
        question that spans two projects is not crowded out by the longer source."""
        q = tokenize(query)
        scored = []
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = 0.0
            for t in set(q):
                f = tf.get(t)
                if f:
                    s += self.idf(t) * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / self.avgdl))
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        results, seen_lines, per_source = [], set(), {}
        for s, i in scored:
            c = self.chunks[i]
            key = (c["path"], c["line_start"])
            if key in seen_lines:  # overlapping windows starting on the same line
                continue
            if per_source.get(c["path"], 0) >= max_per_source:
                continue
            seen_lines.add(key)
            per_source[c["path"]] = per_source.get(c["path"], 0) + 1
            results.append(dict(c, score=round(s, 2)))
            if len(results) >= k:
                break
        return results


def load_index(cfg):
    path = p(cfg, "chunks_file")
    if not path.exists():
        raise SystemExit(
            f"No retrieval index at {path.relative_to(ROOT)}. Run: wiki ingest ./vault/raw  (or: wiki index)"
        )
    return Index(json.loads(path.read_text(encoding="utf-8")))


def build_index(cfg, catalog):
    """(Re)build chunks for every catalogued source. Fully replaces the old index."""
    chunks = []
    for src in catalog:
        text = (ROOT / src["path"]).read_text(encoding="utf-8")
        chunks += chunk_source(src["id"], src["path"], text, cfg["chunk_words"], cfg["chunk_overlap_words"])
    out = p(cfg, "chunks_file")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(chunks, indent=1, ensure_ascii=False), encoding="utf-8")
    return chunks


def format_passage(r, label=None):
    head = f"[{label}] " if label else ""
    return f"{head}{r['path']} — {r['section']} (lines {r['line_start']}-{r['line_end']})"
