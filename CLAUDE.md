# CLAUDE.md — Class 5, Assignment 4: Personal Wiki CLI (local Gemma + RAG)

Persistent rules for this repo. Read before acting; re-read before writing the README.

## Mission

Submit one public GitHub repo (github.com/jcrobbo1007/personal-wiki-class5) showing a personal
wiki CLI that runs **local Gemma** through **Jack's own harness**, with chat / ask / search /
ingest / help, working **offline**. The README is the grading entry point (10 points: deliverable
quality 4, testing and evaluation 3, working result 3). The full brief is in HANDOFF.md.

The code, sources, plan, test questions and README skeleton are already written. The job on
this machine is to **run it for real, review the results, capture evidence and fill in the
README**. Do not rebuild the project.

## Hard rules

1. **No invented results.** Every number, answer, timing and spec in the README comes from a
   file under `evidence/` or `data/`. If a value cannot be traced to a file, it does not go in.
2. **Offline means offline.** The graded run is `scripts/run_offline_evidence.ps1`, started by
   Jack with Wi-Fi off. It refuses to run if the internet is reachable. Never label online
   output as offline. Rehearsal runs go in `evidence/rehearsal/` and are labelled as online.
3. **Originals are never edited.** Nothing in `vault/raw/` changes. If a generated note is wrong,
   fix the note in `vault/wiki/`, not the source. `data/source_catalog.json` hashes prove it.
4. **Report failures honestly.** A wrong or weak answer stays in the evidence and gets explained.
   If a setting is changed after a failure, keep the first run (rename its folder to
   `evidence/offline-run1/`), document the change, and rerun the affected tests offline.
5. **Keep modes separate.** Don't let chat history, the persona or test answers reach ask mode.
   Keep `tests/questions.json` out of `vault/`.
6. **Model weights and credentials never get committed.**
7. **Ask Jack before** changing the model size, changing the test questions, or pushing.

## Commands

```powershell
.\wiki --help
.\wiki ingest ./vault/raw            # [--source mnist] [--note "Title"] [--force] [--dry-run]
.\wiki search "query"
.\wiki ask "question" [--save]
.\wiki chat
.\wiki check [--out NAME]
.\wiki doctor [--out NAME]
.\wiki eval --out NAME               # the four ask tests -> evidence/NAME/T1..T4.md
.\wiki modecheck --out NAME          # chat/search/ask checks -> evidence/NAME/mode-checks.md
python -m unittest discover tests    # plumbing tests, fake backend, no model needed
```

## Reviewing generated wiki notes

For every note in `vault/wiki/`: read it against the cited sections of the originals. Fix
invented or wrong statements, and fix numbers `wiki check` flags if they really are wrong. Keep
filenames, headings, the Related notes and Sources sections as the harness wrote them. Then set
`reviewed: true` in the front matter. Record what was corrected in README section 5.

## Assessing evidence cards

Each `evidence/offline/T*.md` card ends with "Assessment: to be written". Replace it with
two to four honest sentences: did retrieval find the expected passage (and at what rank), is
every material claim supported by the cited passage, are the citations correct, and is it a
pass, partial or fail. Do the same for each "Result: to be assessed" line in
`mode-checks.md`. Don't edit Gemma's answers or the retrieved passages.

## Definition of done

- `evidence/offline/` has doctor.json, after/doctor.json, T1–T4 cards (.md + .json),
  ask-tests-summary.json, mode-checks.md, wiki-check.json and terminal-transcript.txt, all
  showing internet reachable = False.
- `evidence/screenshots/` has obsidian-note.png, obsidian-index.png, obsidian-graph.png and
  offline-terminal.png.
- Wiki notes reviewed and marked `reviewed: true`; `wiki check` clean or remaining issues
  explained.
- README: no `{{` left (`Select-String -Path README.md -Pattern '\{\{'` returns nothing), the
  fill-in comment deleted, every link resolves.
- Pushed to `main`; repo opened signed out (private window) and everything loads.
