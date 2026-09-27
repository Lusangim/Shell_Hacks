# GridLock

GridLock is a local screening tool for public transmission plans in Georgia and South Carolina. It ranks nearby projects from different utilities, shows the source pages and location confidence behind each match, and helps a planner decide what to verify next. A ranked pair is a lead for investigation, not a confirmed joint project.

Built for ShellHacks 2026, Sperry Tech GridLock Challenge. It compares Dominion Energy South Carolina's public plan with the Georgia Power, Georgia Transmission and MEAG projects in the SERTP 2025 regional plan.

## Quick start (Windows, macOS, Linux)

1. `git clone https://github.com/Lusangim/Shell_Hacks.git` (needs Python 3.12 and Git)
2. **Set up once:** double-click **`SETUP.cmd`** (Windows), **`SETUP.command`** (macOS) or **`SETUP.sh`**
   (Linux). It installs the Python environment, the pinned packages and the modern street map (about 220 MB, once).
3. **Start:** double-click **`START.cmd`**, **`START.command`** or **`START.sh`**. http://127.0.0.1:8765
   opens in your browser.
4. Click **Take the tour**.

Full instructions (Google Maps and Satellite view, rebuilding the data from the PDFs, tests, Mac and Linux,
troubleshooting): **[RUNNING.md](RUNNING.md)**. How distances, bands and the ranking work:
[docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## What works

- Interactive offline map, project and pair details, 465 ranked opportunities, search, filters, timeline and 1–80 km area explorer.
- Every pair shows why it ranks where it does: its score, factor by factor (distance band × timing × location × state line × savings, with distance leading).
- Source-linked evidence, accuracy and uncertainty labels, 119 possible-saving ranges from the team's unit costs by job type and distance, CSV export and a Letter print report.
- A guided tour and a coordination brief for a selected pair. The default brief is an offline, graded **Template**; the app does not send a message or contact anyone.
- Light and dark themes, keyboard operation, phone layout and an outline-map fallback when the optional offline map archive is absent.

The committed build contains 230 projects from the loaded public plans, 181 mapped project geometries, and 43 pairs whose projects are in different states. Unknown locations remain unknown. The app does not require a Google key, a Claude account or network access for its default experience.

The richer offline street map is an external PMTiles archive, `gasc-z13.pmtiles` (221 MB, not in git). SETUP downloads it once to `~/dev/gridlock-assets/`; `GRIDLOCK_BASEMAP_PMTILES` selects another copy. Without it, GridLock visibly uses its committed state-outline basemap and the list, details and exports still work. A Google Maps key of your own and an online browser can enable optional roadmap/satellite layers (see RUNNING.md).

## Verify

Install the test browser once with `SETUP.cmd -Tests` (Windows) or `./SETUP.sh --tests` (macOS / Linux). Then, on Windows, use a free test port, separate from any running demo server:

```powershell
$env:GRIDLOCK_TEST_PORT = '8790'
$env:GRIDLOCK_GOOGLE = 'off'
.\VERIFY.cmd
```

`VERIFY.cmd` compiles the Python code, runs pytest (including Chromium browser checks) and writes a timestamped `summary.json` under the local `gridlock-runs\verify` folder. It exits nonzero for a failed check, a count below `scripts/verify-baseline.json`, or an unexpected skip. `scripts\quick-gate.ps1` also runs the shell and interface audits used before merges. The delivery report records the final tested commit, totals and exact summary path.

The current local verification baseline is 716 passing tests, with no allowed skips.

## Data and limits

The loaded plans are Dominion Energy SC's 2026–2030 planned-facilities PDF and the SERTP 2025 regional transmission plan. Each project keeps a document and page reference. Committed source inputs and the pipeline are under `data/` and `pipeline/`; the app starts from committed build artifacts without rerunning extraction. Location estimates use named public geography sources; map proximity does not prove shared construction limits. A possible saving is a screening range, not a measured saving or a commitment by either utility.

The public SERTP overview has a source-classification question because some page headers include “(CEII)”; the founder and Sperry must decide public-release treatment before submission. Okatie's placement remains inferred pending a source-drawing check. The loaded plans do not support a Thomson–Vogtle project by name. See [the delivery report](reviews/2026-09-26-gridlock-build/DELIVERY.md) for the current verification, judging findings, remaining decisions and the final status.

Independent student project; not affiliated with Dominion Energy, Georgia Power, Southern Company, Georgia Transmission, MEAG Power or Sperry Tech. Estimates are for discussion only.
