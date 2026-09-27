# Map as protagonist redesign

Founder brief: apply the supplied three-pane mock throughout GridLock while preserving every feature, data hook, accessible control name and existing logic. Work only on `codex/redesign-astra` in `web-redesign-astra`; no data rebuild, push or deployment. Four milestone commits: shell, pair detail, list/map/tablet, phone/full verification.

Reference: `C:/Users/lucia/dev/gridlock-runs/codex/founder-mock-map-protagonist.webp` (viewed). The explicit 2026-09-27 design supersedes the older yellow-selection and single-panel direction.

Verification: Python from `GRIDLOCK_PY`; port 8779; AI and Google off; installed Playwright browsers. All existing e2e (including the full audit matrix) and API checks remain in scope. Re-run individual failures three times. No tests of live records or external calls.

## Milestone 1, verified 2026-09-27

- New regression failed on the old shell because `.app-bar #search-input` did not exist; passes after the shell move.
- Top bar owns search, Filters dropdown and More disclosure. Existing secondary controls retain their ids and accessible names inside More.
- DOM order is top bar, list, map controls and detail. Desktop pair selection retains the whole list alongside the right pane.
- API plus quick audits: 180 passed, 2 stale search-label failures; repaired label reference and both cases passed three isolated reruns each.
- Full e2e/API run: 539 passed, 37 failed (406 e2e cases including the complete audit matrix; 170 API cases). Every original failed case subsequently passed three isolated reruns after presentation fixes or navigation assertion moves. The first retry batch was 108 passed and 3 failures of one deliberately delayed-shell case; its disabled-Filter keyboard assertion was corrected, then it passed three fresh isolated runs.
- Final shell gate: 39 passed (quick audits, all five new shell regressions, and the T43 focus/provenance suite). Two new focus regressions also passed three isolated runs each. The More-exit and covered-map regressions passed three direct isolated browser invocations each. A later direct browser attempt crossed a test-server teardown; final fixture-owned runs verified both paths.
- Fixed genuine defects exposed by the layout: clipped named status, restored-area layout shift, the tour invitation covering phone basemap buttons, and focus hidden by dropdowns or responsive sheets. Search submission exposes its results from an overlaid detail sheet. All original data, print, copy, tracker and brief checks remain.
- Tests migrated through actual More, filter and back controls; no assertions removed to accommodate a defect. Updated generated focus screenshots reflect the new shell.
- Review support: one agent inspected navigation and migrated test actions. Product code remains root-owned.
- Independent static review identified the remaining Filter Tab-exit and map-project Back focus paths; both received failing regression checks and fixes. No HIGH/CRITICAL findings in that review.
- Lesson, 2026-09-27: moving a control into a disclosure also changes every return-focus path to that control; test those paths explicitly.

## Milestone 2, verified 2026-09-27

- Pair detail now uses the utility title, two project entries, six facts, five native disclosures and an explicit Open brief / Back to pair detail round trip. Existing seven detail blocks and source hooks remain intact; print keeps its original heading and wording.
- The new pair presentation regression failed before implementation, then passed three isolated runs and a fresh visual rerun. Quick audits plus shell/detail regressions: 17 passed.
- Affected feature gate: 154 passed, covering brief, tracker, detail, readable details, demo path, offline, T43, location styling, export, tour, shell and four desktop/phone light/dark full-matrix detail scenes.
- An old phone tour test assumed geometric separation from a now-layered More menu. Its actual click reachability assertion now follows that disclosure; it passed three isolated reruns. A new test exposed the expanded phone list covering the tour timeline, was fixed by collapsing that sheet for the timeline step, and passed three isolated pytest runs (also three direct browser checks).
- Independent review found no blocking M2 issues. Reduced-motion screenshots verified the final detail typography and selected map framing.
- Lesson, 2026-09-27: native disclosures keep evidence accessible with less visual weight, but tours must reveal every ancestor before focusing their target.

## Remaining

- Quiet list, midpoint rank marker, compact timeline and tablet sheet.
- Phone polish, independent review, complete test pass and final handoff.
