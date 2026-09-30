# The graded offline run. Turn Wi-Fi OFF (and unplug Ethernet) first, then from the repo root:
#     powershell -ExecutionPolicy Bypass -File scripts\run_offline_evidence.ps1
# Every step is a fresh CLI process (a restart each time). Everything is written to evidence\offline\.
$ErrorActionPreference = "Continue"
# UTF-8 end to end, so dashes and arrows in the output survive the transcript.
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$Out = "offline"
$Dir = "evidence\$Out"
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
$Log = "$Dir\terminal-transcript.txt"
"Offline evidence run started $(Get-Date -Format s)" | Out-File -Encoding utf8 $Log

function Step($title, [scriptblock]$cmd) {
    $line = "`n===== $title ====="
    Write-Host $line -ForegroundColor Cyan
    $line | Out-File -Append -Encoding utf8 $Log
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $cmd 2>&1 | ForEach-Object { "$_" } | ForEach-Object { $_; $_ | Out-File -Append -Encoding utf8 $Log }
    $t = "(step took $([math]::Round($sw.Elapsed.TotalSeconds,1)) s)"
    $t; $t | Out-File -Append -Encoding utf8 $Log
}

# 0. Prove we are offline before anything else.
$online = Test-NetConnection 1.1.1.1 -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($online) {
    Write-Host "Internet is still reachable. Turn off Wi-Fi / unplug Ethernet and run this again." -ForegroundColor Red
    exit 1
}
Step "Network check: internet reachable = $online" { Get-NetAdapter | Select-Object Name, Status | Format-Table | Out-String }

# Restart the local runtime so nothing is cached from the online session.
Step "Restart Ollama (local runtime only)" {
    Get-Process | Where-Object { $_.ProcessName -like "ollama*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
    Start-Process ollama -ArgumentList serve -WindowStyle Hidden
    Start-Sleep 6
    ollama list
}

Step "wiki --help"                         { python wiki.py --help }
Step "wiki doctor (device + model, before)" { python wiki.py doctor --out $Out }
Step "wiki ingest ./vault/raw"             { python wiki.py ingest ./vault/raw }

$before = (Get-ChildItem vault\wiki -Recurse -Filter *.md | ForEach-Object { $_.FullName }) | Sort-Object
Step "Re-ingest one source (mnist) to check for duplicates" { python wiki.py ingest ./vault/raw --source mnist }
$after = (Get-ChildItem vault\wiki -Recurse -Filter *.md | ForEach-Object { $_.FullName }) | Sort-Object
$dupe = Compare-Object $before $after
Step "Duplicate check" {
    "notes before re-ingest: $($before.Count)   after: $($after.Count)"
    if ($dupe) { "NEW OR MISSING FILES:"; $dupe | Out-String } else { "No new files: re-ingest updated notes in place." }
}

Step "wiki check (links, headings, sources, numbers)" { python wiki.py check --out $Out }
Step "wiki search `"exploration rate`" (no model call)" { python wiki.py search "exploration rate" }
Step "wiki ask (single example, saved card)" { python wiki.py ask "What learning rate did I use for the MNIST model?" --save }
Step "wiki eval: the four ask-mode tests" { python wiki.py eval --out $Out }
Step "wiki modecheck: chat / search / ask boundaries" { python wiki.py modecheck --out $Out }
Step "wiki doctor (memory with model loaded, after)" { python wiki.py doctor --out "$Out\after" }
Step "ollama ps" { ollama ps }

$online2 = Test-NetConnection 1.1.1.1 -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
Step "Network check at end: internet reachable = $online2" { "finished $(Get-Date -Format s)" }

Write-Host "`nDone. Take a screenshot of this window now (evidence\screenshots\offline-terminal.png)." -ForegroundColor Green
Write-Host "Optional: run  python wiki.py chat  for a short live chat, screenshot it, then /exit." -ForegroundColor Green
Write-Host "Then reconnect to the internet and tell Claude Code the offline run is finished." -ForegroundColor Green
