#!/usr/bin/env bash
# GridLock setup for macOS and Linux (also runs in Git Bash on Windows).
#   SETUP.command (macOS) / SETUP.sh (Linux): Python environment, packages and the modern street map
#   --tests   also install the Chromium browser used by the automated checks (large download)
#   --no-map  skip the map download (the app then shows its plain fallback map)
set -euo pipefail
cd "$(dirname "$0")/.."

TESTS=0
NOMAP=0
for arg in "$@"; do
  case "$arg" in
    --tests) TESTS=1 ;;
    --no-map) NOMAP=1 ;;
    *) echo "Unknown option: $arg (use --tests or --no-map)"; exit 2 ;;
  esac
done

VENV="${GRIDLOCK_VENV:-$HOME/dev/gridlock-venv}"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/dev/ms-playwright}"
export GRIDLOCK_AI=off

venv_python() {
  if [ -x "$VENV/bin/python" ]; then echo "$VENV/bin/python"
  elif [ -x "$VENV/Scripts/python.exe" ]; then echo "$VENV/Scripts/python.exe"
  else echo ""
  fi
}

find_python312() {
  local candidate
  for candidate in python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null; then
      echo "$candidate"
      return 0
    fi
  done
  if command -v py >/dev/null 2>&1 && py -3.12 -c 'import sys' 2>/dev/null; then
    echo "py -3.12"
    return 0
  fi
  return 1
}

PY="$(venv_python)"
if [ -z "$PY" ]; then
  if ! BASE="$(find_python312)"; then
    echo "Python 3.12 is required."
    echo "  macOS: install it from https://www.python.org/downloads/ (or: brew install python@3.12)"
    echo "  Linux: sudo apt install python3.12 python3.12-venv (or your distribution's Python 3.12 packages)"
    exit 3
  fi
  echo "Creating the Python 3.12 environment in $VENV ..."
  mkdir -p "$(dirname "$VENV")"
  $BASE -m venv "$VENV"
  PY="$(venv_python)"
  "$PY" -m pip install --requirement requirements.txt
fi
"$PY" -c "import fastapi, uvicorn, pydantic, pytest, playwright, shapely, pyproj, pypdf" ||
  { echo "GridLock's Python environment is incomplete; delete $VENV and run setup again."; exit 3; }
echo "Python environment: OK"

if [ "$NOMAP" = 1 ]; then
  echo "Modern map: skipped (the app shows its plain fallback map until you run: $PY scripts/get_map.py)"
elif ! "$PY" scripts/get_map.py; then
  echo "Modern map: not downloaded (the app still runs with its plain fallback map; run setup again later)"
fi

if [ -d "$PLAYWRIGHT_BROWSERS_PATH" ]; then
  echo "Test browser: OK"
elif [ "$TESTS" = 1 ]; then
  "$PY" -m playwright install chromium
  echo "Test browser: installed"
else
  echo "Test browser: not installed (only the automated checks need it; run setup with --tests)"
fi
echo "SETUP PASS: now open START (START.command on macOS, START.sh on Linux)"
