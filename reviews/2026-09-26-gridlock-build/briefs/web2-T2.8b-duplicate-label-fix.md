# WEB-2 — T2.8b review correction: identical labels at distinct places (sub-agent of Codex lead; gpt-6-sol, reasoning high)

After your current gate, work only in `C:\Users\lucia\dev\gridlock-wt\web-2-b`, branch `wt/web-2-b`, once the lead syncs this brief. Read repo `AGENTS.md`, `.agents/skills/gridlock-build/SKILL.md` §0/§2, `SPEC.md` Contracts/Code style, `references/definition-of-done.md`, `reviews/2026-09-26-gridlock-build/house-patterns.md`, `references/ui-contract.md`, `reviews/2026-09-26-gridlock-build/design/DIRECTION.md`, `references/review-checklists.md` §A/D/E/F/J/K, and your T2.8b reports. Read with `Get-Content -Encoding UTF8`; edit with apply_patch.

## Reproduced finding

Production `/api/search?q=Bluffton` returns **two** `place` results both labelled `Bluffton town`, one at `(31.519817,-84.869119)` and one at `(32.214449,-80.929528)`. `web/js/search.js` writes both to a `known` Map keyed by `label`, overwriting one, and gives both datalist options the same `value`. The user cannot choose the distinct second place; Enter may center the map on the wrong town. Other production labels also collide at distinct coordinates. Duplicate project labels have distinct refs. The current search gate did not test this.

## Repair and checks

First add a failing `tests/e2e/test_search.py` check against the real Bluffton response: both native datalist choices must be distinguishable and keyboard selection of each must center at the matching source coordinate; selection text should name the chosen result without inventing a state. Check a duplicate project result by ref or a synthetic duplicate type, so a future project-detail hook does not lose identity. A prior query must not leave a selectable stale result when the current query has no match. Show RED. Then make the smallest WEB-2-only change to option display/lookup, using the result's typed `ref` or source coordinates as needed and keeping labels from the API verbatim. Use text nodes/DOM properties, never HTML string injection. Existing Savannah and Okatie keyboard journeys, late-response guard, 390 px layout and no-outbound checks must stay green. Run the new e2e check three consecutive times, then focused shell/audits and full lane `scripts/quick-gate.ps1`. Do not weaken, skip or delete any check.

## Ownership and rules

Own only `web/js/search.js`, `tests/e2e/test_search.py`, and appended `reviews/2026-09-26-gridlock-build/web-2/T2.8b-phone-repair.md` (plus this brief if the lead asks). Other files and lanes are read-only. Every command runs inside your worktree, never main. Every test/server command starts `$env:GRIDLOCK_TEST_PORT='8778';`; Python only `& $env:GRIDLOCK_PY`; `GRIDLOCK_AI=off`; no network, install or secrets. Stage by path; never `git add -A`, `git stash`, `git clean` or `git reset --hard`; never print environment variables. No merge, push, deploy, submit or sending.

Stop/report on a new error, the same error surviving three tries, or a contract/architecture/other-lane need. Commit `WEB-2: T2.8b disambiguate search results`, report RED/GREEN, all totals, deviations, open questions and a dated lesson. Do not merge.
