# GridLock

GridLock is a local screening tool for public transmission plans in Georgia and South Carolina. It ranks nearby projects from different utilities, shows the source pages and location confidence behind each match, and helps a planner decide what to verify next. A ranked pair is a lead for investigation, not a confirmed joint project.

Built for ShellHacks 2026, Sperry Tech GridLock Challenge. It compares Dominion Energy South Carolina's public plan with the Georgia Power, Georgia Transmission and MEAG projects in the SERTP 2025 regional plan.

![GridLock: transmission projects in Georgia and South Carolina on the map, with 465 ranked coordination opportunities](docs/screenshots/01-overview.png)

**Every feature in screenshots: [docs/DEMO.md](docs/DEMO.md)** · **Behind the page (pipeline, contracts, API,
security, tests): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** · **The exact rules: [docs/METHODOLOGY.md](docs/METHODOLOGY.md)**
· **Live demo script and Q&A: [docs/PITCH.md](docs/PITCH.md)**

## At a glance

| | |
| --- | --- |
| ![Pair #1 open: why the two projects appear together](docs/screenshots/04-top-pair.png) | ![Score 5.8 shown factor by factor](docs/screenshots/07-score.png) |
| **Open a pair** to see why the two projects appear together, with the plan page behind every fact. | **Every rank can be checked by hand:** the score, factor by factor, with distance counting most. |
| ![Possible saving by job type and distance](docs/screenshots/06-savings.png) | ![A 40 km area around Savannah](docs/screenshots/11-explore-area.png) |
| **Possible savings** from what the two kinds of work could share at their distance, labelled as an estimate. | **Explore an area** of 1 to 80 km around any place, with its projects and pairs. |
| ![A rebuild drawn along existing transmission lines](docs/screenshots/12-route-along-existing-lines.png) | ![Pair #1 on a phone](docs/screenshots/17-phone-pair.png) |
| **Routes along existing lines** when a plan names only a line's two ends. | **Phone layout**, dark theme and full keyboard use. |

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
- Locations from public map data: a line's real route when one HIFLD line joins its two ends, a route along the existing network when several do, and a "town only" flag when only a town centre matched.
- A guided tour and a coordination brief for a selected pair. The default brief is an offline, graded **Template**; the app does not send a message or contact anyone.
- Light and dark themes, keyboard operation, phone layout and an outline-map fallback when the optional offline map archive is absent.

The committed build contains 230 projects from the loaded public plans, 181 mapped project geometries, and 43 pairs whose projects are in different states. Unknown locations remain unknown. The app does not require a Google key, a Claude account or network access for its default experience.

## How it works

- **Pipeline** (Python, offline, about 4 seconds): two plan PDFs → 481 rows → 230 projects in Georgia and South
  Carolina → 181 placed on the map from public substation and line data → 465 pairs within 40 km → savings and
  ranks. Every file is checked against Pydantic data contracts, and rebuilds are byte-identical.
- **Server** (FastAPI, loopback only): read-only JSON routes for projects, pairs, search, areas, briefs, CSV and
  the source PDFs; a Content Security Policy; short JSON errors; a guarded, switched-off AI brief route.
- **Web app** (Leaflet, no build step): the map, ranked list, pair and project details, brief, export, print and
  tour, in light and dark, on desktop and phone.

The details, with a diagram and a sample API response, are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

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

SERTP posts its 2025 plan publicly, though some of its page headers include “(CEII)”; GridLock uses only that public document. Okatie's location is inferred from a junction on the Jasper–Yemassee line and is labelled inferred in the app. The loaded plans do not support a Thomson–Vogtle project by name. See [the delivery report](reviews/2026-09-26-gridlock-build/DELIVERY.md) for the build's verification and judging record.

Independent student project; not affiliated with Dominion Energy, Georgia Power, Southern Company, Georgia Transmission, MEAG Power or Sperry Tech. Estimates are for discussion only.

## Team

Luciano Sanchez, Daniel Cabrera, Srija Uprety and Alex Demarco Sarria, at ShellHacks 2026.

## Licence

GridLock's code and documentation are under the [MIT License](LICENSE). Libraries, source documents and map data
keep their own terms: see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
