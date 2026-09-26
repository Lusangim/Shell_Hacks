# GridLock

GridLock is a local screening tool for public transmission plans in Georgia and South Carolina. It ranks nearby projects from different utilities, shows the source pages and location confidence behind each match, and helps a planner decide what to verify next. A ranked pair is a lead for investigation, not a confirmed joint project.

## What works

- Interactive offline map, project and pair details, 489 ranked opportunities, search, filters, timeline and 1–80 km area explorer.
- Source-linked evidence, accuracy and uncertainty labels, 201 possible-saving ranges with stated team assumptions, CSV export and a Letter print report.
- A guided tour and a coordination brief for a selected pair. The default brief is an offline, graded **Template**; the app does not send a message or contact anyone.
- Light and dark themes, keyboard operation, phone layout and an outline-map fallback when the optional offline map archive is absent.

The committed build contains 230 projects from the loaded public plans, 181 mapped project geometries, and 43 pairs whose projects are in different states. Unknown locations remain unknown. The app does not require a Google key, a Claude account or network access for its default experience.

## Run locally on Windows

The project uses Python 3.12, the pinned packages in `requirements.txt`, and an approved Playwright Chromium bundle for verification. `SETUP.cmd -Offline` checks an already prepared environment without downloading anything. The setup script can install pinned Python packages when offline mode is omitted, but it does not fetch the browser bundle. If your Python or browser folders differ from the script defaults, set `GRIDLOCK_PY` and `PLAYWRIGHT_BROWSERS_PATH` to their local paths first.

From the repository root in PowerShell:

```powershell
.\SETUP.cmd -Offline
$env:GRIDLOCK_GOOGLE = 'off'
.\START.cmd -Port 8765
```

Open `http://127.0.0.1:8765/` if the browser did not open. The server binds to loopback. `START.cmd -NoBrowser -Port 8765` keeps browser launch separate. Stop the server with Ctrl+C.

The richer offline street map uses an external PMTiles archive, `gasc-z13.pmtiles`, selected by `GRIDLOCK_BASEMAP_PMTILES` or the script's local default. That 221 MB archive is not in git. Without it, GridLock visibly uses its committed state-outline basemap and the list, details and exports still work. A founder-configured Google Maps key and an online browser can enable optional roadmap/satellite layers; that live provider path was not exercised in this build.

## Verify

Use a free test port, separate from any running demo server:

```powershell
$env:GRIDLOCK_TEST_PORT = '8790'
$env:GRIDLOCK_GOOGLE = 'off'
.\VERIFY.cmd
```

`VERIFY.cmd` compiles the Python code, runs pytest (including Chromium browser checks) and writes a timestamped `summary.json` under the local `gridlock-runs\verify` folder. It exits nonzero for a failed check, a count below `scripts/verify-baseline.json`, or an unexpected skip. `scripts\quick-gate.ps1` also runs the shell and interface audits used before merges. The delivery report records the final tested commit, totals and exact summary path.

## Data and limits

The loaded plans are Dominion Energy SC's 2026–2030 planned-facilities PDF and the SERTP 2025 regional transmission plan. Each project keeps a document and page reference. Committed source inputs and the pipeline are under `gridlock-data/` and `pipeline/`; the app starts from committed build artifacts without rerunning extraction. Location estimates use named public geography sources; map proximity does not prove shared construction limits. A possible saving is a screening range, not a measured saving or a commitment by either utility.

The public SERTP overview has a source-classification question because some page headers include “(CEII)”; the founder and Sperry must decide public-release treatment before submission. Okatie's placement remains inferred pending a source-drawing check. The loaded plans do not support a Thomson–Vogtle project by name. See [the delivery report](reviews/2026-09-26-gridlock-build/DELIVERY.md) for the current verification, judging findings, remaining decisions and the final status.
