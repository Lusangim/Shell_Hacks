#!/usr/bin/env bash
# macOS: double-click to set up GridLock (Python environment, packages and the modern street map).
cd "$(dirname "$0")" || exit 1
bash scripts/setup.sh "$@"
status=$?
echo
read -r -p "Press Return to close this window. " _ || true
exit $status
