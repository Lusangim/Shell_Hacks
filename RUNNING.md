# Running GridLock

GridLock runs on your own laptop: a small local server plus a web page at http://127.0.0.1:8765.
No account is needed. Internet is needed only during setup (and for the optional Google Maps view).
It works on **Windows, macOS and Linux** with the same two clicks: **SETUP** once, then **START**.

## What you need

- **Python 3.12**
  - Windows: [python.org](https://www.python.org/downloads/) (keep "py launcher" ticked in the installer)
  - macOS: [python.org](https://www.python.org/downloads/) or `brew install python@3.12`
  - Linux: `sudo apt install python3.12 python3.12-venv` (Ubuntu 24.04 and newer), or your distribution's
    Python 3.12 packages
- **Git** from [git-scm.com](https://git-scm.com/) (already on most Macs and Linux machines)
- About **1 GB** of free disk space (packages plus the 220 MB street map)

## Run it in 4 steps

1. Get the code (in a terminal or Command Prompt):
   ```
   git clone https://github.com/Lusangim/Shell_Hacks.git
   ```
2. **Set up, once.** Open the `Shell_Hacks` folder and:

   | Windows | macOS | Linux |
   |---|---|---|
   | double-click **`SETUP.cmd`** | double-click **`SETUP.command`** | double-click **`SETUP.sh`** ("Run as a program"), or run `./SETUP.sh` |

   It creates the Python environment in your home folder (`dev/gridlock-venv`), installs the pinned
   packages, and downloads the modern street map of Georgia and South Carolina (about 220 MB, only once).
   Wait for `SETUP PASS`.
3. **Start.**

   | Windows | macOS | Linux |
   |---|---|---|
   | double-click **`START.cmd`** | double-click **`START.command`** | double-click **`START.sh`**, or run `./START.sh` |

   Your browser opens http://127.0.0.1:8765. To stop GridLock, close that window (or press Ctrl+C in it).
4. Click **Take the tour** for a guided walkthrough of the demo.

**macOS, first time:** if macOS says the file "cannot be opened", Control-click it, choose **Open**, then
**Open** again. If you downloaded a ZIP instead of using `git clone`, run `bash SETUP.command` and
`bash START.command` in Terminal from the `Shell_Hacks` folder.

**Linux:** if double-clicking opens the script as text, right-click it and choose **Run as a Program**, or
run it from a terminal.

## Optional

### Google Maps and Satellite view

1. In [Google Cloud](https://console.cloud.google.com/), enable **Maps JavaScript API** and create an API key.
   Restrict it: *Websites* `http://127.0.0.1:8765/*` and `http://localhost:8765/*`; *APIs* Maps JavaScript API
   only. Billing must be enabled on the project; normal use stays inside Google's free monthly limit.
2. Save the key, alone on one line, as `dev/gridlock-assets/google-maps-key.txt` in your home folder
   (Windows: `%USERPROFILE%\dev\gridlock-assets\google-maps-key.txt`). Never commit it or paste it into a chat.
3. Start with Google switched on:

   | Windows (Command Prompt in the folder) | macOS / Linux (terminal in the folder) |
   |---|---|
   | `START.cmd -Google` | `./START.sh --google` |

   A **Map / Google Maps / Satellite** switch appears while you are online.

### Rebuild the data from the source PDFs

The built map data is already in the repo. To rebuild it yourself, in the `Shell_Hacks` folder:

| Windows | macOS / Linux |
|---|---|
| `%USERPROFILE%\dev\gridlock-venv\Scripts\python.exe -m pipeline.extract` | `~/dev/gridlock-venv/bin/python -m pipeline.extract` |
| `%USERPROFILE%\dev\gridlock-venv\Scripts\python.exe -m pipeline.build_all` | `~/dev/gridlock-venv/bin/python -m pipeline.build_all` |

`pipeline.extract` reads the two plan PDFs in `data/raw/` (54 Dominion Energy SC projects, 427 SERTP rows).
`pipeline.build_all` places the projects on the map and finds the pairs (230 kept, 181 placed, 489 pairs,
43 across the state line). The rebuilt files match the committed ones exactly.

### Run the automated checks

| Windows | macOS / Linux |
|---|---|
| `SETUP.cmd -Tests`, then `VERIFY.cmd` | `./SETUP.sh --tests`, then `~/dev/gridlock-venv/bin/python -m pytest` |

The test option installs the Chromium browser the checks use (about 700 MB on disk).

### Get the street map again

Windows: `GET-MAP.cmd -force`. macOS / Linux: `~/dev/gridlock-venv/bin/python scripts/get_map.py --force`.
Without the map file, GridLock still runs with a plain outline map.

## Troubleshooting

- **"Port 8765 is already in use"**: another GridLock is already running; close it, or start on another port
  (`START.cmd -Port 8766` / `./START.sh --port 8766`). Google Maps only works on port 8765.
- **A plain grey outline map instead of streets**: the street map file is missing; get it again (above).
- **"Python 3.12 is required"**: install Python 3.12 (see "What you need"), then run SETUP again.

The macOS and Linux scripts were tested with Bash on Windows (Git Bash); they have not yet been run on a
real Mac or Linux machine. If a step fails there, the error message says what to install.

## Where things are

- `pipeline/`: reads the plan PDFs and builds the map data (`extract.py`, `build_all.py`, ...)
- `server/`: the local API
- `web/`: the map page
- `data/raw/`: source documents and public inputs; `data/build/`: the generated map data
- `tests/`: automated checks
- `scripts/`: setup, start, verify and map-download scripts (`.ps1` for Windows, `.sh` for macOS / Linux)

## Data and credits

- Dominion Energy SC: SCRTP planned facilities 2026-2030, $2M and above ([scrtp.com](https://www.scrtp.com/assets/pdfs/home/2026-2030-2million-and-above-project-descriptions.pdf))
- Georgia Power, Georgia Transmission and MEAG: SERTP 2025 Regional Transmission Plan ([southeasternrtp.com](https://www.southeasternrtp.com/docs/general/2025/2025%20Regional%20Transmission%20Plan%20and%20Input%20Assumptions.pdf))
- HIFLD Electric Power Transmission Lines (archived layer), OpenStreetMap substations (ODbL), U.S. Census places
- Street map: © OpenStreetMap contributors, via [Protomaps](https://protomaps.com/); optional Google Maps view by Google
