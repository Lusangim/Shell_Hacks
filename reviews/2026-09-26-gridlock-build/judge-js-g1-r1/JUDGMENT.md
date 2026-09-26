# G1 JavaScript gate review — round 1

Frozen commit: `cf95aa70753c04d594c78796b09ce6486fe4bf1e`

## Findings

No CRITICAL, HIGH, MEDIUM, or LOW findings in the G1 walking skeleton.

The four API reads run together and reject non-OK responses (`web/js/api.js:1-15`); the caller exposes loading, empty and error states (`web/js/app.js:30-60`). Plan strings enter list rows and Leaflet tooltips through DOM nodes and `textContent` (`web/js/list.js:4-9`, `web/js/map.js:24-46,181-185`). On render, prior layer contents are cleared (`web/js/map.js:139-175`), and the current selected pair is restored after a theme change (`web/js/map.js:221-227`). Selection flows from map or list into the shared state (`web/js/app.js:103`, `web/js/list.js:21-41,83-91`). Scripts use local paths and explicit `.js` module imports.

## Tests checked

Read `tests/e2e/test_shell.py` and `tests/e2e/audits/test_quick_gate.py`, `test_default.py`. They cover real API loading, map/list counts, malicious project text in both list and tooltip, selection, accuracy and unknown location handling, phone and desktop keyboard paths, sparse local city labels, theme changes including blocked storage, loading/empty/error display, console and external requests, axe, focus, overflow, and copy/color lint. The lead's G1 VERIFY report is 135 passed, 0 failed or skipped. I ran no tests, as directed by the judge brief.

## Residual risk

The error test verifies that a retry button appears but does not exercise recovery after an endpoint resumes. A later reload after a partially completed render could also leave empty Leaflet layer groups attached to the map, because `clearLayers()` empties them without removing the groups; the present UI has no reload control after success. These are test and future change considerations, not a reproduced G1 defect.

Verdict: ready.

material improvement still available: no

