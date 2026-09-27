# Third-party notices

GridLock's own code and documentation are under the [MIT License](LICENSE). The libraries, source
documents and map data below keep their own terms.

## Libraries in this repository

| Component | Where | Licence |
| --- | --- | --- |
| Leaflet 1.9.4 | `web/vendor/leaflet/` | BSD 2-Clause, © 2010-2023 Volodymyr Agafonkin, © 2010-2011 CloudMade ([LICENSE](web/vendor/leaflet/LICENSE)) |
| protomaps-leaflet 5.1.0 | `web/vendor/protomaps-leaflet/` | BSD 3-Clause, © 2021-2024 Protomaps LLC ([LICENSE.txt](web/vendor/protomaps-leaflet/LICENSE.txt)) |
| Leaflet.GridLayer.GoogleMutant 0.16.0 | `web/vendor/googlemutant/` | Beerware licence, with MIT-licensed js-lru by Rasmus Andersson (notices in the file header) |
| Tabler Icons | `web/icons/` | MIT, © 2020-2026 Paweł Kuna ([LICENSE](web/icons/LICENSE)) |
| axe-core 4.13.0 (tests only) | `tests/e2e/vendor/` | MPL-2.0 ([licence](tests/e2e/vendor/axe-core-LICENSE.txt)) |

Python packages are installed by SETUP from PyPI and are not committed. They are pinned in
[`requirements.txt`](requirements.txt): FastAPI, Starlette, uvicorn, Pydantic, Shapely, pyproj, pypdf, pytest, httpx,
Playwright and the Anthropic SDK (MIT, BSD or Apache 2.0 licences).

## Source documents in `data/raw/`

These public documents are included so every citation in the app can be checked. They belong to their
publishers.

- SCRTP Planned Facilities 2026-2030, $2M and above (Dominion Energy South Carolina), from
  [scrtp.com](https://www.scrtp.com/assets/pdfs/home/2026-2030-2million-and-above-project-descriptions.pdf).
- SERTP 2025 Regional Transmission Plan and Input Assumptions (November 26, 2025), from
  [southeasternrtp.com](https://www.southeasternrtp.com/docs/general/2025/2025%20Regional%20Transmission%20Plan%20and%20Input%20Assumptions.pdf).
  Some of its page headers read "(CEII)"; see the README.
- Dominion Energy's Jasper-Okatie route options aerial map (`data/raw/reference/`), used only as a reference
  for the hand-placed Okatie point.

## Map data

- HIFLD Electric Power Transmission Lines (an archived copy; HIFLD Open was retired in August 2025).
- OpenStreetMap substations and the offline street map: © OpenStreetMap contributors, under the
  [Open Database License](https://opendatacommons.org/licenses/odbl/). The street map archive is built with
  [Protomaps](https://protomaps.com/); SETUP downloads it and it is not in git.
- U.S. Census Bureau places and state outlines (public domain).
- The optional Google Maps and Satellite views are provided by Google under Google's terms and use the
  runner's own API key.

The team's unit-cost file (`data/manual/unit_costs_2026.csv`) cites its public price sources in
[`data/manual/unit_costs_2026.md`](data/manual/unit_costs_2026.md).
