# API — T1.2 API skeleton (builder)

Read first: AGENTS.md, `.agents/skills/gridlock-build/SKILL.md` §0 and §2, SPEC.md § Contracts and § Code style, `.agents/skills/gridlock-build/references/definition-of-done.md`, review-checklists §B, §C, §E. Read text with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task
Implement T1.2 from `tasks/todo.md`: `create_app()` and `server/__main__.py`; load and validate artifacts once at startup and refuse clearly when missing/invalid; settings object (never read a key at import, `GRIDLOCK_AI` off/on); typed `response_model` on every route; no CORS; 127.0.0.1 only; host check for 127.0.0.1 and localhost; CSP `default-src 'self'`, nosniff, referrer policy; GET `/api/health`, `/api/meta`, `/api/basemap`, `/api/projects` with filters, `/api/projects/{id}`, `/api/overlaps` with both-project filter semantics, rank order, limit <=500 and offset; error body `{error:{code,message}}`. `/api/projects` returns a GeoJSON FeatureCollection and `/api/overlaps` a bare array. Serve `data/build/basemap.json` once DATA T1.5 creates it; use its `tests/fixtures/api/basemap.json` fixture only until then. Current DATA T0.2 artifacts are legacy-shaped and DATA T0.3b/T1.5 will bring them into contracts, so test against `tests/fixtures/api/` and state clearly that live artifact validation awaits those tasks. Do not silently coerce legacy data into contract values.

Write `tests/api/test_core.py`: happy paths, 422 bad filters and >500 limit, unknown IDs, bad host 400, every response validated against `server/schemas.py`, and socket guard. Prove RED then GREEN. Make startup path configurable for a test artifact folder, while production defaults to `data/build`.

## Ownership
Worktree `C:\Users\lucia\dev\gridlock-wt\api`, branch `wt/api`, port 8772. Own `server/` except `server/schemas.py` and `server/export_contracts.py`, `tests/api/`, and report `reviews/2026-09-26-gridlock-build/api/T1.2.md`. Other files, especially `contracts/`, are read-only. Never run a command from `C:\Users\lucia\dev\gridlock`. The committed T0.3a contract is on main `1b190e6`; worktree is created from current main.

## Environment and rules
Every command starts a new shell. Begin every test/server command with `$env:GRIDLOCK_TEST_PORT='8772';`. `GRIDLOCK_AI=off`; Python only as `& $env:GRIDLOCK_PY`; `PLAYWRIGHT_BROWSERS_PATH` is set; no network. Never print environment variables. Test first; never weaken a check. Unknowns stay null; names/descriptions verbatim. Stop and report on AGENTS.md hard-rule triggers. Stage by path; never `git add -A`, `git stash`, `git clean`, `git reset --hard`; one commit `API: T1.2 build API skeleton`; never merge, push or touch main.

## Report
Task, files changed, each acceptance line with failing and passing output, suite totals, deviations, exact `For <lane>` patches, open questions, one dated one-line lesson. Save it to the owned report path and include it in your final response. Report only checks you ran.
