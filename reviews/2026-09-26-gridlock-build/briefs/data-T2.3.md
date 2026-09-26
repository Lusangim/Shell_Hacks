# DATA — T2.3 savings model (sub-agent of Codex lead; gpt-6-sol, reasoning high)

Start after DATA T2.2 merges. Read inside your worktree: repo `AGENTS.md`; `.agents/skills/gridlock-build/SKILL.md` §0 and §2; `SPEC.md` Contracts, Overlap rules and Code style; `references/definition-of-done.md`; `reviews/2026-09-26-gridlock-build/house-patterns.md`; T2.3 in `tasks/todo.md`; `references/review-checklists.md` §A/B/C/E. Read with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task

**Write the proposed formula and hand-worked examples into `reviews/2026-09-26-gridlock-build/data/T2.3.md` before changing model code.** Then implement an honest savings estimate for each overlap. Create `data/manual/assumptions.json` with each assumption's id, low/high, unit, precision, rationale, and dated public source or explicit `team assumption`. Do not present a team assumption as a sourced rate. A usable plan cost takes priority; if a proxy is used, flag it in `savings.basis` and ground its unit/cost arithmetic in the assumptions file. Unknown values stay null, never zero. `savings.status` must be `range`, `timing_too_far` (year gap > 2), `no_cost`, or `unknown_year`; a range has low < high, visible assumption IDs and explicit basis. Round only to the assumptions' stated precision. Savings do not enter ranking score. Keep source project amounts verbatim and respect cost flags. Rebuild deterministic artifacts and report how many pairs receive each status, plus at least one named pair's hand calculation.

## Verify

Write `tests/pipeline/test_savings.py` first and run RED. Include hand-computed examples for all four statuses; missing cost/year; year gaps exactly 2 and 3; plan versus proxy basis; low/high ordering; precision; a real pair from built artifacts; and deterministic rebuild. Run focused and affected pipeline tests, then lane `scripts/quick-gate.ps1`. Do not weaken, skip or delete checks. If the frozen contract cannot express an honest result, stop and report rather than editing it.

## Ownership and environment

Worktree `C:\Users\lucia\dev\gridlock-wt\data`, branch `wt/data`, synced to main by the lead. **Run every command in this worktree, never `C:\Users\lucia\dev\gridlock`.** Own `pipeline/` except `briefs.py`, `data/manual/assumptions.json`, generated `data/build/`, `tests/pipeline/` except `test_contracts.py`, and your report `reviews/2026-09-26-gridlock-build/data/T2.3.md`. Everything else is read-only, including `server/schemas.py` and `contracts/`. Port 8771: begin each test/server command `$env:GRIDLOCK_TEST_PORT='8771';`; Python only `& $env:GRIDLOCK_PY`; `GRIDLOCK_AI=off`; no network, install or secrets. Every command starts a new shell. Stage by path; never `git add -A`, `git stash`, `git clean` or `git reset --hard`; never print environment variables. No merge, push, deploy, submit or sending.

Stop/report if a fix adds errors, the same error survives three tries, a contract/architecture/other-lane change is needed, or a dependency is missing. One commit `DATA: T2.3 estimate coordination savings`. Final report and message: formula recorded before code, acceptance/check/RED/GREEN per line, suite totals, status counts, deviations, For DATA patches, open questions and one dated lesson. Report only what ran.
