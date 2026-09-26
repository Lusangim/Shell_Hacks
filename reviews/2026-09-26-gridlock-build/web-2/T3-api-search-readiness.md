# WEB-2 T3: preserve search flight during hydration

Date: 2026-09-26. Builder base: `5d793e4`. Test port: 8797.

## Task and files

Prevent a late shell `/api/meta` response from replacing an explicit search destination with the initial overview. Repair the keyboard search helper's fixed 12-Tab limit without bypassing keyboard navigation.

- `web/js/search.js`: mark the existing initial-map-fit flag before a validated search result flies to its source coordinates. An explicit destination now takes precedence over the pending overview fit.
- `tests/e2e/test_search.py`: four deterministic delayed-meta search cases and two untouched-overview cases; DOM-size-bounded Tab traversal with visited-element loop detection.
- This report.

## Acceptance and evidence

Every test command set `GRIDLOCK_TEST_PORT=8797`, `GRIDLOCK_AI=off`, and `GRIDLOCK_GOOGLE=off`; Python ran through `$env:GRIDLOCK_PY`. Chromium used the configured Playwright browser path. No network or paid service was used.

### Delayed shell cannot override search

`test_keyboard_search_keeps_source_center_after_delayed_meta` holds the real `/api/meta` route, reaches search by Tab, types Savannah, presses Enter, waits for the exact source center and zoom, releases meta, waits for the shell's final loaded status, then asserts the exact center and zoom again. It covers 1440 and 390 pixels with animated and reduced motion.

RED before product edits: `pytest tests/e2e/test_search.py -k delayed_meta -q` produced `4 failed, 2 passed, 14 deselected in 15.46s`. Two repetitions with `--tb=line` produced the same totals in 14.67s and 14.30s. All four failures occurred at the final coordinate assertion after the late initial fit. Expected `[32.018043, -81.196492, 11]`; desktop latitude became `32.35901998634024` with zoom `7.25`, and mobile latitude became `24.43201235598284` with zoom `5.5`.

GREEN after the two-line product change and helper repair: the complete search suite ran three times: `20 passed in 54.32s`, `20 passed in 52.10s`, `20 passed in 52.74s`.

### Untouched first view fits both states

`test_untouched_first_view_fits_both_states_after_delayed_meta` holds and releases the same meta route without selecting a destination. After shell hydration it asserts the map bounds contain both complete state geometries. Both screen sizes passed on original source and in all three GREEN runs.

### Keyboard helper remains a real keyboard check

The helper sends real Tab keys, fails on a repeated focused element before search, and bounds the walk by the current DOM size. It never clicks or directly focuses search. Every existing assertion remains. All existing keyboard search cases passed in the three focused GREEN runs.

Tour RED is supplied by the lead's assignment, not a run by this builder: the held T1.8 tour gate reported eight search keyboard failures because the tour adds three legitimate controls before search. The lead will sync and rerun the tour branch after this repair is integrated; combined-tour GREEN is not claimed here.

## Lane gate

Pending lead sync to current main before the full lane gate. Focused suite currently has 20 cases: 14 existing and six new. `git diff --check` passed.

## Review, deviations, and open work

The change follows the existing state flag and source-coordinate validation. It changes no API contract, shared map/app code, DOM rendering, motion preference handling, or source fields. Review checklists A/D/E/F/J/K applied to the owned diff; no fixed sleeps, weakened checks, or new dependencies.

Declared deviations: combined-tour verification is coordinated by the lead because tour files are outside this branch's ownership. No other-lane patch is needed. Open work: record full lane gate after main sync and lead's combined-tour result. No product decision is unresolved.

2026-09-26 lesson: Explicit user navigation must claim initialization state before a pending shell continuation can apply its default viewport.
