# Local setup for an existing machine or a fresh checkout. ASCII only.
# SETUP.cmd              Python environment + packages + the modern offline map (about 220 MB, once)
# SETUP.cmd -Tests       also installs the Chromium browser used by VERIFY.cmd (large download)
# SETUP.cmd -NoMap       skip the map download (the app then shows its plain fallback map)
# SETUP.cmd -Offline     check an existing environment without downloading anything
param([switch]$Offline, [switch]$Tests, [switch]$NoMap)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $env:GRIDLOCK_PY) { $env:GRIDLOCK_PY = Join-Path $env:USERPROFILE 'dev\gridlock-venv\Scripts\python.exe' }
if (-not $env:PLAYWRIGHT_BROWSERS_PATH) { $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:USERPROFILE 'dev\ms-playwright' }
$env:GRIDLOCK_AI = 'off'

# 1. Python environment with the pinned packages
if (-not (Test-Path -LiteralPath $env:GRIDLOCK_PY)) {
  if ($Offline) { throw 'GridLock venv is missing; offline setup cannot create it without packages' }
  $venv = Split-Path (Split-Path $env:GRIDLOCK_PY -Parent) -Parent
  Write-Output "Creating the Python 3.12 environment in $venv ..."
  py -3.12 -m venv $venv
  if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required (install it from python.org with the py launcher)' }
  & $env:GRIDLOCK_PY -m pip install --requirement (Join-Path $repo 'requirements.txt')
  if ($LASTEXITCODE -ne 0) { throw 'Pinned package installation failed' }
}
& $env:GRIDLOCK_PY -c "import fastapi, uvicorn, pydantic, pytest, playwright, shapely, pyproj, pypdf"
if ($LASTEXITCODE -ne 0) { throw 'GridLock venv is incomplete; check pinned requirements' }
Write-Output 'Python environment: OK'

# 2. Modern offline base map (OpenStreetMap via Protomaps)
if ($NoMap -or $Offline) {
  Write-Output 'Modern map: skipped (the app shows its plain fallback map until you run GET-MAP.cmd)'
} else {
  & $env:GRIDLOCK_PY (Join-Path $repo 'scripts\get_map.py')
  if ($LASTEXITCODE -ne 0) { Write-Output 'Modern map: not downloaded (the app still runs with its plain fallback map; try GET-MAP.cmd later)' }
}

# 3. Test browser, only needed for VERIFY.cmd
if (Test-Path -LiteralPath $env:PLAYWRIGHT_BROWSERS_PATH) {
  Write-Output 'Test browser: OK'
} elseif ($Tests -and -not $Offline) {
  & $env:GRIDLOCK_PY -m playwright install chromium
  if ($LASTEXITCODE -ne 0) { throw 'Chromium install for tests failed' }
  Write-Output 'Test browser: installed'
} else {
  Write-Output 'Test browser: not installed (only VERIFY.cmd needs it; run SETUP.cmd -Tests)'
}
Write-Output 'SETUP PASS: run START.cmd to open GridLock'
