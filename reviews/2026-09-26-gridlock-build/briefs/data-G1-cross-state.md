# DATA — G1 repair: cross-state truth (sub-agent of Codex lead; gpt-6-sol, reasoning high)

Read first in this order: repo `AGENTS.md`; `.agents/skills/gridlock-build/SKILL.md` §0 and §2; `SPEC.md` Contracts, Overlap rules and Code style; `references/definition-of-done.md`; `reviews/2026-09-26-gridlock-build/house-patterns.md`; `references/review-checklists.md` §A/B/C/E; `reviews/2026-09-26-gridlock-build/judge-python-g1-r1/JUDGMENT.md`. Nothing else unless a dependency calls for it. Read text with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task

Close the G1 Python review's HIGH finding: `pipeline/find_overlaps.py` currently infers `cross_state` from the presence of Dominion Energy SC. The real pair `desc-p26__sertp-p150-ef263c` is Georgia/Georgia, yet gets `cross_state=true` and the 1.5 score multiplier. Derive cross-state from the two source-backed project state fields. Rebuild the affected artifacts. Recompute and record the before/after cross-state count, rank and top-ten effects without protecting an incorrect old count. Preserve source-row and placement counts. Do not edit frozen contracts. Do not tackle the judge's MEDIUM atomic multi-file publication finding in this repair; the lead records it for later.

## Verify

Write `tests/pipeline/test_cross_state.py` first with the real Georgia/Georgia pair, a genuine differing-state pair, score multiplier and pair-note consequences, and all built pairs checking flag against project states. Run it RED before code. Correct the implementation and run it GREEN; update exact-count/top-ten regression checks only for verified changes. Run affected pipeline tests and `scripts/quick-gate.ps1`. Report the concrete red and green output, counts and rank effects. Do not weaken, skip or delete checks.

## Ownership and environment

Worktree `C:\Users\lucia\dev\gridlock-wt\data-g1`, branch `wt/data-g1`, from the G1 main tree. **Run every command inside this worktree, never in `C:\Users\lucia\dev\gridlock`.** You own `pipeline/find_overlaps.py`, `data/build/overlaps.json`, `data/build/meta.json`, `tests/pipeline/test_cross_state.py`, affected exact-value checks in `tests/pipeline/test_build_extras.py` and `tests/pipeline/test_rebuild_regression.py`, and your report `reviews/2026-09-26-gridlock-build/data/G1-cross-state.md`. Every other file is read-only; especially `server/schemas.py`, `contracts/`, `SPEC.md` and the separate `wt/data` T2.1 branch. `GRIDLOCK_AI=off`; no network, download, install or secrets. Python only `& $env:GRIDLOCK_PY`; every command starts a new shell, so begin every test/server command with `$env:GRIDLOCK_TEST_PORT='8777';`. Stage by explicit path. Never `git add -A`, `git stash`, `git clean` or `git reset --hard`; never print environment variables. No merge, push, deploy, submit or sending.

Stop and report if a fix adds errors, the same error survives three attempts, you need another lane's file or a contract/architecture decision, or a dependency is missing. One commit `DATA: G1 correct cross-state scoring`. Final message and report: task, files, each acceptance line with red/green check, suite totals, deviations, For DATA patches, open questions and one dated one-line lesson. Report only what you ran.
