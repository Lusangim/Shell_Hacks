#!/usr/bin/env bash
# Linux: run (or double-click, "Run as a program") to set up GridLock: Python environment, packages and
# the modern street map.
cd "$(dirname "$0")" || exit 1
bash scripts/setup.sh "$@"
status=$?
if [ -t 0 ]; then echo; read -r -p "Press Return to close. " _ || true; fi
exit $status
