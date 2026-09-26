# DATA — T0.3b Stable IDs and real pages (builder)

Read first: AGENTS.md, `.agents/skills/gridlock-build/SKILL.md` §0 and §2, SPEC.md § Contracts and § Code style, `.agents/skills/gridlock-build/references/definition-of-done.md`, and review-checklists §B, §C, §E. Read text with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task
Implement T0.3b after T0.2 and T0.3a: DESC IDs `desc-p<N>` where N is the source PDF page; SERTP IDs `sertp-p<page>-<hash6 of normalized name + description>`, with `-2`, `-3` in source-document order on collisions. Keep `source.page` the real PDF page and a source doc/url. Preserve names and descriptions verbatim. Every generated project/overlap artifact must validate against the committed `server/schemas.py` and `contracts/`; update the stage meta to its contract shape with honest nulls (T1.5 adds full extras later). Preserve row counts and top-10 ranking unless a source-cited correction needs a before/after table for lead approval. Do not edit `server/schemas.py` or `contracts/`; report an exact `For LEAD` patch if needed.

Write `tests/pipeline/test_ids.py`: IDs unique across all rows and identical over two builds; every project source page contains its name or printed project ID (normalize whitespace and punctuation only, no fictional match); artifacts validate. Prove RED then GREEN. Note that SERTP p.133 lists one project twice, and DESC printed `project_id` can repeat; do not use printed ID as unique row ID.

## Ownership
Worktree `C:\Users\lucia\dev\gridlock-wt\data`, branch `wt/data`, port 8771. Own `pipeline/` except `briefs.py`, `data/build/`, `data/manual/` except contacts, `tests/pipeline/` except `test_contracts.py` and `test_rebuild_regression.py` (you may add `test_ids.py`), and report `reviews/2026-09-26-gridlock-build/data/T0.3b.md`. Everything else is read-only. Never run a command in `C:\Users\lucia\dev\gridlock`. PDF inputs are now committed at `data/raw/`; read only.

## Environment and rules
Every command starts a new shell. Begin every test/server command with `$env:GRIDLOCK_TEST_PORT='8771';`. `GRIDLOCK_AI=off`; Python only as `& $env:GRIDLOCK_PY`; `PLAYWRIGHT_BROWSERS_PATH` set; no network. Never print environment variables. Test first; never weaken a check. Unknowns stay null and data verbatim. Stop and report on AGENTS.md hard-rule triggers. Stage by path; never `git add -A`, `git stash`, `git clean`, `git reset --hard`; one new commit `DATA: T0.3b stabilize IDs and source pages`; never merge, push or touch main.

## Report
Task, files changed, each acceptance line with failing and passing output, suite totals, deviations, exact `For <lane>` patches, open questions, one dated one-line lesson. Save it to the owned report path and include it in your final response. Report only checks you ran.
