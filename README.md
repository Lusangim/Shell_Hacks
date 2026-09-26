# GridLock — ShellHacks 2026 (Sperry Tech challenge)

Finds where neighboring electric utilities' **planned** transmission projects overlap in place and time, so they can share crews, equipment, land and permits.
Scope: Georgia + South Carolina, focused on the SC–GA border (Dominion Energy SC vs Georgia Power / GTC / MEAG).

- `gridlock-data/` — data pipeline, source documents and outputs. See [gridlock-data/README.md](gridlock-data/README.md).
- `gridlock-data/preview.html` — quick preview map (open in a browser).

## Run
```
cd gridlock-data
pip install pypdf shapely pyproj
python extract.py && python fetch_hifld.py && python place_projects.py && python find_overlaps.py && python build_preview.py
```

## Data sources (all public)
- Dominion Energy SC planned transmission projects 2026–2030 ≥ $2M — SCRTP (scrtp.com)
- SERTP 2025 Regional Transmission Plan & Input Assumptions (southeasternrtp.com) — states it contains no CEII
- HIFLD Electric Power Transmission Lines (U.S. DHS, via ArcGIS)
- OpenStreetMap substations © OpenStreetMap contributors, ODbL
- U.S. Census Gazetteer places; US state boundaries (PublicaMundi)
