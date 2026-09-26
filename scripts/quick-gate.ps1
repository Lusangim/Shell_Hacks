# Per-merge gate. ASCII only; each invocation owns its GRIDLOCK_TEST_PORT.
param([string]$Repo = '')
$ErrorActionPreference = 'Stop'
if (-not $Repo) { $Repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
if (-not $env:GRIDLOCK_TEST_PORT) { Write-Error 'GRIDLOCK_TEST_PORT is required'; exit 3 }
$lanePort = [int]$env:GRIDLOCK_TEST_PORT
if (-not $env:GRIDLOCK_PY) { $env:GRIDLOCK_PY = Join-Path $env:USERPROFILE 'dev\gridlock-venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $env:GRIDLOCK_PY)) { Write-Error 'GridLock Python venv is missing; run SETUP.cmd'; exit 3 }
if (-not $env:PLAYWRIGHT_BROWSERS_PATH) { $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:USERPROFILE 'dev\ms-playwright' }
$env:GRIDLOCK_AI = 'off'
Push-Location $Repo
try {
  & $env:GRIDLOCK_PY -c "from tests.harness import required_test_port, require_free_loopback_port; require_free_loopback_port(required_test_port())"
  if ($LASTEXITCODE -ne 0) { Write-Output 'QUICK GATE test port is already bound or invalid'; exit 3 }
  & $env:GRIDLOCK_PY -m compileall -q pipeline server tests
  if ($LASTEXITCODE -ne 0) { exit 1 }
  & $env:GRIDLOCK_PY -m pytest -q
  if ($LASTEXITCODE -ne 0) { exit 1 }
  if (Test-Path -LiteralPath 'tests\e2e\test_shell.py') {
    $env:GRIDLOCK_TEST_PORT = [string]($lanePort + 3000)
    & $env:GRIDLOCK_PY -m pytest tests\e2e\test_shell.py -q
    if ($LASTEXITCODE -ne 0) { exit 1 }
  } else { Write-Output 'SKIP allow-list: no web shell yet (e2e smoke)' }
  if ((Test-Path -LiteralPath 'web\index.html') -and (Test-Path -LiteralPath 'tests\e2e\audits')) {
    $env:GRIDLOCK_TEST_PORT = [string]($lanePort + 6000)
    & $env:GRIDLOCK_PY -m pytest tests\e2e\audits -q
    if ($LASTEXITCODE -ne 0) { exit 1 }
  } elseif (-not (Test-Path -LiteralPath 'web\index.html')) {
    Write-Output 'SKIP allow-list: no web shell yet (axe default)'
  } else { Write-Error 'Web shell exists but the required axe audit is missing'; exit 1 }
  Write-Output 'QUICK GATE PASS'
  exit 0
} finally { $env:GRIDLOCK_TEST_PORT = [string]$lanePort; Pop-Location }
