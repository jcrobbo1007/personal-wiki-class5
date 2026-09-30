<!--
FILL-IN RULES (delete this comment before submitting):
Every {{placeholder}} is replaced with a value from a file under evidence/ or data/, or the
line is deleted. Never invent a number, an answer or a screenshot. Failed or weak results
stay in and get explained. See CLAUDE.md.
-->

# Personal Wiki CLI — local Gemma + RAG (Class 5, Assignment 4)

A terminal assistant over my own notes from *From Zero to AI Agents*. My three earlier project
write-ups are the sources. A local Gemma model turns them into a linked Obsidian wiki. My own
Python harness gives three modes on top: **chat** with a study-partner persona, **ask** for
cited factual answers, and **search** for the original passages. Everything runs on my laptop
with the internet off.

**Result in one line:** {{e.g. "3 of 3 answerable questions answered with correct citations,
and the unsupported question refused with INSUFFICIENT EVIDENCE, all offline on gemma4:e2b" —
taken from evidence/offline/ask-tests-summary.json and the assessed cards}}

| Jump to | |
|---|---|
| CLI and harness code | [`wiki.py`](wiki.py), [`harness/`](harness) |
| Wiki (open `vault/` in Obsidian) | [`vault/index.md`](vault/index.md), [`vault/wiki/`](vault/wiki), [`vault/raw/`](vault/raw) |
| Four ask-mode evidence cards | [T1](evidence/offline/T1.md) · [T2](evidence/offline/T2.md) · [T3](evidence/offline/T3.md) · [T4](evidence/offline/T4.md) |
| Chat / search mode checks | [`evidence/offline/mode-checks.md`](evidence/offline/mode-checks.md) |
| Offline run transcript | [`evidence/offline/terminal-transcript.txt`](evidence/offline/terminal-transcript.txt) |
| Screenshots | [`evidence/screenshots/`](evidence/screenshots) |

---

## 1. Purpose and sources

The wiki exists to answer questions about my own coursework: what I trained, which settings I
chose and why, what the results were, and which ideas carried across projects. It is scoped to
three sources I wrote myself, so every answer can be checked by hand.

| Source id | Original (unchanged, in `vault/raw/`) | What it is |
|---|---|---|
| `pacman-dqn` | [`Pac-Man DQN Project.md`](vault/raw/Pac-Man%20DQN%20Project.md) | README of my Class 3 Ms. Pac-Man DQN repo ([pacman-dqn-class3](https://github.com/jcrobbo1007/pacman-dqn-class3)) |
| `custom-llm` | [`Custom LLM Project.md`](vault/raw/Custom%20LLM%20Project.md) | README of my Class 4 nanoGPT repo ([custom-llm-class4](https://github.com/jcrobbo1007/custom-llm-class4)) |
| `mnist` | [`MNIST From Scratch Log.md`](vault/raw/MNIST%20From%20Scratch%20Log.md) | My Class 3 MNIST-from-scratch run log |

The originals are byte-for-byte copies. [`data/source_catalog.json`](data/source_catalog.json)
records each one's id, path and SHA-256, so any change to them would be visible. The originals
still contain image links that pointed into their own repos; those images are not copied here,
so Obsidian shows them as missing. The text is untouched on purpose.

**How originals become wiki pages.** [`data/wiki_plan.json`](data/wiki_plan.json) maps sources
to ten readable notes in two folders, `Projects/` and `Concepts/`. For each note, ingestion
pulls the listed sections out of the originals and sends them with
[`prompts/ingest-instructions.md`](prompts/ingest-instructions.md) to local Gemma. Gemma writes
the Summary and Key details. The harness adds the title, front matter, related-note links and
the Sources list. Because the harness writes the links and filenames, not the model, they always
point at real notes.

## 2. Setup and device

**Device** (from [`evidence/offline/doctor.json`](evidence/offline/doctor.json)):

| | |
|---|---|
| OS | {{device.os}} |
| CPU | {{device.cpu}}, {{device.cpu_threads}} threads |
| RAM | {{device.ram_total_gb}} GB total, {{device.ram_available_gb}} GB available at run time |
| GPU / VRAM | {{device.gpus, or "none used: CPU inference"}} |
| Free disk | {{device.disk_free_gb}} GB |
| Python | {{device.python}} (standard library only, no pip packages) |

**Model and runtime:**

| | |
|---|---|
| Model | `gemma4:e2b` (Gemma 4 E2B), digest `{{runtime.digest}}` |
| Quantization | {{runtime.details.quantization_level}} ({{runtime.file_size_gb}} GB file) |
| Runtime | Ollama {{runtime.ollama_version}}, local HTTP API at `127.0.0.1:11434` |
| Official download | `ollama pull gemma4:e2b` ([ollama.com/library/gemma4:e2b](https://ollama.com/library/gemma4:e2b)). Weights are not committed. |
| Context | `num_ctx` 8192; temperature 0.0 for ask, 0.6 for chat, 0.2 for ingest |

**Why E2B.** {{Two or three sentences grounded in the measurements below: this laptop runs on
CPU (or name the GPU); E2B loaded at X GB, leaving Y GB of RAM free; an ask answer took Z s.
E4B would roughly double load memory and slow answers, and the tests below did / did not show
a quality problem that would justify it.}}

**Measured** (from `evidence/offline/after/doctor.json`, `ask-tests-summary.json` and the ingest log):

| Measurement | Value |
|---|---|
| Model memory once loaded (Ollama `/api/ps`) | {{runtime.loaded_memory_gb}} GB |
| Ollama process memory (working set) | {{runtime.ollama_process_memory_gb}} GB |
| Full ingest of 3 sources to 10 notes | {{wall_seconds}} s |
| Ask answer, per question (T1–T4) | {{seconds per test}} |
| Chat reply | {{typical seconds from mode-checks.md}} |

**Commands** (Windows PowerShell, from the repo root; on Mac/Linux use `python3 wiki.py` instead of `.\wiki`):

```powershell
# once, online: install Ollama, pull the model, run the harness self-test
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1

.\wiki --help
.\wiki ingest ./vault/raw                  # build catalog, index and wiki notes with local Gemma
.\wiki search "exploration rate"           # original passages only, no model call
.\wiki ask "What learning rate did I use for the MNIST model?" --mode local
.\wiki chat                                # Margin, the study partner; /exit to leave
.\wiki check                               # review aid for the generated notes

# the graded offline run (Wi-Fi off first)
powershell -ExecutionPolicy Bypass -File scripts\run_offline_evidence.ps1
```

Useful errors: if Ollama is not running, or the model has not been pulled, every model command
stops with a message naming the fix (`ollama serve` / `ollama pull gemma4:e2b`). There is no
cloud fallback. `search` still works with the model off.

## 3. Architecture

| Piece | What it is here | Code |
|---|---|---|
| **Model** | Gemma 4 E2B running in Ollama. It only sees the text the harness sends. It does not read files, remember sessions or call tools. | [`harness/llm.py`](harness/llm.py) |
| **Retrieval tool** | Splits the originals into passages by Markdown section (≈160-word windows, 40-word overlap, source path and line numbers kept) and ranks them with BM25 keyword scoring. No model, no network. | [`harness/retrieval.py`](harness/retrieval.py) |
| **RAG workflow** | Ask mode: retrieve → put the numbered passages and research rules into the prompt → Gemma answers → citations checked. | [`harness/modes.py`](harness/modes.py) `ask()` |
| **Harness** | Picks the mode, loads that mode's instructions, keeps chat history for chat only, decides when chat needs notes, builds prompts, calls Gemma, checks citations, handles errors and saves every result. | [`harness/`](harness) |
| **CLI** | The `wiki` command: `ingest`, `index`, `search`, `ask`, `chat`, `check`, `doctor`, `eval`, `modecheck`, `--help`. | [`wiki.py`](wiki.py) |

**One question traced through the code** (`.\wiki ask "What learning rate did I use for the MNIST model?"`):

1. `wiki.py` `main()` parses the command and calls `cmd_ask()`. Ask gets a fresh process with no chat state.
2. `retrieval.load_index()` loads the passages from `.index/chunks.json`. That file is rebuilt from `vault/raw/` at every ingest and kept outside the vault.
3. `modes.ask()` calls `Index.search()`. BM25 ranks passages, keeps the top 5 (at most 3 from any one file) and drops any below a score of 3.0. If nothing clears the bar, the harness answers `INSUFFICIENT EVIDENCE` itself, without calling the model.
4. The prompt is built from `prompts/wiki-instructions.md` (system) plus the passages labelled `[S1]…[S5]` with their paths, sections and line numbers, and then the question. No persona and no chat history go in.
5. `llm.OllamaClient.chat()` POSTs to `http://127.0.0.1:11434/api/chat` with temperature 0 and gets the answer plus token counts and timings.
6. `modes.check_citations()` confirms every `[S#]` exists and flags any number in the answer that is not in the cited passages. The result is `cited`, `cited-with-warnings`, `uncited` or `insufficient-evidence`.
7. `wiki.py` prints the answer, the citations with file and line numbers, and the check. `evidence.log_record()` appends the whole record to `evidence/logs/<date>.jsonl`.

**How the three modes differ:**

| | chat | ask | search |
|---|---|---|---|
| Instructions | [`prompts/persona.md`](prompts/persona.md): Margin, a warm, dry study partner who knows what it can and can't do | [`prompts/wiki-instructions.md`](prompts/wiki-instructions.md): neutral research rules | none |
| Conversation history | last 6 exchanges | never | never |
| Retrieval | only when the router says the turn needs notes, or on `/notes` | always | always |
| Model call | yes | yes (unless nothing is retrieved) | **no** |
| Citations | `[N#]` for facts taken from notes; ideas are labelled "Suggestion" | `[S#]` required on every factual sentence | shows paths and line numbers |

**When chat retrieves** (`ChatSession.route()`): conversational turns ("what can you help me
with?", "make that shorter", greetings, rewrite requests) never trigger a lookup. Other turns
run a search. Notes are used if the best passage scores ≥ 6.0, or if the message talks about
my own work (my project, run, score, model…) and the best score is at least 3.0. Chat history
stores my plain messages, not the injected passages, so notes from one turn don't pile up as
fake context in later turns. A claim I make in chat stays in chat history, and ask never sees
that history.

## 4. Design choices

- **Passage size.** Chunks follow Markdown sections, so a passage stays inside one topic, and
  run about 160 words with 40 words of overlap, so a table row and its explanation usually land
  together. Ask sends at most 5 passages (roughly {{prompt_chars from a card}} characters). That
  fits easily in the 8k context and leaves room for the answer.
- **Retrieval method.** Keyword BM25 with light stemming, so "moved" meets "Move". It needs no
  embedding model, so there is nothing extra to download and nothing that could quietly call a
  hosted API. The cost is weaker handling of paraphrase (see T2 and the reflection below).
  At most 3 passages come from any one file, so a question spanning two projects (T3) is not
  crowded out by the longer README.
- **Research rules vs. personality.** They live in separate files and are loaded by different
  code paths. Ask never gets the persona and chat never gets the research rules, so personality
  cannot leak into factual answers.
- **Insufficient evidence.** It is handled at two levels. The harness refuses before calling
  the model when nothing is retrieved, and the prompt tells Gemma to reply `INSUFFICIENT
  EVIDENCE:` when the passages don't answer the question.
- **Citation checks.** A citation isn't proof by itself, so the harness checks that labels exist
  and that numbers in the answer appear in the cited text. I still read every cited passage
  against the answer (the Assessment in each card).
- **Note names and folders.** Short subject names (`Ms Pac-Man DQN`, `Learning Rate
  Choices`…) with the first heading matching the filename. There are two topic folders,
  `Projects/` and `Concepts/`, and a grouped `index.md`. Machine ids (`note_id`, `source_ids`,
  model, date) live in front matter. Source hashes live in `data/source_catalog.json`.
  Retrieval chunks, logs and evidence stay outside `vault/`.
- **Re-ingestion without duplicates.** Filenames come from the plan, so re-ingesting overwrites
  the same file. `.\wiki ingest ./vault/raw --source mnist` regenerates only the notes built from
  that source. A note I have marked `reviewed: true` is never overwritten silently: the new draft
  goes to `.index/drafts/` instead, unless I pass `--force`. `wiki check` flags any note that is
  not in the plan.
- **Model settings.** Temperature 0 for ask gives repeatable, least-random answers. Gemma's
  thinking mode is switched off (`think: false`) so replies are direct and faster on CPU.
  {{Note any setting changed after a failure, and the rerun, here.}}

## 5. The wiki in Obsidian

Open the `vault/` folder itself as the Obsidian vault. The graph is filtered with
`path:wiki/` and attachments are hidden (saved in `vault/.obsidian/graph.json`). Projects and
Concepts are colour-grouped.

1. **An open note with sources and related links:**
   ![Open note](evidence/screenshots/obsidian-note.png)
2. **The index, grouped by topic:**
   ![Index](evidence/screenshots/obsidian-index.png)
3. **Graph view** (filter `path:wiki/`, attachments off):
   ![Graph](evidence/screenshots/obsidian-graph.png)

**Traced path:** `index.md` → [[{{a project note}}]] → its link to [[{{a concept note}}]] →
Sources → `{{raw file}}`, section "{{section}}", which contains "{{short quote}}".

**Review of generated notes.** {{What `wiki check` flagged (evidence/offline/wiki-check.json)
and what was corrected by reading the originals, e.g. "Gemma wrote 0.001 as 0.01 in Learning
Rate Choices; corrected against Custom LLM Project.md line 26". Originals were never edited.
Reviewed notes are marked `reviewed: true`.}}

**Duplicate check:** re-ingesting `mnist` offline left {{N}} notes before and {{N}} after, with
no new files (see the transcript, step "Duplicate check").

## 6. Evidence: four ask-mode tests (offline)

The questions and expected passages were written before the run, in
[`tests/questions.json`](tests/questions.json). That file sits outside the vault, so retrieval
can't find the answer key. Every card records the retrieved passages with paths and scores, the
exact model, the local execution setting, internet status, Gemma's verbatim answer, the checked
citations, and my assessment.

| Test | Question | Retrieved expected source? | Answer | Citations support it? | Card |
|---|---|---|---|---|---|
| T1 direct | Mean trained Pac-Man score vs. baseline | {{}} | {{}} | {{}} | [T1](evidence/offline/T1.md) |
| T2 paraphrased | Why the digit classifier failed when digits moved | {{}} | {{}} | {{}} | [T2](evidence/offline/T2.md) |
| T3 two sources | Learning rates for Pac-Man and the LLM | {{}} | {{}} | {{}} | [T3](evidence/offline/T3.md) |
| T4 unsupported | Cloud GPU cost for the LLM | n/a | {{}} | {{}} | [T4](evidence/offline/T4.md) |

{{One short paragraph per failure or weak answer: what went wrong (retrieval or model), and
whether anything was changed and rerun. Keep the earlier result.}}

## 7. Evidence: chat and search mode checks (offline)

Full transcript: [`evidence/offline/mode-checks.md`](evidence/offline/mode-checks.md). C1–C5
are one chat session in order.

| Check | Expected | Observed |
|---|---|---|
| C1 chat "what can we do?" | Capabilities, no lookup, no refusal | {{}} |
| C2 chat "what can you help me with?" | Same | {{}} |
| C3 chat: draft a 3-step plan | Suggestions labelled; note facts cited | {{}} |
| C4 chat "make that shorter" | Uses C3 from the conversation | {{}} |
| C5 chat: claim "5,000 points" | Stays in chat only | {{}} |
| C6 search "exploration rate" | Passages + paths, no model call | {{}} |
| C7 ask "Did my agent score 5,000…?" | Uses sources (best game 1,130), not the chat claim | {{}} |

## 8. Offline demonstration

[`scripts/run_offline_evidence.ps1`](scripts/run_offline_evidence.ps1) refuses to start if
`1.1.1.1:443` is reachable. It then restarts Ollama, runs every step as a fresh CLI process, and
tees all output into
[`evidence/offline/terminal-transcript.txt`](evidence/offline/terminal-transcript.txt). Every
evidence record also carries its own `internet_reachable: false` check.

![Offline terminal](evidence/screenshots/offline-terminal.png)

{{Optional: live chat screenshot, evidence/screenshots/offline-chat.png}}

## 9. Reflection: one limitation and one improvement

{{One real failure or limitation seen in the evidence, with the cause if known. A likely
candidate: keyword retrieval on the paraphrased T2 question ranked the MNIST "Three mistakes"
section above "Shift experiment", because the question's words ("digits", "pixels") appear
more often there. Say whether Gemma still answered correctly from the lower-ranked passage.}}

**Improvement I'd try:** {{e.g. hybrid retrieval that adds a small local embedding model
(such as `embeddinggemma` through Ollama) to BM25 and merges the rankings, then reruns T1–T4 to
check that T2 ranks the shift passage first without losing T4's refusal.}}

## Repository layout

```
wiki.py, wiki.cmd          CLI entry point (+ Windows launcher)
harness/                   config, llm (Ollama client), retrieval (BM25), modes (chat/ask),
                           ingest, check, evidence, system (device specs, offline check)
prompts/                   persona.md (chat), wiki-instructions.md (ask), ingest-instructions.md
config.json                model, runtime URL, context, retrieval settings
data/                      wiki_plan.json (source → note map), source_catalog.json (hashes)
vault/                     THE OBSIDIAN VAULT: raw/ originals, wiki/ notes, index.md
tests/                     questions.json (fixed test set), test_harness.py (plumbing tests)
scripts/                   setup_windows.ps1, run_offline_evidence.ps1
evidence/                  offline/ cards, mode checks, transcript, doctor; screenshots/; logs/
```

No optional online mode is included; local is the only execution setting.
