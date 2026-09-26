# Start the local app. ASCII only.
param([int]$Port = 8765, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $env:GRIDLOCK_PY) { $env:GRIDLOCK_PY = Join-Path $env:USERPROFILE 'dev\gridlock-venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $env:GRIDLOCK_PY)) { Write-Error 'GridLock Python venv is missing; run SETUP.cmd'; exit 3 }
if (-not $env:PLAYWRIGHT_BROWSERS_PATH) { $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:USERPROFILE 'dev\ms-playwright' }
$env:GRIDLOCK_AI = 'off'
$env:GRIDLOCK_TEST_PORT = [string]$Port
Push-Location $repo
try {
  & $env:GRIDLOCK_PY -c "from tests.harness import require_free_loopback_port; require_free_loopback_port($Port)"
  if ($LASTEXITCODE -ne 0) { Write-Error "Port $Port is already in use"; exit 3 }
  if (-not $NoBrowser) { Start-Process ("http://127.0.0.1:{0}/" -f $Port) }
  & $env:GRIDLOCK_PY -m server
  exit $LASTEXITCODE
} finally { Pop-Location }
