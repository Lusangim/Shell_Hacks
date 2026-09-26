# API — T4.3 judged CSV handoff corrections

Sub-agent of the Codex lead, most capable model, high reasoning. Work only in `C:\Users\lucia\dev\gridlock-wt\api-t43` on `wt/api-t43`, from main `07ae0ac`. One task, one commit: `API: T4.3 qualify exported savings and utility`. Port 8779.

Read first: AGENTS.md; .agents/skills/gridlock-build/SKILL.md §0/§2; SPEC.md § Contracts/Overlap rules/Code style/Boundaries; definition-of-done.md; house-patterns.md; review-checklists §A/§C/§E/§K. Read frozen G3 business and domain judgments on main read-only, especially JBUS-01 and JDOMAIN-01, including their exact acceptance checks. No contract/schema change.

## Acceptance
- JBUS-01: export still has 489 ordered rows unfiltered and existing identity/numeric/source columns. Each of 201 savings ranges is explicitly labelled an estimate and includes its readable basis, applicable dated team assumptions (top pair's 1%–3% of known $5,376,418 scope, partner cost unknown; mileage-proxy example's $1m–$3m/mi) and not-verified/shared-work caveat. Non-range statuses explain why without invented range amounts; no raw assumption ID in a user-facing text field. Filtered/browser download parity and CSV formula protection persist.
- JDOMAIN-01 CSV portion: Utility A/B cells qualify `utility_basis=inferred_from_location` as `(inferred)`; stated utilities stay plain. Canonical API JSON/filter/search/contacts values unchanged.
- JDOMAIN-01 offline-brief sibling: the real top Template must not claim an inferred utility is source-listed (the current `server/brief_template.py` says both projects are “listed by” their utilities, then adds a later generic caveat). Qualify the inferred project's attribution in the opening wording and retain the existing explicit ownership-verification caveat. Keep canonical organization contact labels and the frozen Brief schema unchanged; add a RED/GREEN real-ID test.
- Preserve UTF-8 BOM, deterministic column order and CRLF CSV behavior; do not weaken any existing test. Use the stored `savings.basis`, `assumption_ids` and committed assumptions with faithful presentation wording; avoid inventing values or contacts.

## You own
`server/app.py` only for CSV export logic, `server/brief_template.py` only for the source-listed attribution wording, `tests/api/test_detail_export.py`, `tests/api/test_briefs.py`, optionally new focused `tests/api/test_t43_csv.py` and `tests/api/test_t43_brief.py`, and report `reviews/2026-09-26-gridlock-build/api-t43/T4.3.md`. Everything else read-only, especially WEB/WEB-2, frozen `server/schemas.py`/`contracts/` and data artifacts. If a change requires another owner, write a “For WEB/WEB-2” patch in your report.

## Verification and rules
Test first with real top and proxy pairs: RED → smallest GREEN. Run focused tests then `scripts\quick-gate.ps1` on your branch. Start each test/server command `$env:GRIDLOCK_TEST_PORT='8779'; $env:GRIDLOCK_AI='off'; $env:GRIDLOCK_GOOGLE='off';`; Python only `& $env:GRIDLOCK_PY`; baseline 674. No network/install/real Google/Claude/key/credential/.env/debug.log access, env prints, 8765, push/deploy/send. Run every command inside your worktree, never main. Read text with `Get-Content -Encoding UTF8`; edit repo text via apply_patch. Stage exact owned paths; never `git add -A`, stash, clean or reset-hard. Do not merge/touch main. If AGENTS stop rule applies, park and report with work committed. Stop your browsers/servers and report port state.

Final message and saved report: files changed; each acceptance line with before/after check output; focused and quick-gate totals; deviations; “For WEB/WEB-2” patches; questions; one dated lesson. Report only checks you ran.
