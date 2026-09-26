# Start the local app. ASCII only.
# START.cmd                 open GridLock at http://127.0.0.1:8765
# START.cmd -Google         also offer Google Maps / Satellite (needs your own key file; see RUNNING.md)
# START.cmd -NoBrowser      start the server without opening a browser
param([int]$Port = 8765, [switch]$NoBrowser, [switch]$Google)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $env:GRIDLOCK_PY) { $env:GRIDLOCK_PY = Join-Path $env:USERPROFILE 'dev\gridlock-venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $env:GRIDLOCK_PY)) { Write-Error 'GridLock Python venv is missing; run SETUP.cmd'; exit 3 }
if (-not $env:PLAYWRIGHT_BROWSERS_PATH) { $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:USERPROFILE 'dev\ms-playwright' }
$env:GRIDLOCK_AI = 'off'
$env:GRIDLOCK_TEST_PORT = [string]$Port
if ($Google) { $env:GRIDLOCK_GOOGLE = 'on' }
Push-Location $repo
try {
  & $env:GRIDLOCK_PY -c "from tests.harness import require_free_loopback_port; require_free_loopback_port($Port)"
  if ($LASTEXITCODE -ne 0) { Write-Error "Port $Port is already in use"; exit 3 }
  if (-not $NoBrowser) { Start-Process ("http://127.0.0.1:{0}/" -f $Port) }
  & $env:GRIDLOCK_PY -m server
  exit $LASTEXITCODE
} finally { Pop-Location }
