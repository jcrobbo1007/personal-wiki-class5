# Kickoff prompt for Claude Code (paste everything below the line)

> Start Claude Code in `C:\Users\jcrob\code`. It will clone the repo itself.

---

You are helping me finish Assignment 4 of "From Zero to AI Agents" (Class 5): a personal wiki
CLI that uses a **local Gemma model + RAG**, run **offline**, submitted as one public GitHub
repo. The project is already built and pushed. Your job is to set it up on this Windows
laptop, run it for real, review the results, capture the evidence and finish the README.
Do not rebuild or redesign it.

**1. Get the repo and the rules**

- `git clone https://github.com/jcrobbo1007/personal-wiki-class5` into `C:\Users\jcrob\code`
  and `cd` into it.
- Read `CLAUDE.md` and follow it for the whole task. Then skim `README.md` (the skeleton you'll
  fill in), `tests/questions.json` (the fixed tests) and `scripts/run_offline_evidence.ps1`.

**2. Check the machine, then confirm the model with me**

Report the OS, CPU, total and available RAM, any GPU and its VRAM, and free disk space. The
plan is **Gemma 4 E2B** (`gemma4:e2b` in Ollama, about 3 GB at 4-bit). Tell me in two lines
whether it fits comfortably and whether E4B would be worth it. Wait for my OK before downloading.

**3. Set up (online)**

- Run `powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1`. It installs Ollama
  with winget if missing, pulls the model, gets a test reply and runs the harness self-tests.
- If the Ollama tag differs from `gemma4:e2b`, find the right E2B tag, update `model` in
  `config.json` and tell me.
- Rehearse once, online, clearly labelled: `.\wiki ingest ./vault/raw`, then
  `.\wiki eval --out rehearsal`, then `.\wiki modecheck --out rehearsal`. Read the outputs. If
  the harness crashes, fix the bug and tell me what you changed. If answers are weak, tell me;
  don't tune until I agree. Show me the T1–T4 statuses and timings.

**4. The offline run: I do this part**

Tell me when you're ready. I will turn Wi-Fi off, open a **separate** PowerShell window in the
repo and run:

```
powershell -ExecutionPolicy Bypass -File scripts\run_offline_evidence.ps1
```

It refuses to start while online. It restarts Ollama, runs help, doctor, ingest, a duplicate
check (re-ingest of one source), check, search, ask, the four ask tests, the mode checks and
doctor again. All output goes to `evidence\offline\`. I'll screenshot that window as
`evidence\screenshots\offline-terminal.png`, reconnect and tell you. Don't run anything while
I'm offline.

**5. After I reconnect**

- Confirm that every record in `evidence/offline/` says internet reachable = False and names
  `gemma4:e2b` with local execution. If anything is missing or failed, tell me before going on.
- **Review the wiki**: read each note in `vault/wiki/` against its cited original sections
  (`wiki check` flags numbers not found in the sources). Fix wrong or invented statements in the
  notes (never in `vault/raw/`), set `reviewed: true` in each note's front matter, then run
  `.\wiki check --out review`. Keep a list of what you corrected.
- **Assess the evidence**: write the Assessment section in T1–T4 and the Result lines in
  `mode-checks.md`. Read each cited passage against each claim, and say pass, partial or fail.
- **Obsidian**: walk me through opening the `vault` folder (not the repo) as a vault in
  Obsidian. The graph filter `path:wiki/` with attachments hidden is already saved. Have me save
  three screenshots to `evidence\screenshots\` as `obsidian-note.png` (an open note showing
  Related notes and Sources), `obsidian-index.png` and `obsidian-graph.png` (labels readable).

**6. Write it up**

Fill every `{{placeholder}}` in `README.md` from the evidence files: device, model digest and
quantization, memory, timings, the T1–T4 table, the mode-check table, the review corrections,
the traced path, and one real limitation with one concrete improvement. Delete the fill-in
comment and any placeholder whose data doesn't exist. Replace the `[[...]]` in "Traced path"
with plain text, because GitHub doesn't render wiki links. Check that no `{{` is left and every
link resolves.

**7. Publish**

Show me the README summary and `git status`, then commit and push to `main` once I confirm.
Open the repo in a signed-out private window and check that the README, code, `vault/`,
evidence cards and screenshots all load. Walk the Definition of done in `CLAUDE.md` with me.
Then give me the repo URL to submit on the course portal.
