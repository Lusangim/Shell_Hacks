# GridLock: ShellHacks 2026 (Sperry Tech challenge)

GridLock finds where neighboring electric utilities' **planned** transmission projects come close in place
and time: within 40 km of each other and entering service around the same years. Planners can then look
at sharing crews, outages, land and permits. It compares Dominion Energy South Carolina's public plan with
the Georgia Power, Georgia Transmission and MEAG projects in the SERTP 2025 regional plan. It shows them on
an interactive street map of Georgia and South Carolina, with a ranked list of pairs, the source document
and page for every project, a savings estimate with its assumptions, and a guided tour.

## Quick start (Windows, macOS, Linux)

1. `git clone https://github.com/Lusangim/Shell_Hacks.git` (needs Python 3.12 and Git)
2. **Set up once:** double-click **`SETUP.cmd`** (Windows), **`SETUP.command`** (macOS) or **`SETUP.sh`**
   (Linux). It installs the Python environment, the packages and the modern street map (about 220 MB, once).
3. **Start:** double-click **`START.cmd`**, **`START.command`** or **`START.sh`**. http://127.0.0.1:8765
   opens in your browser.
4. Click **Take the tour**.

Full instructions (Google Maps and Satellite view, rebuilding the data from the PDFs, tests, Mac and Linux,
troubleshooting): **[RUNNING.md](RUNNING.md)**. How distances, bands and the ranking work (draft):
[docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Data sources (all public)

- Dominion Energy SC planned transmission projects 2026-2030, $2M and above: SCRTP (scrtp.com)
- SERTP 2025 Regional Transmission Plan and Input Assumptions, the publicly posted overview (southeasternrtp.com)
- HIFLD Electric Power Transmission Lines (U.S. DHS; the archived public layer)
- OpenStreetMap substations and street map, © OpenStreetMap contributors (ODbL); map tiles via Protomaps
- U.S. Census Gazetteer places; U.S. state boundaries

Independent student project; not affiliated with Dominion Energy, Georgia Power, Southern Company,
Georgia Transmission, MEAG Power or Sperry Tech. Estimates are for discussion only.
