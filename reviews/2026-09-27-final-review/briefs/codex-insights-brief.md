# Codex task: "Start here" places and an impact summary (founder request, 2026-09-27)

You are working in a git worktree of GridLock on branch `codex/insights`. It was cut from Claude's integration
branch, which includes the UI pass so far, the savings-in-score work, the score breakdown and the new brief
panel. Build the two features below, commit on this branch and stop. Don't push. Run tests on port 8777
(`GRIDLOCK_TEST_PORT=8777`), never 8765. Set `PLAYWRIGHT_BROWSERS_PATH=%USERPROFILE%\dev\ms-playwright`,
`GRIDLOCK_AI=off` and `GRIDLOCK_GOOGLE=off`.

Standing rules: nothing invented, and every number comes from the build data. Product wording is plain
English with no em or en dashes in our own text, IDs are never shown to users, and all data strings go in
with textContent. The Pydantic contracts use `extra="forbid"` and every contract change regenerates
`contracts/*.schema.json` from `server/export_contracts.exported_schemas()`.

## 1. "Start here": the places where close pairs cluster

New users need a starting point.

- **Data (deterministic, in the pipeline).**
  - Take every pair in the touching, under 1.6 km and under 8 km bands.
  - Place each one at the midpoint of the nearest points between its two project shapes (EPSG:5070, as in
    `pipeline/find_overlaps.py`).
  - Name it after the nearest Census place in the build's places data (the same places the search uses).
  - Group by place and keep places with at least 2 pairs.
  - Sort by pair count (descending), then by best rank (ascending), and keep the top 5.
  - Write them to `data/build/meta.json` as `hotspots: [{label, lat, lon, pairs, best_rank}]`, where label
    is the place name as search shows it, e.g. "Savannah city".
  - Add a `Hotspot` model and the field to the Meta contract, regenerate the schemas, and update the meta
    fixture and its tests.
  - Rebuilds must stay byte-identical.
- **UI.** A new module `web/js/start-here.js` and styles in a new `web/css/insights.css` (linked from
  `web/index.html`).
  - Render a "Start here" row right under the search form: one button per hotspot, such as "Savannah · 6 close
    pairs".
  - Clicking a button centres the map there and opens the existing area explorer around it at 10 km. Reuse
    the controller that `web/js/search.js` creates, through a small exported hook or a
    `gridlock:explore-place` custom event. Don't copy area logic.
  - The buttons need keyboard access, visible focus, 44 px targets on phones and light and dark themes.

## 2. Impact summary for the current results

This is a one-line card in the ranked-list header, computed in the browser from the pairs currently loaded,
so it follows the filters. Put it in a new `web/js/impact.js` with its container in `web/index.html`, and call it
wherever the list is re-rendered after results load; that hook is probably in `web/js/app.js`. Example:

"465 pairs · 43 across the state line · possible savings of $X to $Y across 119 pairs · most pairs: Georgia Power
and Georgia Transmission Corp. (N)"

- Sum `low_usd` and `high_usd` over pairs whose savings status is `range`. Round to the nearest $1,000 and
  format like the rest of the app.
- A disclosure or tooltip on the card says: "Each pair is estimated on its own. Pairs that share a project
  overlap, so this is a screening figure, not a budget."
- "Most pairs" is the utility pair with the most pairs in the current results.
- With zero results, show "No pairs match these filters."

## Tests (write them first)

- Pipeline: the hotspots are deterministic (build twice, compare), each hotspot's `pairs` count is right for
  its place, the list is ordered, there are at most 5, and one of them is in the Savannah area (the top pairs
  are at McIntosh).
- Contract: the new field validates, and a bad hotspot (negative count, missing label) is rejected.
- API: `/api/meta` returns the hotspots.
- e2e (new file `tests/e2e/test_insights.py`):
  - The Start here buttons render from the API data.
  - Clicking the first button opens the area panel with a 10 km radius.
  - The impact line's numbers equal what `/api/overlaps` gives for the same filters, including after
    choosing the touching band.
  - Both features pass axe in light and dark at 1440x900 and 390x844.

Run your new and changed test files, `python -m pytest tests/pipeline tests/api tests/eval -q`, and
`tests/e2e/test_shell.py`.

## Don't touch

Other agents are working in these files, so only add small hooks and say which in your report:
`web/js/brief.js`, `web/js/overlap-detail.js`, `web/js/list.js` (row layout), `web/js/tour-content.js`,
`web/js/map.js`, `web/js/area.js` (a Codex task is adding an area-mode button there), `web/js/export.js`, the
CSV code in `server/app.py`, and the panel layout rules in `web/css/app.css`.

## Done means

All the tests above pass, and there is one commit, `DATA/WEB: Start here places and an impact summary (founder
request)`, on `codex/insights`. Your final message lists the files changed, the tests run with their totals,
and the top five hotspots with their counts.
