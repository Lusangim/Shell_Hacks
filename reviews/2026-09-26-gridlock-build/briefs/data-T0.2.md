# DATA — T0.2 Restructure into packages (builder)

Read first: AGENTS.md, `.agents/skills/gridlock-build/SKILL.md` §0 and §2, `SPEC.md` § Contracts and § Code style, `.agents/skills/gridlock-build/references/definition-of-done.md`, and review-checklists §B, §C, §E. Read text with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task
Restructure with `git mv` into `pipeline/`, `data/raw/`, `data/manual/`, `data/build/`. `& $env:GRIDLOCK_PY -m pipeline.build_all` runs offline (`--refresh` only for downloads). Stage counts reconcile in `meta.json`: every source row is kept, dropped with a reason, or the build fails. Keep counts 230 kept, 181 placed, 477 overlaps, 44 cross-state and the same top 10 pairs unless a legitimate change has a before/after table for lead approval. Remove v0 `preview.html` and `build_preview.py`; preserve the `gridlock-data/README.md` correction. Write `tests/pipeline/test_rebuild_regression.py`; prove RED then GREEN and two rebuilds byte-identical.

## Ownership
Worktree `C:\Users\lucia\dev\gridlock-wt\data`, branch `wt/data`, port 8771. Own `gridlock-data/` for moves and its README, `pipeline/`, `data/`, `tests/pipeline/test_rebuild_regression.py`, and your report `reviews/2026-09-26-gridlock-build/data/T0.2.md`. Everything else is read-only. Never run a command in `C:\Users\lucia\dev\gridlock`. Read git-ignored inputs in the main copy only if needed and by absolute path.

## Environment and rules
Every command starts a new shell. Begin every test/server command with `$env:GRIDLOCK_TEST_PORT='8771';`. `GRIDLOCK_AI=off`; Python only as `& $env:GRIDLOCK_PY`; `PLAYWRIGHT_BROWSERS_PATH` is set; no network. Never print environment variables. Test first; never weaken a check. Unknown values stay null and data strings verbatim. Stop and report on AGENTS.md hard-rule triggers. Stage by path; never `git add -A`, `git stash`, `git clean`, `git reset --hard`; one commit `DATA: T0.2 restructure packages`; never merge, push or touch main.

## Report
Task, files changed, each acceptance line with failing and passing output, suite totals, deviations, exact `For <lane>` patches, open questions, one dated one-line lesson. Save it to the owned report path and include it in your final response. Report only checks you ran.
