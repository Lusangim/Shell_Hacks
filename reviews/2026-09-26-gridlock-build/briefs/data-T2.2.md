# DATA — T2.2 location quality and border region (sub-agent of Codex lead; gpt-6-sol, reasoning high)

Read first in this order, inside your worktree: repo `AGENTS.md`; `.agents/skills/gridlock-build/SKILL.md` §0 and §2; `SPEC.md` Contracts, Overlap rules and Code style; `references/definition-of-done.md`; `reviews/2026-09-26-gridlock-build/house-patterns.md`; T2.2 in `tasks/todo.md`; `references/review-checklists.md` §A/B/C/E. Read text with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task

Every project with an endpoint in the border region (lat 31.5–34.0, lon −82.8 to −80.5) must be placed from a named public source or remain unknown with its reason. Each hand fix in `data/manual/manual_locations.csv` must carry a source and note. Keep Okatie explicitly INFERRED because the founder has not verified the route-map position. Do not invent coordinates, endpoint equivalence or a claim of exactness. Use only already committed public inputs and the named read-only main-copy inputs when needed. Report a before/after table of region placement, total placed/unmapped, overlaps, cross-state count, top-ten changes and why; the lead approves the table before merge.

## Verify

Write `tests/pipeline/test_manual_locations.py` first and run it RED before implementation. Check the region's full relevant project set, source-backed/manual provenance, unknown reasons, and Okatie's INFERRED accuracy. Run focused tests, a byte-identical offline rebuild, and `scripts/quick-gate.ps1` on your lane branch. Keep existing count and ranking tests accurate to verified data; never weaken, skip or delete a check. If no additional coordinate can be sourced, retain unknowns and explain the complete search rather than inventing one.

## Ownership and environment

Worktree `C:\Users\lucia\dev\gridlock-wt\data`, branch `wt/data`, after the lead syncs G1 and T2.1. **Run every command inside this worktree, never in `C:\Users\lucia\dev\gridlock`.** Own `pipeline/` excluding `briefs.py`, `data/manual/manual_locations.csv`, generated `data/build/`, `tests/pipeline/` excluding `test_contracts.py`, and `reviews/2026-09-26-gridlock-build/data/T2.2.md`. All other files are read-only, especially frozen `server/schemas.py` and `contracts/`. Port 8771: each test/server command starts `$env:GRIDLOCK_TEST_PORT='8771';`; Python only `& $env:GRIDLOCK_PY`; `GRIDLOCK_AI=off`; no network, install or secrets. Stage by explicit path. Never `git add -A`, `git stash`, `git clean` or `git reset --hard`; never print environment variables. No merge, push, deploy, submit or sending.

Stop and report if a fix adds errors, an error survives three tries, you need another lane's file or a contract/architecture decision, or a dependency is missing. One commit `DATA: T2.2 audit border locations`. Final report and message: every acceptance line with RED/GREEN output, suite totals, before/after table, deviations, For DATA patches, open questions and one dated lesson. Report only what ran.
