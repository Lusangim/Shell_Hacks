# GridLock data pack (built 2026-09-26)

All sources are public. Confirm with Sperry Tech on site that the SERTP overview document is acceptable (see "CEII note").

| File | What it is |
|---|---|
| `desc_scrtp_2026_2030.pdf` | Dominion Energy SC planned transmission projects ≥ $2M, 2026–2030 (SCRTP). Source: https://www.scrtp.com/assets/pdfs/home/2026-2030-2million-and-above-project-descriptions.pdf |
| `desc_2026_2030_projects.csv` | 54 DESC projects parsed: name, ID, description, need, status, planned in-service date, total cost |
| `sertp_2025_rtp.pdf` | SERTP 2025 Regional Transmission Plan & Input Assumptions (Nov 26 2025). Southern BAA (Georgia Power, GTC, MEAG, Savannah area) projects from p.60. Source: https://www.southeasternrtp.com/docs/general/2025/2025%20Regional%20Transmission%20Plan%20and%20Input%20Assumptions.pdf |
| `sertp_2025_projects.csv` | 427 SERTP projects parsed (326 in the SOUTHERN area): area, in-service year, name, description, need, page |
| `extract.py` | The parser that made both CSVs (re-run it if the PDFs are updated) |

## Pipeline (run in order)
```
python extract.py          # PDFs -> desc_2026_2030_projects.csv, sertp_2025_projects.csv
python fetch_hifld.py      # HIFLD lines for GA/SC -> hifld_lines_ga_sc.geojson
python place_projects.py   # -> projects.geojson + placement_report.csv
python find_overlaps.py    # -> overlaps.json (ranked)
```
Other inputs: `osm_substations_sc_ga.json` (OpenStreetMap), `places_se.csv` (Census places, also for city search), `us_states.geojson`, `manual_locations.csv` (hand fixes; a note starting with INFERRED keeps the project "approximate").

Status 2026-09-26 01:30: 230 GA/SC projects kept, 181 placed (42 exact, 139 approximate), 49 unknown. 477 pairs within 40 km; 44 cross-state. #1 = Okatie–McIntosh tie vs McIntosh 230 kV relay upgrades (touching, both 2028).
**To verify by hand:** Okatie location (inferred from HIFLD tap on the Jasper–Yemassee line). Augusta area is under-placed: only 3 cross-state pairs there.

## What's missing: coordinates
Neither plan has lat/lon. Each project is named by its endpoint **substations** (e.g. "Jasper – Okatie 230 kV"). To map them:
1. Get substation points from **OpenStreetMap** (Overpass: `node/way["power"="substation"]` in SC/GA, match on `name`) and/or **HIFLD Substations**. HIFLD transmission lines are on data.gov: https://catalog.data.gov/dataset/electric-power-transmission-lines
2. A line project = the segment between its two substations. For "closest points", use the existing HIFLD/OSM line geometry between those endpoints when there is one; otherwise draw a straight line (the challenge accepts that approximation).
3. Substation-only projects = a point.
4. Compute the minimum distance between each DESC and GPC geometry pair (GeoPandas/Shapely in a projected CRS such as EPSG:5070). Buckets: touching, < 1.6 km, < 8 km, < 40 km. Add timeline overlap by comparing in-service years.

## Strong candidate overlaps already visible in the text
- **DESC #41 "Okatie – McIntosh 115 kV Tie: Add Series Reactor"** (2028, $5.4M). This is a literal cross-border tie into Georgia Power's McIntosh. It lines up with GPC 2028 McIntosh 230 kV relay upgrades, West McIntosh breaker replacement, Goshen–McIntosh 115 kV rebuild, Rice Hope autotransformer, Calvert–West McIntosh reconductor (2029) and Big Ogeechee 500/230 kV (2026).
- **Savannah cluster:** DESC Jasper–Okatie 230 kV #2 (6.5 mi, Dec 2026), Okatie sub expansion (2026), Yemassee–Ritter (2027) vs GPC "SAV:" projects (Goshen–Kraft, Coleman–Dean Forest, Little Ogeechee, Meldrim, 2026–2035).
- **Augusta cluster:** DESC Urquhart–Toolebeck 115 kV (2026), Urquhart–Aiken 46 kV (2027), Stevens Creek–Graniteville 115 kV (2029), Modoc–McCormick (2029) vs GPC/MEAG Goshen Area Strategic Solution (Waynesboro–Wilson switching station, 2030), Warrenton-area rebuilds (2027–2030), and Thomson–Vogtle 500 kV.

## CEII note
The challenge bans CEII data. The SERTP overview PDF says it "does not include Critical Energy Infrastructure Information (CEII) materials" and is posted publicly, but its page headers say "SERTP TRANSMISSION PROJECTS (CEII)". **Ask Sperry Tech to confirm before you rely on it.** The SCRTP DESC list is plainly public. Do not use anything from the SERTP "Secure Area" or the SCRTP CEII-NDA.
