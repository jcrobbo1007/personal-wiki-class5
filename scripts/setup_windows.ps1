# Run ONCE while ONLINE, from the repo root:   powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
# Installs Ollama (if missing), downloads the Gemma model, and checks that a local reply works.
$ErrorActionPreference = "Stop"
$Model = (Get-Content config.json | ConvertFrom-Json).model

Write-Host "== Python"
python --version
if ($LASTEXITCODE -ne 0) { throw "Python 3.10+ is required on PATH." }

Write-Host "== Ollama"
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Ollama with winget..."
    winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
    $env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"
}
ollama --version

# Make sure the local server is up (the Ollama app normally starts it).
try { Invoke-RestMethod http://127.0.0.1:11434/api/version | Out-Null }
catch { Start-Process ollama -ArgumentList serve -WindowStyle Hidden; Start-Sleep 5 }

Write-Host "== Downloading $Model (one time)"
ollama pull $Model
ollama list

Write-Host "== Local test reply"
ollama run $Model "Reply with exactly: local gemma ok"

Write-Host "== Harness self-test (no model needed)"
python -m unittest discover tests

Write-Host "`nSetup done. Next: disconnect from the internet and run scripts\run_offline_evidence.ps1"
