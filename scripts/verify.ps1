# Full local verification. Exit: 0 pass, 1 checks failed, 2 baseline regressed, 3 environment.
param([string]$Repo = '')
$ErrorActionPreference = 'Stop'
if (-not $Repo) { $Repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
if (-not $env:GRIDLOCK_TEST_PORT) { $env:GRIDLOCK_TEST_PORT = '8790' }
if (-not $env:GRIDLOCK_PY) { $env:GRIDLOCK_PY = Join-Path $env:USERPROFILE 'dev\gridlock-venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $env:GRIDLOCK_PY)) { Write-Error 'GridLock Python venv is missing; run SETUP.cmd'; exit 3 }
if (-not $env:PLAYWRIGHT_BROWSERS_PATH) { $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:USERPROFILE 'dev\ms-playwright' }
$env:GRIDLOCK_AI = 'off'
& $env:GRIDLOCK_PY -c "from tests.harness import required_test_port, require_free_loopback_port; require_free_loopback_port(required_test_port())"
if ($LASTEXITCODE -ne 0) { Write-Output 'VERIFY test port is already bound or invalid'; exit 3 }
$runRoot = Join-Path $env:USERPROFILE 'dev\gridlock-runs\verify'
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$runDir = Join-Path $runRoot $stamp
New-Item -ItemType Directory -Path $runDir | Out-Null
$xmlPath = Join-Path $runDir 'pytest.xml'
$summaryPath = Join-Path $runDir 'summary.json'
$baseline = Get-Content -Encoding UTF8 (Join-Path $Repo 'scripts\verify-baseline.json') -Raw | ConvertFrom-Json
Push-Location $Repo
try {
  & $env:GRIDLOCK_PY -m compileall -q pipeline server tests
  if ($LASTEXITCODE -ne 0) { Write-Output 'VERIFY compile failed'; exit 1 }
  & $env:GRIDLOCK_PY -m pytest -q --junitxml=$xmlPath
  $pytestExit = $LASTEXITCODE
  if (-not (Test-Path -LiteralPath $xmlPath)) { Write-Output 'VERIFY pytest produced no summary'; exit 3 }
  [xml]$report = Get-Content -Encoding UTF8 $xmlPath -Raw
  $suite = $report.testsuites.testsuite
  if (-not $suite) { $suite = $report.testsuite }
  $total = [int]$suite.tests
  $failed = [int]$suite.failures + [int]$suite.errors
  $skipped = [int]$suite.skipped
  $passed = $total - $failed - $skipped
  $skipReasons = @($suite.testcase | Where-Object { $_.skipped } | ForEach-Object { $_.skipped.message })
  $unknownSkips = @($skipReasons | Where-Object { $_ -notin $baseline.allowed_skips })
  $code = 0
  if ($pytestExit -ne 0 -or $failed -gt 0) { $code = 1 }
  if ($code -eq 0 -and ($passed -lt [int]$baseline.passed -or $unknownSkips.Count -gt 0)) { $code = 2 }
  $summary = [ordered]@{ exit_code=$code; passed=$passed; failed=$failed; skipped=$skipped; baseline_passed=[int]$baseline.passed; unknown_skips=$unknownSkips; pytest_xml=$xmlPath; commit=(git rev-parse --short HEAD) }
  [System.IO.File]::WriteAllText($summaryPath, ($summary | ConvertTo-Json -Depth 5), [System.Text.Encoding]::UTF8)
  Write-Output ("VERIFY summary: {0}" -f $summaryPath)
  Write-Output ("passed={0} failed={1} skipped={2} baseline={3} exit={4}" -f $passed,$failed,$skipped,$baseline.passed,$code)
  exit $code
} finally { Pop-Location }
