# T2.6 security judgment

Date: 2026-09-26. Independent reviewer; did not build this change. Frozen HEAD verified as `ef0a435`; reviewed range `969299c..ef0a435`. Mode: source review plus local Chromium runtime checks on port 8784.

## Scope and verdict

Ready from the scoped security lens. Findings: P0 0, P1 0, P2 0, P3 0. No demonstrated security defect in the T2.6 filter and URL-state change.

Inspected the changed web modules, HTML and CSS, committed filter tests, and directly reached project/detail/map rendering, API filtering, error handling, security middleware and test server isolation. Applied review-checklists sections A and E. Checked malformed and duplicate URL parameters, oversized input, hash decoding, safe DOM sinks, request ordering, local request destinations and error exposure.

This is not a repository-wide security certification. Did not rerun the full gate, audit dependencies or git history for secrets, inspect credentials/raw documents, exercise AI generation, or review unrelated export/pipeline security. Existing project/overlap API routes were traced for this change; they were not introduced by T2.6. No product or test code was changed.

## Evidence and strengths

- `web/js/filters.js:55`: URL parsing uses explicit known utility/voltage sets, enum sets, bounded year syntax and finite coordinate ranges. Duplicate scalar keys are discarded; repeated known utilities are deduplicated. Reversed year ranges are cleared. Invalid recognized values get a visible generic warning and are removed with `replaceState` (`:142`, `:177`).
- `web/js/filters.js:21` and `web/js/api.js:16`: only accepted filter keys enter fresh `URLSearchParams`, then fixed local `/api/projects` and `/api/overlaps` paths. User input cannot select the fetch origin or a filesystem path. `writeURL` (`filters.js:91`) starts from the current URL and mutates its search parameters; unknown keys are retained in history but never forwarded by `filterQuery`.
- `web/js/filters.js:159`: utility names and voltage labels use DOM property assignment and `textContent`. The changed unknown-location list uses `field` (`web/js/list.js:5`); citations use an allowlisted document ID and positive integer page (`web/js/project-detail.js:23`). Reached map tooltips pass DOM nodes (`web/js/map.js:24` and `:182`), avoiding HTML interpretation of plan strings.
- `web/js/app.js:106`: each filter request aborts the previous controller and increments a request number. Both success and error paths discard stale results. Projects and overlaps resolve together before rendering. Displayed errors use fixed recovery text, not the thrown request path or server body (`:117`). The committed delayed-request and failed-request/retry tests passed.
- `web/js/app.js:64` catches malformed hash decoding. `web/js/list.js:97` compares IDs as data rather than interpolating them into a CSS selector. Reached overlap detail validates the pair ID before a fixed, encoded local request (`web/js/overlap-detail.js:8`, `:141`, `:148`); malformed/traversal hash probes made no detail request.
- Existing server guards remain in the reached path: localhost host validation and CSP (`server/app.py:283`), generic validation/internal-error responses (`:295`, `:304`), typed filter parameters (`:324`, `:346`), equality/set filtering over loaded artifacts (`:192`, `:212`). Server launch binds 127.0.0.1 (`server/__main__.py`). No new outward action or paid-generation caller appears in the diff.

## Checks actually run

Every test/probe command used `GRIDLOCK_TEST_PORT=8784`, `GRIDLOCK_AI=off`, the installed Playwright browser directory, and Python only through `& $env:GRIDLOCK_PY`. The existing `live_server` fixture checks port availability, starts its own server with the outbound socket guard, and terminates that server in `finally`.

Focused committed tests:

```text
& $env:GRIDLOCK_PY -m pytest tests/e2e/test_filters.py -q -k 'malformed_url or late_filtered_response or filtered_request_error or filter_url_reload'
4 passed, 7 deselected in 15.26s
```

These cover malformed URL fallback (`test_filters.py:127`), stale filtered responses (`:140`), failed filtered requests and retry (`:199`), and URL reload/back/forward with selection outside filters (`:91`). This is the complete pytest total for this review, not the lead's full-gate total.

Six additional read-only browser probes ran through the same server fixture using an inline Python script; no test file was added. Each new page collected page errors and intercepted all requests, aborting any destination outside the assigned local server. All six finished with zero page errors and zero external requests:

| Input | Observed result |
|---|---|
| `?band=touching&band=lt_8km` | Visible invalid-link warning, query cleared, ranked rows available. |
| `utility=` followed by 8,192 `x` characters | Visible invalid-link warning, query cleared, ranked rows available. |
| `?utility=%3Cimg%20src=x%20onerror=alert(1)%3E&year_min=%E0%A4%A` | Visible invalid-link warning, query cleared, ranked rows available; no image node inserted in utility options. |
| `?utility=Georgia+Power&utility=Georgia+Power` | Filtered requests contained exactly one `utility=Georgia Power`; filter completion status appeared. |
| `/#overlap=%E0%A4%A` | Unknown-overlap message; no `/api/overlaps/` detail request. |
| `/#overlap=..%2F..%2F` | Unknown-overlap message; no `/api/overlaps/` detail request. |

Browsers were closed and both fixture server lifetimes ended through their cleanup paths. Final git status also showed an untracked `debug.log` created during runtime checks; it was not inspected or staged. Only this report was committed.

## Coverage limits

The committed filter tests do not permanently encode every duplicate/oversized/HTML case above; retaining those probes as regressions would be useful future coverage, not a demonstrated defect. There is no explicit overall query-length cap in the browser parser. The 8,192-character invalid value recovered correctly; arbitrary huge URLs and browser resource exhaustion were not stress-tested, so no denial-of-service claim is made. Reserved `year`/`area` values are validated and preserved here; their future feature consumers were not assessed.

2026-09-26 lesson: fresh allowlisted query construction, DOM text sinks and request-generation checks make URL-state security traceable without repeating the full gate.

material improvement still available: no
