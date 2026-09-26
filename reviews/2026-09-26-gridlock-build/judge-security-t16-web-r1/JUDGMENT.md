# T1.6 browser map security judgment, round 1

Reviewed 2026-09-26 11:58–12:01 EDT on frozen commit `a36e7cfe3f2c796441e76dbfe83d7ffc53861481`, port 8789. Independent reviewer; no product or test edits.

Scope: `web/js/basemap.js`, the changed map rendering and styling, their callers and focused browser checks, the local vendor loaders/licenses, and compatibility with `server/map_assets.py`'s config/CSP boundary. The API Range/config implementation had a separate review. This review includes live Chromium with local responses and fake Google objects, plus source inspection. It does not claim live Google service compatibility or a full gate. The compact-phone print CSS correction after this frozen commit is outside this judgment.

## Findings

P0: 0 · P1: 0 · P2: 1 · P3: 0.

### T16-WEB-SEC-01 — P2: the first selection cancels a newer Google selection

Location: `web/js/basemap.js:110–112`, with the shared promise awaited at line 122 and fallback at lines 136–138.

Trigger: hold the first local GoogleMutant response, click **Google Maps**, click **Satellite**, then release a successful plugin response with a working fake Maps API. The cached `model.googleReady` promise captures the first call's `ownRequest`. The second click increments `model.request`, so line 112 rejects shared initialization even though the current selection still needs that initialization. The newer selection then catches that rejection and returns to offline.

Observed in a local Chromium probe: the final status was `Google map unavailable. Showing offline map.`, with zero page errors and zero external requests. A second explicit Satellite click succeeded and displayed `Satellite map`. This is a selection/failure-handling weakness, not an injection or key-exposure finding. Rapid changes while the plugin is loading report a false service failure and require a retry.

Fix: separate shared loader readiness from selection freshness. Before starting the external API loader, check whether the current desired selection still needs Google and the browser is online; use each request token to control layer installation and status after readiness. Returning to Map or going offline must still prevent a not-yet-started Google request. An obsolete request must not reject initialization needed by the newest Google selection or reset a newer readiness promise.

Acceptance: with a delayed local plugin, Google Maps → Satellite → successful release ends on Satellite without an error or extra click; Google Maps → Map → successful release stays offline and makes no Google API request; stale completion/failure cannot alter a newer selection. Use local stubs and fake keys only. Add these cases to the canonical browser suite.

## Checks performed

- Canonical command: `pytest tests/e2e/test_modern_map.py -k 'real_api or missing_archive or google' -q --tb=short`: **5 passed, 7 deselected in 8.70s**. This covered two real local config/Range integrations, default missing-archive behavior, lazy plugin failure, and fake roadmap/satellite/offline switching. No test assertion was changed.
- The delayed-plugin probe above reproduced T16-WEB-SEC-01 and verified a retry succeeds.
- A separate local probe intercepted the API script at DOM insertion, before any network operation. A synthetic key containing query/fragment delimiters remained one encoded `key` parameter on the fixed `maps.googleapis.com/maps/api/js` URL. The only parameter names were `key`, `v`, and `loading`; the URL had no fragment. No synthetic key appeared in page URL or local/session storage. Before the explicit click there was no API script insertion. The probe recorded only boundary results, not a real credential.
- The same probe called `gm_authFailure()` and observed the visible offline failure status and offline selection. It rendered an HTML-like state name and verified the literal text, with no inserted image element.
- Browser routes blocked every nonlocal request; the probe request lists contained only the assigned loopback origin. All commands set AI and Google off. No real key file was opened; no real Google request, download, installation or outbound action occurred. Fixture servers and browsers closed normally.
- `git diff --check` passed. No full quick gate or VERIFY run was performed by this reviewer.

## Boundaries that are implemented well

- Default map configuration and the PMTiles URL are fixed local paths. The Google plugin is loaded only after explicit selection, and absent/disabled config or offline state prevents selection. Failed local scripts and authentication use fixed visible messages, without echoing key or error details.
- The key remains in the in-memory config and the required official API script URL. Authored code does not log it, persist it, or copy it into application URL state. `URL.searchParams.set` prevents key text from adding a callback, host, or fragment.
- State/city/project labels use DOM nodes populated by `textContent`; the attribution HTML is a fixed authored constant. The new status messages are fixed strings. No data-driven HTML interpreter was found in the changed map code.
- Offline CSP remains `default-src 'self'`. The optional API loader's fixed host is present in the enabled CSP, which adds explicit Google hosts. The full provider host requirements and real browser-key restrictions remain an unperformed founder-run online check.
- Protomaps receives only the fixed local archive. Its inspected fetch paths use supplied PMTiles/XYZ sources; its optional Sheet loader is unused. No automatic remote bootstrap/update was found. The supplied BSD 3-clause license is retained in `web/vendor/protomaps-leaflet/LICENSE.txt`.
- GoogleMutant initialization registers a Leaflet factory and does not load the Maps API script itself. Its Beerware notice and embedded LRU MIT notice remain in the bundle. Google logo/attribution nodes are moved into Leaflet control corners by the vendor's `_setupAttribution`; authored CSS does not hide those nodes. OSM/Protomaps attribution is added independently of tile success. Real Google attribution rendering was not exercised against the live service.

material improvement still available: yes
