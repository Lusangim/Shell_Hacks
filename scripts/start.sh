#!/usr/bin/env bash
# Start GridLock on macOS and Linux (also runs in Git Bash on Windows): http://127.0.0.1:8765
#   --google      also offer Google Maps / Satellite (needs your own key file; see RUNNING.md)
#   --no-browser  do not open a browser
#   --port N      use another port (Google Maps only works on 8765)
set -euo pipefail
cd "$(dirname "$0")/.."

PORT=8765
BROWSER=1
while [ $# -gt 0 ]; do
  case "$1" in
    --google) export GRIDLOCK_GOOGLE=on ;;
    --no-browser) BROWSER=0 ;;
    --port) PORT="${2:?--port needs a number}"; shift ;;
    *) echo "Unknown option: $1 (use --google, --no-browser or --port N)"; exit 2 ;;
  esac
  shift
done

VENV="${GRIDLOCK_VENV:-$HOME/dev/gridlock-venv}"
if [ -x "$VENV/bin/python" ]; then PY="$VENV/bin/python"
elif [ -x "$VENV/Scripts/python.exe" ]; then PY="$VENV/Scripts/python.exe"
else echo "GridLock's Python environment is missing; run SETUP first."; exit 3
fi

export GRIDLOCK_AI=off
export GRIDLOCK_TEST_PORT="$PORT"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/dev/ms-playwright}"
"$PY" -c "from tests.harness import require_free_loopback_port; require_free_loopback_port($PORT)" 2>/dev/null ||
  { echo "Port $PORT is already in use (another GridLock may be running)."; exit 3; }

URL="http://127.0.0.1:$PORT/"
if [ "$BROWSER" = 1 ]; then
  (
    sleep 2
    case "$(uname -s)" in
      Darwin) open "$URL" ;;
      Linux) xdg-open "$URL" >/dev/null 2>&1 || echo "Open $URL in your browser" ;;
      MINGW*|MSYS*|CYGWIN*) cmd.exe /c start "" "$URL" ;;
      *) echo "Open $URL in your browser" ;;
    esac
  ) &
fi
echo "GridLock is running at $URL (close this window or press Ctrl+C to stop)"
exec "$PY" -m server
