# DATA — T1.5 Build extras (Codex builder, gpt-6-sol, high)

Read first: AGENTS.md, `.agents/skills/gridlock-build/SKILL.md` §0 and §2, SPEC.md § Contracts and § Code style, `.agents/skills/gridlock-build/references/definition-of-done.md`, `reviews/2026-09-26-gridlock-build/house-patterns.md` if it exists, review-checklists §B, §C, §E. Read text with `Get-Content -Encoding UTF8`; edit repo text with apply_patch.

## Task
T1.5 acceptance from `tasks/todo.md`: `build_all` writes `places.json` for Census places in GA and SC, `basemap.json` with state outlines and city labels now (counties belong to T3.5), and full contract-valid `meta.json` with stage counts, `no_overlap_count`, and `unmapped_count` with truthful reasons including unplaced Southern Company rows. Set `utility_basis="inferred_from_location"` for unprefixed Southern rows placed in GA; other basis values follow source evidence. Preserve prior T0.3b IDs, citations, 230/181/477/44 counts, ranked top ten, and byte-identical rebuild. Use the committed `data/raw/places_se.csv` and `us_states.geojson`; the ignored `C:\Users\lucia\dev\gridlock\gridlock-data\gaz_places.zip` is available read-only if needed. Never invent a place coordinate.

Write `tests/pipeline/test_build_extras.py` with RED/GREEN for these outputs, nonempty local basemap, counts/reasons and repeatability. Also prove the production `server.app.load_artifacts(data/build)` succeeds once basemap exists. If a frozen contract blocks a truthful output, stop and report an exact `For LEAD` patch; do not edit `server/schemas.py` or `contracts/`.

## Ownership
Worktree `C:\Users\lucia\dev\gridlock-wt\data`, branch `wt/data`, port 8771. Own `pipeline/` except `briefs.py`, `data/build/`, `data/manual/` except contacts, `tests/pipeline/test_build_extras.py`, and report `reviews/2026-09-26-gridlock-build/data/T1.5.md`. Other tests and all server files are read-only; request lead authorization before modifying a regression check. Never run a command in `C:\Users\lucia\dev\gridlock`.

## Environment and rules
Every command starts a new shell. Begin every test/server command with `$env:GRIDLOCK_TEST_PORT='8771';`. `GRIDLOCK_AI=off`; Python only as `& $env:GRIDLOCK_PY`; `PLAYWRIGHT_BROWSERS_PATH` set; no network. Never print environment variables. Test first; never weaken a check. Unknowns stay null and data verbatim. Stop and report on AGENTS.md hard-rule triggers. Stage by path; never `git add -A`, `git stash`, `git clean`, `git reset --hard`; one new commit `DATA: T1.5 build places basemap and meta`; never merge, push or touch main.

## Report
Task, files changed, every acceptance check's failing and passing output, suite totals, deviations, exact `For <lane>` patches, open questions, one dated one-line lesson. Save to the owned report path; report only what you ran.
