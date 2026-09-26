# WEB — T1.3 Web shell (builder)

Read first: AGENTS.md, `.agents/skills/gridlock-build/SKILL.md` §0 and §2, `SPEC.md` § Contracts and § Code style, `.agents/skills/gridlock-build/references/definition-of-done.md`, `references/ui-contract.md`, `reviews/2026-09-26-gridlock-build/design/DIRECTION.md`, and review-checklists §D, §E, §F, §J. Read text with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task
Build the T1.3 shell per `tasks/todo.md`: desktop interactive Leaflet SVG map and side panel, 390 px bottom sheet, local basemap, light/dark tokens from DIRECTION, external `theme-init.js` before paint, utility and accuracy styles, ranked overlaps, loading/empty/error states, safe `textContent` with `data-src` for data, DOM-node tooltips, noscript, disclaimer, source edition dates from `/api/meta`. Write `tests/e2e/test_shell.py` proving map features equal placed-project count, list at least 10, zero console errors at 1440/390, malicious data as text in list and tooltip. The API and contracts are under construction; use temporary local fixture data in your owned files for RED/GREEN, then align to the merged fixtures and API as they become available. Do not edit contracts or API files.

## Ownership
Worktree `C:\Users\lucia\dev\gridlock-wt\web`, branch `wt/web`, port 8773. Own `web/` except WEB-2 files named in `tasks/plan.md`, `tests/e2e/test_shell.py`, and report `reviews/2026-09-26-gridlock-build/web/T1.3.md`. Everything else is read-only. Never run a command in `C:\Users\lucia\dev\gridlock`.

## Environment and rules
Every command starts a new shell. Begin every test/server command with `$env:GRIDLOCK_TEST_PORT='8773';`. `GRIDLOCK_AI=off`; Python only as `& $env:GRIDLOCK_PY`; `PLAYWRIGHT_BROWSERS_PATH` is set; no network. Never print environment variables. Test first; never weaken a check. Data strings stay verbatim; unknowns stay null. Stop and report on AGENTS.md hard-rule triggers. Stage by path; never `git add -A`, `git stash`, `git clean`, `git reset --hard`; one commit `WEB: T1.3 build web shell`; never merge, push or touch main.

## Report
Task, files changed, each acceptance line with failing and passing output, suite totals, deviations, exact `For <lane>` patches, open questions, one dated one-line lesson. Save it to the owned report path and include it in your final response. Report only checks you ran.
