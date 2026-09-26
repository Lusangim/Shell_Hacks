# G3 reliability and security judgment

Lead archive note: this main-copy report retains the two essential screenshots. Other screenshots and the independent probe scripts were inspected by the judge but were not retained in the archive.

Independent T4.1 judge, 2026-09-26. Frozen copy: `C:\Users\lucia\dev\gridlock-wt\judge-reliability-r1`. Initial and final HEAD: `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc`. Assigned loopback port: 8783. No product changes or commit.

## Verdict and scores

**One verified P2 reliability defect; no verified security defects.** P0: 0, P1: 0, P2: 1, P3: 0. The phone search error and empty states need a small WEB correction.

- Reliability: **7/10**, anchored to a solid implementation rather than the professional 8: normal journeys, races, malformed input, reload and restart work, but a common phone search failure has no visible or accessible feedback.
- Security: **8/10**, professional for this local, offline scope: multiple independent boundaries held under the exercised hostile inputs. This score does not certify untested live Google or Claude integrations or public distribution.

Mode achieved: **live Chromium browser, API probes, screenshots and source review**. First impression: the app loads into a populated map and ranked list with 489 opportunities, visible edition/uncertainty context on desktop and clear phone expand controls. Measured widths were 390, 768 and 1440 pixels; the targeted defect was reproduced at 390 x 844. General walkthrough height was 900.

Sources read: assigned brief; GridLock skill sections 0/7; judge and security role files; CLAUDE; SPEC contracts, overlap rules, code style and boundaries; PROJECT-PROFILE reliability/security lenses; G3 tracker and delivery; UI contract, definition of done, house patterns and review checklists A/H; AI brief guards; relevant server, browser and generator code and callers/tests. The workflow vault router was read only.

## Verified defect

### JREL-01 — P2: collapsed phone search hides every result/error message

**Location:** `web/css/app.css:230` sets `.panel:not(.expanded) .search-state` to `display: none` at phone widths. The input remains visible and usable. `web/js/search.js:30` writes all feedback into that hidden element; callers include line 56 (searching), line 81 (results/no results) and line 85 (failure). `web/index.html:113` assigns the same hidden element `role="status"`. There is no equivalent update to the visible global status on either tested path.

**Trigger and evidence:** open the default app at 390 x 844, keep the sheet collapsed, then:

1. Enter `zzzz-no-such-place`. The response is an empty result list. `#search-state` contains `No local matches`, but computed display is `none`, Playwright `is_visible()` is false, and the message is absent from visible body text.
2. Route `/api/search?*` to a local synthetic 503 response, then enter `Savannah`. `#search-state` contains `Search unavailable. Check the local server and try again.`, but the same visibility checks fail.
3. In both cases the visible `#status` stays **489 ranked opportunities loaded.** The existing ranked list remains unchanged. Expanding the sheet exposes the same error text, confirming the response handler worked and CSS hid the result.

Screenshots: [empty search, 390 x 844](JREL-01-empty-390x844.png) and [503 search, 390 x 844](JREL-01-503-390x844.png). The independent reproduction is [mobile_search_repro.py](mobile_search_repro.py); it printed both verified hidden states and the expanded control. This is a state visibility defect, not a preference about compact layout.

**Impact:** phone users cannot distinguish no matching place, an in-progress search, or a broken local service. `display:none` also removes the live status from the accessibility tree. Existing checks that assert only `to_contain_text` pass despite this defect.

**Correction, WEB owner:** retain visible search feedback while the search is active in the collapsed sheet, or place the active search message in another visible live status region. Preserve the useful initial phone map and two-row layout; there is no need to expose all introductory help permanently.

**Acceptance check:** on a new 390 x 844 page with `aria-expanded=false`, type an unmatched term and assert a visible `No local matches` message without expanding. Inject a local 503, type Savannah, and assert a visible error with recovery guidance and no success status presented as search completion. Hold a response to verify a visible searching state. Restore the endpoint and search Okatie to verify recovery. Use `to_be_visible()` plus the text assertion; verify no overflow and retain the existing map/list and phone target checks. Repeat at 1440 px to protect desktop behavior. No correction was made by this judge.

## What is genuinely good

- **Local recovery works:** missing map settings and a missing PMTiles archive each retain the 489-row list and visibly select the outline fallback. A failed brief disables Copy, displays Retry, and returns to a labelled Template after recovery. See `map-config-unavailable.png`, `archive-unavailable.png`, and `brief-unavailable.png`.
- **State survives real use:** search to Savannah, area selection, area reload, direct pair links, rapid distance-band changes, Back/Forward and filtered reload passed. At 390/768/1440, 510-character, script-tag and non-Latin searches did not execute script or overflow the page. This includes the hidden-phone-message exception above.
- **Service interruption remains recoverable:** stopping the owned server produced a visible desktop search failure while the loaded map/list remained intact; restarting it recovered search and a full reload. See `server-stopped.png`.
- **Security boundaries compose correctly:** bad Host returned 400; cross-origin map configuration and missing/foreign brief headers returned 403; correctly formed local generation requests returned 409 with AI off. Traversal attempts against source PDFs, briefs and static assets returned 404 with structured errors. The actual offline page returned `Content-Security-Policy: default-src 'self'`.
- **Data has safe destinations:** reviewed plan labels, search results, brief prose and tooltip builders use text nodes/`textContent`. Citation URLs are selected from a fixed document whitelist. Formula/control prefixes are escaped in CSV; brief IDs are validated before cache file construction; malformed/stale caches fall back; atomic cache publication and fake-client spending/concurrency guards passed.
- **Prompt-input containment has executable evidence:** the fixture description cannot close the structured-input block, synthetic instruction output is rejected by the grader, and the current production brief client returns no real client. No model or external service was called.

## Checks and limitations

All test/server commands set `GRIDLOCK_TEST_PORT=8783`, `GRIDLOCK_AI=off`, `GRIDLOCK_GOOGLE=off`; Python was invoked only through `$env:GRIDLOCK_PY`. Chromium used the supplied `PLAYWRIGHT_BROWSERS_PATH`. The server's existing outbound socket guard and the independent walkthrough's browser route guard restricted requests to loopback. Fake clients and fake payloads were used for error/spend checks.

`run_checks.py`: **242 passed in 291.46 seconds**, zero failures/skips. It ran these existing suites:

- API: core, search, detail/export, area, brief routes, brief generator/cache.
- Evaluation: template/grader including hostile description and rejected invented facts.
- Browser: search, filters, brief, area, including the existing race/history/keyboard/error cases.

Pytest temporary evidence was redirected into this judgment folder. `live_probe.py`: **36 independent checks passed** (21 API/header/guard probes; nine viewport journeys; six fallback/retry/link/history/restart checks). The later targeted reproduction independently confirmed JREL-01. The broad pass's text assertions deliberately were not treated as proof of visibility after screenshots exposed the gap.

This was a focused judgment, not a new full VERIFY run. I did not inspect credentials, environment values, `.env`, `debug.log`, or real API keys; did not enable live Google/Claude, run downloads, install packages, send anything or audit git history for release secrets. Actual Google integration and real Claude output quality remain founder-controlled, untested integrations, not verified defects. Source classification/public release and domain correctness remain the other lenses' responsibility. No extra concern or preference is promoted to a finding.

## Cleanup and summary

Browsers and owned server processes were closed. The first immediate post-termination TCP probe briefly still connected; a fresh probe after shutdown completed returned `PORT_8783_LISTENER_ABSENT True`. The targeted reproduction then started and stopped its own server and again returned that result. Final HEAD is unchanged; tracked `git diff --stat` is empty. Git status also reported an untracked `debug.log`; it was not opened or manually edited.

Top five findings: **only JREL-01 is verified; no second through fifth finding.** Evidence folder: `reviews/2026-09-26-gridlock-build/judge-reliability-r1/` in this frozen copy. Correction owner: WEB.

2026-09-26 — A status text assertion must be paired with visibility when responsive CSS can hide the live region.

material improvement still available: yes
