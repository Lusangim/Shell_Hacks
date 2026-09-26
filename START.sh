#!/usr/bin/env bash
# Linux: run (or double-click, "Run as a program") to start GridLock; your browser opens
# http://127.0.0.1:8765. Close the window or press Ctrl+C to stop.
cd "$(dirname "$0")" || exit 1
bash scripts/start.sh "$@"
status=$?
if [ $status -ne 0 ] && [ $status -ne 130 ] && [ -t 0 ]; then
  echo
  read -r -p "GridLock stopped with an error. Press Return to close. " _ || true
fi
exit $status
