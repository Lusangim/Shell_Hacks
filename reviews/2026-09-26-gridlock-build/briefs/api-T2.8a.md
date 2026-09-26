# API — T2.8a local search route (sub-agent of Codex lead; gpt-6-sol, reasoning high)

Read first in your worktree: repo `AGENTS.md`; `.agents/skills/gridlock-build/SKILL.md` §0 and §2; `SPEC.md` Contracts and Code style; `references/definition-of-done.md`; `reviews/2026-09-26-gridlock-build/house-patterns.md`; task T2.8a in `tasks/todo.md`; `references/review-checklists.md` §A/C/E. Read text with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task and verification

Add `GET /api/search?q=` across locally built `places.json`, placed project names and named substations/endpoints, returning at most ten typed `SearchResult` records (`type`, `label`, `lat`, `lon`, `ref`). Match query prefixes and word starts; q shorter than two characters returns 422. Search is deterministic, case-insensitive and uses only local validated artifacts. Ensure `sav` returns Savannah first and `okat` returns an Okatie project, with honest coordinates and no invented substation position. Preserve startup behavior for existing synthetic API fixtures that do not have `places.json`, while requiring the real production artifact if applicable. Use the frozen `server.schemas.SearchResult`; no contract edit. No outbound request.

Write `tests/api/test_search.py` first and run RED, including the named real searches, shorter query, no result, ten-result cap, type validation, source-backed coordinates, and special-character input. Run focused API tests and the lane `scripts/quick-gate.ps1` GREEN. Every changed response path must validate against the contract. Test input abuse and avoid regex injection. Do not weaken, skip or delete checks.

## Ownership and environment

Worktree `C:\Users\lucia\dev\gridlock-wt\api`, branch `wt/api`, synced to G1 by the lead. **Run every command inside that worktree, never `C:\Users\lucia\dev\gridlock`.** Own `server/` except frozen `server/schemas.py`, `tests/api/test_search.py` and other tests under `tests/api/` needed for this route, and your report `reviews/2026-09-26-gridlock-build/api/T2.8a.md`. Read-only: `contracts/`, `data/`, `pipeline/`, `web/`, LEAD files, `SPEC.md`, `.agents/`, `.claude/`. Port 8772: begin every test/server command `$env:GRIDLOCK_TEST_PORT='8772';`; Python only `& $env:GRIDLOCK_PY`; `GRIDLOCK_AI=off`; no network, install or secrets. Every command starts a new shell. Stage by path, never `git add -A`, `git stash`, `git clean` or `git reset --hard`; never print environment variables. No merge, push, deploy, submit or sending.

Stop/report if a fix adds errors, the same error survives three tries, another lane/contract/architecture change is needed, or a dependency is missing. One commit `API: T2.8a add local search`. Final report and message: acceptance/check/RED/GREEN per line, suite totals, deviations, For API patches, open questions and a dated one-line lesson. Report only what ran.
