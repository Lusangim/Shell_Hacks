# Local setup for an existing machine or a fresh checkout. ASCII only.
param([switch]$Offline)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $env:GRIDLOCK_PY) { $env:GRIDLOCK_PY = Join-Path $env:USERPROFILE 'dev\gridlock-venv\Scripts\python.exe' }
if (-not $env:PLAYWRIGHT_BROWSERS_PATH) { $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:USERPROFILE 'dev\ms-playwright' }
$env:GRIDLOCK_AI = 'off'
if (-not (Test-Path -LiteralPath $env:GRIDLOCK_PY)) {
  if ($Offline) { throw 'GridLock venv is missing; offline setup cannot create it without packages' }
  $venv = Split-Path (Split-Path $env:GRIDLOCK_PY -Parent) -Parent
  py -3.12 -m venv $venv
  if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required to create the GridLock venv' }
  & $env:GRIDLOCK_PY -m pip install --requirement (Join-Path $repo 'requirements.txt')
  if ($LASTEXITCODE -ne 0) { throw 'Pinned package installation failed' }
}
& $env:GRIDLOCK_PY -c "import fastapi, uvicorn, pydantic, pytest, playwright, shapely, pyproj, pypdf"
if ($LASTEXITCODE -ne 0) { throw 'GridLock venv is incomplete; check pinned requirements' }
if (-not (Test-Path -LiteralPath $env:PLAYWRIGHT_BROWSERS_PATH)) {
  throw 'Chromium browser folder is missing; copy the approved Playwright browser bundle before VERIFY'
}
Write-Output 'SETUP PASS: pinned Python environment and approved browser folder found'
