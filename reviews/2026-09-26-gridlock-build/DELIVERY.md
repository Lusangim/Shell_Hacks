# GridLock delivery report

**In progress (last gate G1, 2026-09-26 07:00 EDT).** This is a gate hand-off, not the final delivery.

## What works now

- Offline source processing keeps 230 of 481 source rows, places 181 projects, and produces 489 cross-utility overlaps, 43 across states. Each kept project cites a real PDF page.
- The local API validates artifacts at startup and serves health, metadata, basemap, project and overlap routes with bounded filters.
- `SETUP.cmd -Offline` passed with the existing environment; `START.cmd -Port 8770 -NoBrowser` served fixture health and was stopped; `VERIFY.cmd` is the full check.
- The public map and ranked list load from production artifacts on main; keyboard, focus, axe, overflow, external-request and copy audits pass. G1 desktop and phone screenshots are in `g1/`.
- No Claude API, network request, push, deployment or submission occurred.

## Task state

| Task | State and evidence |
|---|---|
| T0.0–T0.6, T0.8–T1.0 | Done in setup, per `tasks/todo.md`; T0.7 skipped by founder. |
| T0.2 | Done, `d9604b0`; source counts, top ten and deterministic rebuild checks passed. |
| T0.3a | Done, `1b190e6`; exported schemas and typed fixtures validated. |
| T0.3b | Done, `d635f20`; 230 page citations and artifact contracts checked. |
| T0.4 | Done, `fdd8539`; offline setup, START fixture, port isolation and VERIFY proved. |
| T1.2 | Done, `ca53d05`; API tests passed. |
| T1.3 | Done, `c1e4e6c` with axe, focus and city-label corrections; main quick gate 139 passed, 17 shell checks and 18 audits passed. |
| T1.5 | Done, `24e50d8`; 1,150 local places, basemap, full metadata, focused 3 passed and main quick gate 61 passed. |
| T1.1 | Done since G1a, `7298579`; 37 focused checks, five PDF cost hand-checks, complete 459 SERTP marker accounting. |
| T1.4a | Done; `reviews/2026-09-26-gridlock-build/lead/T1.4a.md`. Three 17-check runs passed, then the main quick gate passed 135 suite + 17 shell + 18 audit with no skip. |
| T2.1 | Done since G1; `102b6ad`. 489 geodesic overlaps, 43 source-state cross-state, source-backed touch reasons, 21 focused lead rerun and 156 suite + 17 shell + 18 audit lane quick gate. |
| T2.2 | Done since G1; `8efaaaa`. All 55 mapped border projects have named location provenance; 49 kept unknowns show reasons; Okatie remains INFERRED. Five lead checks and integrated main quick gate 173 suite + 17 shell + 18 audits passed. |
| T2.3 | Done since G1; `79869e7`. Formula recorded before code; 201 clearly labelled screening ranges, 214 timing-too-far and 74 no-cost outcomes. Assumption text follows validated rates. Thirteen focused lead checks and integrated main quick gate 186 suite + 17 shell + 18 audits passed. |
| T2.4 | Done since G1; `ae1fa7a`. Typed pair detail, unpaged BOM CSV with safe text cells, and two whitelisted local source PDFs. Eighteen focused lead checks and integrated main quick gate 204 suite + 17 shell + 18 audits passed. |
| T2.8a | Done since G1; `44aefc2`. Typed local search over 1,150 places and placed projects/stations, 12 focused lead rerun and integrated main quick gate 168 suite + 17 shell + 18 audits. |
| T2.8b | Done since G1; `321bd0e`. Local keyboard search and source-backed duplicate choices, 390 px two-row sheet, ten focused lead e2e checks and integrated main quick gate 214 suite + 17 shell + 18 audits passed. Original `wt/web-2` branch remains a parked historical attempt. |
| T2.5–T2.7, T2.9–T2.11; T3.1–T3.5; T1.4b; T4.1–T4.4; D.1–D.3 | Not started or in progress on a branch. |
| G1a | Passed: type review and confirmation, full VERIFY green. |
| G1 | Passed: Python HIGH corrected and confirmed, JS ready, full VERIFY green, 1440/390 screenshots and house patterns committed. |
| G2–G4 | Not started. |

## Verification and judgment

G1 VERIFY: `C:\Users\lucia\dev\gridlock-runs\verify\20260926-065451-443\summary.json`: exit 0, 139 passed against baseline 139, 0 failed, 0 skipped. The preceding G1a VERIFY had 58 passed and one named temporary skip; G1 has no skip. The G1 lane quick gate passed 139 suite, 17 shell and 18 audit checks.

G1a type design round 1 (`judge-type-g1a-r1/JUDGMENT.md`) found 2 HIGH and 4 MEDIUM; material improvement available. Round 2 (`judge-type-g1a-r2/JUDGMENT.md`) confirmed both HIGH closed by direct probes and fixtures, with 26 focused checks passing. Multiline member and nonnegative/reconciled count MEDIUMs are closed. Two MEDIUMs remain: nested lists in frozen Pydantic models can mutate, and exported JSON Schemas do not encode all runtime cross-field validators. The optional JSON Schema runtime probe could not run because `jsonschema` is not installed; no dependency was added. No CRITICAL or HIGH finding remains.

G1 Python round 1 (`judge-python-g1-r1/JUDGMENT.md`) reproduced one HIGH: a Georgia/Georgia pair was flagged cross-state and scored with the 1.5 bonus. DATA repaired it in `eafbb0e`; the count changed 44→43, that pair's score 0.096→0.064 and rank 323→385, and top ten stayed unchanged. The fresh Python confirmation (`judge-python-g1-r2/JUDGMENT.md`) found no remaining CRITICAL/HIGH and said material improvement still available: no. The JavaScript reviewer (`judge-js-g1-r1/JUDGMENT.md`) reported ready, no findings and no material improvement available. One Python MEDIUM remains: `pipeline/build_all.py` publishes seven artifacts sequentially, so a late failed replacement could leave a mixed dataset; it is tracked for later DATA work.

## Parked work, choices and questions

The original `wt/web-2` T2.8b branch remains parked as a historical failed attempt; the independent phone and duplicate-label repair is merged and verified. No feature cut was made. Unknown roster, licence, Okatie verification, and Claude access remain open founder questions. Safe defaults: no invented person or endpoint, Okatie stays inferred, no API calls or spend, no push or submission. Sperry acceptance of the public SERTP overview plan is also unconfirmed; only public material is used.

Q2 provenance caveat for Sperry and G2 domain review: the already committed, publicly posted SERTP 2025 overview PDF has transmission-project page headers marked `(CEII)`. SPEC Q2/Q11 explicitly acknowledge this and set the unattended default to use the existing overview, while SPEC's boundary also says to use nothing marked CEII. DATA T2.10 is citing existing artifact fields and pages without newly transcribing marked passages. The founder and Sperry need to resolve whether the source is acceptable before any public push; the lead will not remove a decided source or rewrite history without that decision.

No change to Claude-owned files is proposed. The G1a contract guards were added before freeze; later changes require the SPEC type review procedure.

T1.1 surfaced stale parsed CSVs with ASCII hyphens where the source PDF prints en dashes. The lead assigned those two derived CSV files to DATA T1.1 for an offline, completeness-checked re-extraction; 22 DESC names were corrected, the SERTP CSV stayed byte-identical, and original PDFs remained read-only.

## Lessons and resume

2026-09-26 — Contract fixtures need impossible-state probes; a valid fixture alone did not catch contradictory savings and same-utility overlaps.

2026-09-26 — A utility name cannot stand in for the source-backed state when a ranking rule depends on geography.

The lead session ID is recorded in the newest `C:\Users\lucia\dev\gridlock-runs\codex\*-lead.jsonl`; resume it with `codex exec resume <session id>` and first read MISSION.md, TRACKER.md, todo.md and git status. G1 is tagged; DATA T2.1/T2.2/T2.3, API T2.4/T2.8a and WEB-2 T2.8b have since merged. WEB T2.5a and DATA T2.10 are running. The Codex lead continues.
