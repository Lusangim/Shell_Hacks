#!/usr/bin/env bash
# macOS: double-click to start GridLock; your browser opens http://127.0.0.1:8765. Close this window to stop.
cd "$(dirname "$0")" || exit 1
bash scripts/start.sh "$@"
status=$?
if [ $status -ne 0 ] && [ $status -ne 130 ]; then
  echo
  read -r -p "GridLock stopped with an error. Press Return to close this window. " _ || true
fi
exit $status
