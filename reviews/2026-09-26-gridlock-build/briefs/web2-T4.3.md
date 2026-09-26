# WEB-2 — T4.3 judged tour, search and print corrections

Sub-agent of the Codex lead, most capable model, high reasoning. Work only in `C:\Users\lucia\dev\gridlock-wt\web2-t43` on `wt/web2-t43`, from main `07ae0ac`. One task, one commit: `WEB-2: T4.3 judged tour search and print fixes`. Port 8778.

Read first: AGENTS.md; .agents/skills/gridlock-build/SKILL.md §0/§2; SPEC.md § Contracts/Overlap rules/Code style/Boundaries; definition-of-done.md; house-patterns.md; ui-contract.md; DIRECTION-v2.md; review-checklists §A/§D/§E/§F/§J/§K. Read G3 judgments on main read-only, especially JUD-01/02, JCOPY-02 and JDOMAIN-01, with their screenshots and acceptance checks.

## Acceptance
- JUD-01: first-visit tour invitation must not intersect either zoom control at 390/768/1440 in light/dark. Actual enabled center-pointer zoom clicks must zoom without dismissing the invitation. Preserve dismissal, Projects reachability and the phone two-row/map geometry.
- JUD-02: a fresh-default full tour includes both built `Explore an area` and `Read a coordination brief` steps (8–12 total) with a real, truthful target; area explanation tells the user how to choose a place, brief step reaches the real Template panel. Preserve search/filter state, keyboard Back/Next/Escape, focus return and safe skipping of genuinely unavailable targets/API failures.
- JCOPY-02: duplicate project and place search choices remain distinct/selectable while no internal `desc-p`/`sertp-p` ref appears in native option value/label or filled input. Prefer a truthful readable ordinal when no descriptive disambiguator is available. Keep original ref internally for selection. Replace stale `test_search.py` assertion that requires visible refs with stronger distinct-selection coverage, never weaken the behavior.
- JDOMAIN-01 print-table portion: each inferred utility is qualified in the ranked print report (and any other print-only utility field); stated ownership stays unqualified. The selected-pair print summary belongs to WEB and may be integrated later; do not edit WEB files.

## You own
`web/js/tour.js`, `web/js/tour-content.js`, `web/css/tour.css`, `web/js/search.js`, `web/js/export.js`, `tests/e2e/test_tour.py`, `tests/e2e/test_search.py`, `tests/e2e/test_export.py`, any new `tests/e2e/test_t43_web2.py`, and report `reviews/2026-09-26-gridlock-build/web2-t43/T4.3.md`. Other files read-only, especially WEB's `web/css/app.css`, `web/js/app.js`, `web/js/project-detail.js`, API/server files and frozen schemas/contracts. If another owner is needed, include exact “For WEB/API” patch in your report instead of editing.

## Verification and rules
Write failing browser checks before product edits and show RED/GREEN on real defaults/IDs. Run focused tests and `scripts\quick-gate.ps1` on your branch with each test/server command beginning `$env:GRIDLOCK_TEST_PORT='8778'; $env:GRIDLOCK_AI='off'; $env:GRIDLOCK_GOOGLE='off';`. Python only `& $env:GRIDLOCK_PY`; Playwright path preconfigured. Baseline 674. No network/install/real Google/Claude/key/credential/.env/debug.log access, env prints, 8765, push/deploy/send. Run every command inside this worktree, never main. Read text `Get-Content -Encoding UTF8`; edit repo text via apply_patch. Stage exact owned paths; never `git add -A`, stash, clean or reset-hard. Do not merge/touch main. Park and report if AGENTS stop rule applies, with work committed. Stop your browser/server and report port state.

Final message and saved report: files changed; each acceptance line with before/after check output; focused and quick-gate totals; deviations; “For WEB/API” patches; questions; one dated lesson. Report only checks you ran.
