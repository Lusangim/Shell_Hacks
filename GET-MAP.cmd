@echo off
setlocal
rem Download (or re-download with -force) the modern offline base map for GA + SC. SETUP.cmd runs this for you.
if not defined GRIDLOCK_PY set "GRIDLOCK_PY=%USERPROFILE%\dev\gridlock-venv\Scripts\python.exe"
if not exist "%GRIDLOCK_PY%" (
  echo GridLock's Python environment was not found. Run SETUP.cmd first.
  exit /b 3
)
set "ARGS="
if /i "%~1"=="-force" set "ARGS=--force"
if /i "%~1"=="-dryrun" set "ARGS=--dry-run"
"%GRIDLOCK_PY%" "%~dp0scripts\get_map.py" %ARGS%
exit /b %ERRORLEVEL%
