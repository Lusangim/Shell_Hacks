# GridLock house patterns at G1

These are observed patterns in the walking skeleton. Subsequent builders should preserve them where their feature touches the same surface.

- `web/js/list.js:8` and `web/js/map.js:30`: put public-plan text into DOM nodes with `textContent`; keep `data-src` on quoted data fields so visible product-copy audits can distinguish source text.
- `web/js/app.js:33` and `web/js/app.js:59`: expose loading, success, empty and failure through the existing status and list-state elements; make a failed request visible to the person using the page.
- `web/js/map.js:52` and `web/css/tokens.css:3`: derive map and utility colors from the light/dark token sheet; avoid color literals in feature modules.
- `web/js/map.js:131` and `web/js/list.js:43`: keep the Leaflet SVG map and the ranked list synchronized from the same API records; the list is the complete keyboard path when map vectors are outside Tab order.
- `tests/e2e/test_shell.py:145` and `tests/e2e/audits/test_quick_gate.py:1`: test the real API-backed shell and the browser at desktop and phone widths, including console, accessibility, keyboard, external-request and overflow checks.
- `tests/conftest.py:30` and `tests/harness.py:21`: use the assigned loopback test port and shut down each fixture's server; reject an occupied listener before starting a test server.
- `server/app.py:1` and `pipeline/build_all.py:1`: generate deterministic local artifacts in the pipeline and serve those artifacts through the API; preserve source fields and explicit nulls.

2026-09-26 — The production data and full Tab walk exposed map focus states that the synthetic shell alone did not show.
