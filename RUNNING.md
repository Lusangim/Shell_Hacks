# Running GridLock

GridLock runs on your own laptop: a small local server plus a web page at http://127.0.0.1:8765.
No account is needed. Internet is needed only during setup (and for the optional Google Maps view).

## What you need (Windows 10 or 11)

- **Python 3.12** from [python.org](https://www.python.org/downloads/) (keep "py launcher" ticked in the installer)
- **Git** from [git-scm.com](https://git-scm.com/)
- About **1 GB** of free disk space (packages plus the 220 MB map file)

## Run it in 4 steps

1. Get the code:
   ```
   git clone https://github.com/Lusangim/Shell_Hacks.git
   ```
2. Open the `Shell_Hacks` folder and double-click **`SETUP.cmd`**. It creates the Python environment in
   `%USERPROFILE%\dev\gridlock-venv`, installs the pinned packages, and downloads the modern street map of
   Georgia and South Carolina (about 220 MB, only once). Wait for `SETUP PASS`.
3. Double-click **`START.cmd`**. Your browser opens http://127.0.0.1:8765.
4. Click **Take the tour** for a guided walkthrough of the demo.

To stop GridLock, close the START window (or press Ctrl+C in it).

## Optional

### Google Maps and Satellite view

1. In [Google Cloud](https://console.cloud.google.com/), enable **Maps JavaScript API** and create an API key.
   Restrict it: *Websites* `http://127.0.0.1:8765/*` and `http://localhost:8765/*`; *APIs* Maps JavaScript API
   only. Billing must be enabled on the project; normal use stays inside Google's free monthly limit.
2. Save the key, alone on one line, as `%USERPROFILE%\dev\gridlock-assets\google-maps-key.txt`.
   Never commit it or paste it into a chat.
3. Open a Command Prompt in the `Shell_Hacks` folder and run `START.cmd -Google`. A
   **Map / Google Maps / Satellite** switch appears while you are online.

### Rebuild the data from the source PDFs

The built map data is already in the repo. To rebuild it yourself, open a Command Prompt in the
`Shell_Hacks` folder:
```
%USERPROFILE%\dev\gridlock-venv\Scripts\python.exe -m pipeline.extract
%USERPROFILE%\dev\gridlock-venv\Scripts\python.exe -m pipeline.build_all
```
`pipeline.extract` reads the two plan PDFs in `data/raw/` (54 Dominion Energy SC projects, 427 SERTP rows).
`pipeline.build_all` places the projects on the map and finds the pairs (230 kept, 181 placed, 489 pairs,
43 across the state line). The rebuilt files match the committed ones exactly.

### Run the automated checks

```
SETUP.cmd -Tests
VERIFY.cmd
```
`-Tests` installs the Chromium browser the checks use (about 700 MB on disk).

### Get the map again

Run `GET-MAP.cmd` (or `GET-MAP.cmd -force` to replace it). Without the map file, GridLock still runs with
a plain outline map.

## Mac or Linux (not yet tested)

```
python3.12 -m venv ~/dev/gridlock-venv
~/dev/gridlock-venv/bin/pip install -r requirements.txt
~/dev/gridlock-venv/bin/python scripts/get_map.py
GRIDLOCK_AI=off ~/dev/gridlock-venv/bin/python -m server
```
Then open http://127.0.0.1:8765.

## Troubleshooting

- **"Port 8765 is already in use"**: another GridLock is already running; close it, or run
  `START.cmd -Port 8766` (Google Maps only works on port 8765).
- **A plain grey outline map instead of streets**: the map file is missing; run `GET-MAP.cmd`.
- **"Python 3.12 is required"**: install Python 3.12 from python.org, then run `SETUP.cmd` again.

## Where things are

- `pipeline/`: reads the plan PDFs and builds the map data (`extract.py`, `build_all.py`, ...)
- `server/`: the local API
- `web/`: the map page
- `data/raw/`: source documents and public inputs; `data/build/`: the generated map data
- `tests/`: automated checks
- `scripts/`: setup, start, verify and map-download scripts

## Data and credits

- Dominion Energy SC: SCRTP planned facilities 2026-2030, $2M and above ([scrtp.com](https://www.scrtp.com/assets/pdfs/home/2026-2030-2million-and-above-project-descriptions.pdf))
- Georgia Power, Georgia Transmission and MEAG: SERTP 2025 Regional Transmission Plan ([southeasternrtp.com](https://www.southeasternrtp.com/docs/general/2025/2025%20Regional%20Transmission%20Plan%20and%20Input%20Assumptions.pdf))
- HIFLD Electric Power Transmission Lines (archived layer), OpenStreetMap substations (ODbL), U.S. Census places
- Street map: © OpenStreetMap contributors, via [Protomaps](https://protomaps.com/); optional Google Maps view by Google
