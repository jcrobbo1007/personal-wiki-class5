"""The three interaction modes. Each one loads its own instructions and context.

search : retrieval tool only. No model call, no history.
ask    : RAG. Standalone question -> retrieve -> research rules + passages -> Gemma -> citation check.
         Never sees chat history or the chat persona.
chat   : personal assistant. Persona + recent conversation. Retrieves notes only when the
         router decides the turn needs them (or on /notes).
"""
import re

from .config import ROOT
from .retrieval import format_passage

INSUFFICIENT = "INSUFFICIENT EVIDENCE"
# One bracket may hold several labels: [S1] or [S4, S5].
CITE = re.compile(r"\[([SN]\d+(?:\s*,\s*[SN]\d+)*)\]")
NUM = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")


def _read_prompt(name):
    return (ROOT / "prompts" / name).read_text(encoding="utf-8")


# ------------------------------------------------------------------ search

def search(index, query, k):
    return index.search(query, k=k)


# ------------------------------------------------------------------ ask

def ask(cfg, client, index, question):
    passages = index.search(question, k=cfg["ask_top_k"])
    passages = [r for r in passages if r["score"] >= cfg["min_retrieval_score"]]
    record = {
        "mode": "ask",
        "execution": "local" if client.backend == "ollama" else client.backend,
        "model": client.model,
        "question": question,
        "retrieved": [dict(r, label=f"S{i}") for i, r in enumerate(passages, 1)],
    }
    if not passages:
        # Nothing cleared the retrieval threshold: answer without calling the model at all.
        record.update(
            answer=f"{INSUFFICIENT}: no passage in the wiki sources matched this question.",
            model_called=False,
            citations=[],
            check={"status": "insufficient-evidence", "notes": ["no passages above retrieval threshold"]},
        )
        return record

    blocks = []
    for i, r in enumerate(passages, 1):
        blocks.append(f"[S{i}] {format_passage(r)}\n{r['text']}")
    user = "Source passages:\n\n" + "\n\n".join(blocks) + f"\n\nQuestion: {question}\nAnswer:"
    messages = [{"role": "system", "content": _read_prompt("wiki-instructions.md")}, {"role": "user", "content": user}]
    answer, stats = client.chat(messages, temperature=cfg["ask_temperature"])
    record.update(answer=answer, model_called=True, stats=stats, prompt_chars=len(user))
    record["citations"], record["check"] = check_citations(answer, passages, prefix="S")
    return record


def check_citations(answer, passages, prefix="S"):
    """Verify labels exist and numbers in the answer appear in the cited passages."""
    labels = {f"{prefix}{i}": r for i, r in enumerate(passages, 1)}
    found = [c.strip() for group in CITE.findall(answer) for c in group.split(",")]
    used = [c for c in dict.fromkeys(found) if c.startswith(prefix)]
    notes, valid = [], []
    for c in used:
        if c in labels:
            r = labels[c]
            valid.append({"label": c, "path": r["path"], "section": r["section"], "lines": f"{r['line_start']}-{r['line_end']}"})
        else:
            notes.append(f"cites {c}, which was not supplied")
    insufficient = INSUFFICIENT in answer.upper()
    cited_text = " ".join(labels[c["label"]]["text"] for c in valid).replace(",", "")
    for n in dict.fromkeys(NUM.findall(CITE.sub("", answer))):
        bare = n.replace(",", "")
        if len(bare) > 1 and bare not in cited_text:
            notes.append(f"number {n} not found in the cited passages")
    if insufficient and not valid:
        status = "insufficient-evidence"
    elif not valid:
        status = "uncited"
        notes.append("answer has no valid citation; treat as unsupported")
    elif notes:
        status = "cited-with-warnings"
    else:
        status = "cited"
    if insufficient and valid:
        status += "+partial"
    return valid, {"status": status, "notes": notes}


# ------------------------------------------------------------------ chat

CONVERSATIONAL = re.compile(
    r"^\s*(hi|hey|hello|thanks|thank you|ok|okay|cool|great|bye)\b"
    r"|what can (you|we) (do|help)|what can you help|who are you|how do you work|help me with"
    r"|\b(make|keep) (it|that|this) (shorter|longer|simpler|punchier)|\bshorter\b|\brewrite\b|\brephrase\b"
    r"|\b(that|this|it) (again|instead)\b|turn (that|this|it) into|bullet",
    re.I,
)
NOTES_HINT = re.compile(
    r"\b(my|our|i|did|we)\b.*\b(project|run|model|notes?|score|result|class|assignment|pac-?man|mnist|llm|nanogpt|dqn|eval)",
    re.I,
)


class ChatSession:
    """Holds conversation context for chat mode only. Ask mode never reads it."""

    def __init__(self, cfg, client, index):
        self.cfg, self.client, self.index = cfg, client, index
        self.history = []  # [{role, content}] — conversation, not evidence
        self.persona = _read_prompt("persona.md")

    def route(self, message, force=False):
        """Decide whether this turn needs the notes. Returns (use_notes, reason, passages)."""
        if force:
            hits = self.index.search(message, k=self.cfg["chat_top_k"])
            return bool(hits), "forced by /notes", hits
        if CONVERSATIONAL.search(message):
            return False, "conversational or follow-up turn", []
        hits = self.index.search(message, k=self.cfg["chat_top_k"])
        top = hits[0]["score"] if hits else 0.0
        if top >= self.cfg["chat_retrieval_score"] or (NOTES_HINT.search(message) and top >= self.cfg["min_retrieval_score"]):
            return True, f"asks about his own work (top score {top})", [h for h in hits if h["score"] >= self.cfg["min_retrieval_score"]]
        return False, f"no strong match in notes (top score {top})", []

    def turn(self, message, force_notes=False):
        use, reason, hits = self.route(message, force_notes)
        system = self.persona
        user_content = message
        if use and hits:
            blocks = [f"[N{i}] {format_passage(h)}\n{h['text']}" for i, h in enumerate(hits, 1)]
            user_content = (
                "Notes retrieved for this message (cite as [N1], [N2] only if you use them):\n\n"
                + "\n\n".join(blocks)
                + f"\n\nMy message: {message}"
            )
        keep = self.cfg["chat_history_turns"] * 2
        messages = [{"role": "system", "content": system}] + self.history[-keep:] + [{"role": "user", "content": user_content}]
        reply, stats = self.client.chat(messages, temperature=self.cfg["chat_temperature"])
        # History stores the plain message, not the injected passages, to keep context small.
        self.history += [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
        if use and hits:
            cites, check = check_citations(reply, hits, prefix="N")
            if check["status"] == "uncited":  # fine in chat if the reply only makes suggestions
                check = {"status": "notes-supplied-none-cited", "notes": ["no [N#] citations; acceptable only if the reply states no facts from the notes"]}
        else:
            cites, check = [], {"status": "no-notes-used", "notes": []}
        return {
            "mode": "chat",
            "execution": "local" if self.client.backend == "ollama" else self.client.backend,
            "model": self.client.model,
            "message": message,
            "retrieval": {"used": bool(use and hits), "reason": reason, "passages": hits},
            "reply": reply,
            "citations": cites,
            "check": check,
            "history_turns_sent": len(messages) - 2,  # earlier chat messages included
            "stats": stats,
        }

    def reset(self):
        self.history = []
