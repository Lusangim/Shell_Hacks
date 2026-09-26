# GridLock delivery report

**In progress — last tagged gate G1. G2 VERIFY passed at 12:42 EDT on 2026-09-26; the G2 reviewer round is pending.** This is a current handoff, not the final delivery.

## What works now

- The local app shows a modern offline street map of Georgia and South Carolina, 489 ranked public-plan overlaps, search, filters, project/pair detail, a source-year timeline, source PDFs, CSV export and a Letter print report. A missing PMTiles archive falls back visibly to state outlines.
- The API serves the fixed read-only PMTiles archive with validated HTTP Range. Optional Google roadmap/satellite is available only with an explicitly configured browser key and online state; every build test and server run kept Google off and never opened the real key.
- Source processing keeps 230 of 481 input rows, places 181 projects, records 128 unplaced explanations, and builds 489 cross-utility overlaps, 43 across source states. Kept projects cite public PDF pages; unknown and inferred locations remain labelled.
- `SETUP.cmd -Offline` was exercised against the existing environment. To run locally: `START.cmd -Port 8770 -NoBrowser`; to verify: set `GRIDLOCK_GOOGLE=off` and run `VERIFY.cmd` on port 8790. The lead stops its test servers and browsers after each run.
- No Claude API, real Google request, network download, push, deployment, payment, message or submission occurred.

## Task state

| Task | State and evidence |
|---|---|
| T0.0–T0.8; T1.0 | Setup complete per `tasks/todo.md`; T0.7 was skipped by founder direction. |
| T0.2, T0.3a, T0.3b, T0.4 | Done: source pipeline, frozen contracts/fixtures, 230 citations and offline harness; G1a and G1 VERIFY passed. |
| T1.1, T1.2, T1.3, T1.5 | Done: parsed project fields, local API, keyboard map/list shell and source-backed places/outlines. |
| T1.4a | Done: 18 quick audits, broken-page proofs and repeated green runs; `lead/T1.4a.md`. |
| T1.6 | Done on main: API `5c0101d`, WEB `ccd0702`, WEB-2 search flight `18e2544`; source-backed two-state map and lazy optional Google. Main quick gate 344/19/18. API and browser security reviews finished with no open finding after the T16-WEB-SEC-01 repair. Desktop zoom 6–17; phone initial/minimum 5.5 is the declared fit needed to show both complete states above two ranked rows. Live Google compatibility is untested. |
| T1.7, T1.8 | Not started: readable detail/print text and guided walkthrough, both added by the founder. Direction and acceptance are in `design/DIRECTION-v2.md` and `tasks/todo.md`. |
| T2.1, T2.2, T2.3, T2.4 | Done: 489 geodesic pairs and 43 true cross-state pairs; 55 border provenance repairs, 49 unknowns retained; 201 labelled savings ranges, 214 timing-too-far, 74 no-cost; typed detail, safe BOM CSV and two whitelisted local source PDFs. |
| T2.5a, T2.5b, T2.6, T2.7 | Done: project and overlap detail, pair map highlighting/deep links, validated filters/URL state, source-year slider and play/pause. Existing browser hydration races were repaired in test-only commits `d5e2366` and `a507d8b` without removing assertions. |
| T2.8a, T2.8b | Done: typed local place/project/station search and keyboard duplicate-choice UI. |
| T2.9 | Done: server-byte CSV download for current filters and Letter print report, `3057075` merged as `d6980c0`; lead reran three CSV cases, synced lane gate 278/19/18, scoped security P0–P3 zero. |
| T2.10 | Done: named-example table and cautious Savannah/Augusta demo wording in `docs/METHODOLOGY.md`; source-page no-hit evidence kept for unlisted projects. |
| T2.11 / G2 reviewers | Pending on frozen main after the green G2 VERIFY: domain top-ten spot-check, behavioral test analysis and silent-failure sweep. |
| T3.1, T3.2, T3.3a, T3.4a | Built on held `wt/api`, not merged before G2 tag. T3.1 real-ID eval/template and T3.2 fake-client generator passed a 359/18/18 lane gate; two T3.2 P2 malformed-input findings were confirmed closed. T3.3a guarded brief routes passed 107 focused and a separate security review with zero findings; its first full gate exposed WEB test timing races, repaired on main, and its synced full gate remains due after G2. T3.4a area API passed 254/17/18 on its earlier branch state. No real client/spend path is enabled. |
| T3.3b, T3.4b, T3.5, T1.4b | Not started: brief UI, area UI, resilience/counties/dark-theme completion and full audit matrix. |
| T4.1–T4.4, G3/G4, D.1–D.3 | Not started. The founder capped post-G3 judging at four rounds; the final delivery requires sanitizer, README, green VERIFY and tag `delivered`. |

## Verification and judgment

G2 pre-review VERIFY summary: `C:\Users\lucia\dev\gridlock-runs\verify\20260926-123703-505\summary.json` — exit **0**, **344 passed**, **0 failed**, **0 skipped**, baseline **344**, commit `cfc300e`. Four pytest warnings concern `record_property` with JUnit xunit2; assertions passed. The final main quick gate on the same product and new connected demo-path test passed **344 suite + 19 shell + 18 audits**. The demo check walks search → pair → detail → both local source PDFs → server CSV. Four current 1440/390 light/dark screenshots are in `g2/`.

G1a type review found two HIGH, both corrected and confirmed; two MEDIUM remain (nested Pydantic mutability and exported JSON Schema cross-field expressiveness). G1 Python review's false GA/GA cross-state bonus was corrected and confirmed; JS review was ready. The known pipeline publication MEDIUM remains: seven artifacts are replaced sequentially, so a late failure could leave mixed output. G1 is tagged `g1`.

T2.6 scoped security review had no findings. T2.9 scoped security review had P0–P3 zero. T1.6 API security review had P0–P3 zero. T1.6 browser review round 1 found one P2 delayed Google→Satellite selection race; WEB reproduced and fixed it, added stale-layer/cancellation checks, and fresh round 2 found P0–P3 zero with `material improvement still available: no`. Held T3.2 and T3.3a security confirmations have no open finding. G2 domain, tests and silent-failure verdicts are pending.

## Parked work and founder decisions

No decided feature was cut. Phase 3 API commits are held off main until G2 is tagged; their UI is not on the current demo path. Historical `wt/web` and `wt/web-2` failed attempts remain parked; the corrected implementations are on main. A missing external PMTiles archive shows an outline fallback. Optional Google controls stay hidden without a configured key or browser online state. This runtime exposes four total agent slots, including the lead, despite the founder's requested ceiling of eight.

- **SERTP/CEII (Q2):** the publicly posted SERTP overview has page headers marked `(CEII)` while the spec both acknowledges use of that overview and says to use nothing marked CEII. The unattended safe state is the already loaded, cited public overview, with no new transcription from marked passages; founder/Sperry must decide acceptability before public release.
- **People and external services:** team roster/roles/Discord tags and licence are unknown; no person or contact was invented. Claude access and a spend ceiling are not approved, so briefs remain offline templates. A real Google browser key, provider restrictions, CSP host completeness and live roadmap/satellite loading were not tested; founder-run online acceptance is needed before presenting that optional mode.
- **Source checks:** Okatie remains inferred until the founder verifies it on a route map. The loaded plans contain no Thomson–Vogtle project by name; adding one requires a verified source and founder decision. The founder may decide whether phone zoom 5.5 is acceptable for the two-state first view.

No Claude-owned file was edited. Proposed profile correction after delivery: `PROJECT-PROFILE.md` describes VERIFY as a private-worktree/browser-matrix run with a Markdown summary, while the actual `scripts/verify.ps1` runs compileall and pytest on the selected repo and writes JSON; quick-gate separately runs shell and audits. The SPEC/Q2 source-classification tension also needs a founder decision, not a silent spec edit.

## Lessons and resume

2026-09-26 — Source-backed state geometry must drive first-view tests; a tiny synthetic rectangle hid a real overview requirement.

2026-09-26 — Shared lazy map initialization and per-click selection freshness need separate state; an obsolete request may not cancel the newest choice.

2026-09-26 — Server-byte exports and current-filter revisions prevent browser reconstruction or stale print reports.

The lead session ID is the `thread_id` in the newest `C:\Users\lucia\dev\gridlock-runs\codex\*-lead.jsonl`. To resume: `codex exec resume <session id>`, then read `MISSION.md`, `TRACKER.md`, `tasks/todo.md` and `git status`. No builder is running at this G2 pre-review freeze; the three G2 gate reviewers are next. This report will be rewritten after their findings and at every later gate.
