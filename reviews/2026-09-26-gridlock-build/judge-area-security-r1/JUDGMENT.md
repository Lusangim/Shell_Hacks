# T3.4b scoped security judgment

Date: 2026-09-26. Independent security judge; frozen HEAD verified as `003d310`. All commands ran in `C:\Users\lucia\dev\gridlock-wt\judge-area-security-r1`. Port 8784; AI and Google off. No product or test code changed.

## Scope and conclusion

Reviewed the `main...003d310` area feature diff in `web/js/area.js`, `web/js/filters.js`, `web/js/search.js`, `web/js/app.js`, `web/index.html`, `web/css/area.css`, and `tests/e2e/test_area.py`. Read `server/area.py`, the Area/Center schema, and the area route's numeric validation to trace the boundary. Reviewed map/search entry, restored coordinates and radius, history/filter/year interaction, text and link rendering, request cancellation, stale responses, error/retry, and Escape.

No reproduced or line-cited P0, P1, P2, or P3 security findings in this scope. No owning-lane security fix required.

This is not a full application audit. Existing source-file route handling, CSV exports, generation/CSRF/spending guards, prompt injection, other application renderers, historical secrets, and production deployment were not re-audited. No credentials, environment-variable values, or `debug.log` were inspected. No third-party service was contacted.

## Verification actually run

Common settings for every runtime command: `GRIDLOCK_TEST_PORT=8784`, `GRIDLOCK_AI=off`, `GRIDLOCK_GOOGLE=off`, `PYTHONDONTWRITEBYTECODE=1`, `PLAYWRIGHT_BROWSERS_PATH=C:\Users\lucia\dev\ms-playwright`. Python was invoked only through `$env:GRIDLOCK_PY`.

Command:

```powershell
& $env:GRIDLOCK_PY -m pytest -q -p no:cacheprovider tests/e2e/test_area.py tests/e2e/test_search.py::test_malicious_search_label_is_text_only
```

Result: **14 passed in 61.94s**. This includes the four desktop/phone and light/dark offline checks, map entry, reload and Back/Forward with filters/year, 422/503 retry binding, three deliberately late-response paths, delayed shell initialization, untrusted utility labels, and malicious search labels. The race tests deliberately return a response after cancellation, exercising the sequence guard independently of successful abort.

An additional read-only Python/Playwright stdin probe used the existing `live_server` fixture and one Chromium page, with all browser requests outside the exact local server prefix aborted and recorded. No probe file was added. Inputs and assertions:

1. Fulfilled `/api/area` with one project and one overlap. Used `<img src=x onerror="window.injected=true">` as the project name, utility, accuracy, source document, band label, and count keys. Source URL was `javascript:alert(1)`; overlap ID was `javascript:alert(1)//../../` followed by that image string. Asserted exact name/citation text, no image element, no `window.injected`, and an href exactly equal to `#overlap=` plus the encoded ID. Clicking the overlap link kept navigation on the local origin. The source URL did not become an active link.
2. Loaded nine malformed URLs: `area=NaN,-81`; `area=Infinity,-81`; `area=91,-81`; `area=32,181`; `area=32,-81,1`; and valid `area=32,-81` with radius `0`, `81`, `Infinity`, or the encoded image string. After shell load, every case had a hidden area panel and made **zero area requests**.
3. Requested eight API boundary cases: latitude `NaN`, `Infinity`, `91`, or the image string; longitude `181`; radius `0`, `81`, or `Infinity`. Other coordinates were `32,-81`. Every response had status **422** and a JSON `error` object.

Probe output:

```text
PASS: 1 composite source/link injection; 9 malformed URL restore cases; 8 API boundary cases; 0 page errors; 0 external requests.
```

Both test/probe processes exited 0. The fixture and browser were closed through their cleanup paths. A final local socket check passed: no listener remains on port 8784. `git status --short` showed only the lead-provided untracked brief and this judgment folder; tracked files were unchanged.

## Sound controls

- `web/js/area.js:9` uses `textContent` for result fields and counts; `:43` fixes the overlap destination to a fragment and encodes its ID. Public-plan strings do not become HTML, scripts, or external links in this surface.
- `web/js/search.js:4` accepts only finite, bounded coordinates from search results. `web/js/area.js:150` validates restored coordinate syntax/bounds and finite radius bounds before drawing/requesting. `server/app.py:348` independently bounds latitude, longitude and radius and rejects non-finite values. Map entry and slider state cannot bypass that server boundary.
- `web/js/area.js:107` aborts the preceding request and increments its sequence; `:119` and `:128` discard stale success and failure paths. Clearing at `:69` also advances the sequence, so a completed older request cannot reopen cleared results.
- `web/js/area.js:115` constructs an encoded query on the fixed relative `/api/area` route. Its catch path uses a fixed recovery message rather than rendering server exception text. Retry loads the currently selected center.
- `web/js/filters.js:90` and `:211` manipulate a URL derived from the current local URL and preserve the area/radius state across filter and year writes. Existing tests verify history restoration and that clearing the area persists through later filter/year changes.
- `web/index.html:123` explicitly states the unknown-location limitation and that area totals cover all loaded plans independently of filters/year, reducing misleading interpretation of the unfiltered area endpoint.

2026-09-26 lesson: Exercise stale responses with an intentionally ineffective abort, and inject source fields and fragment IDs together to verify the entire new rendering boundary.

material improvement still available: no
