# GridLock delivery report

**In progress — G3 feature freeze, 2026-09-26 17:16 EDT.** Main VERIFY passed on `efc5283` with 674 passed, zero failed and zero skipped. The product is ready for the founder's two frozen judging rounds. This report is a current handoff, not final delivery.

## What works now

- The local app shows a modern offline map of Georgia and South Carolina, 489 ranked public-plan overlaps, source-backed project and pair details, search, filters, timeline, area explorer, CSV, Letter print and a guided tour. All 24 audit scene combinations passed at 1440/390 px in light/dark themes.
- The data pipeline keeps 230 of 481 input rows, places 181 projects, explains 128 unplaced rows, and records 43 cross-state overlaps. Unknown and inferred locations stay labelled; costs and savings retain their basis and caveats.
- Briefs are graded offline templates by default. The 30-case real-ID evaluation has 20 development and 10 held-out cases; all 30 selected templates and all 489 built-overlap templates passed the grader. No real Claude call or spend occurred.
- The local PMTiles map is optional on a fresh clone: when its separate archive is absent, the app visibly falls back to state outlines. Optional Google map controls require a configured browser key and an online browser; every build test and server run kept Google off and never opened the real key.
- To run: `SETUP.cmd -Offline` with the prepared local environment, then `START.cmd -Port 8770 -NoBrowser`; to verify, set `GRIDLOCK_GOOGLE=off` and run `VERIFY.cmd` with a free `GRIDLOCK_TEST_PORT`. README still describes the old preview and is due for correction at D.2.

## Task state and evidence

| Tasks | State |
|---|---|
| T0.0–T0.8, T1.0 | Setup and design complete per `tasks/todo.md`; T0.7 skipped by founder direction. |
| T0.2, T0.3a/b, T0.4 | Source pipeline, frozen contracts, PDF citation checks and offline harness complete; G1a and G1 tagged. |
| T1.1–T1.3, T1.5 | Parsed source fields, local API, keyboard map/list shell and source-backed places/outlines complete. |
| T1.4a, T1.4b | Quick audits and full gate complete. T1.4b `4eeb008`: 37/37 real matrix, 50/50 scratch proofs, three 3/3 repeats, 674 suite + 19 shell + 99 audits; exact 4.5:1, 3:1 and 44 px boundaries. The T1.7 copy-lint P3 is closed. |
| T1.6–T1.8 | Modern offline map with optional Google mode, readable detail/print/brief text and guided walkthrough complete. The phone overview's minimum zoom is 5.5 to show both states above the two-row sheet, a declared T1.6 deviation. Live Google compatibility remains a founder-run check. |
| T2.1–T2.4 | 489 geodesic overlaps, 43 true cross-state pairs, 55 border provenance repairs, 49 unknown project locations, 201 labelled savings ranges, typed detail, safe CSV and two whitelisted local source PDFs complete. |
| T2.5a/b, T2.6–T2.9 | Project/pair detail, filters, timeline, typed local search, CSV export and readable Letter print complete; browser race, URL and keyboard checks included in VERIFY. |
| T2.10–T2.11 | Six named examples and cautious source wording recorded; G2 domain judge checked top ten source records and five distances. All seven assigned G2 P2/P3 wording, race and gesture findings were repaired before G3. |
| T3.1–T3.3b | Real-ID evaluation, deterministic grader/template, fake-client guarded generation/cache, brief routes and offline brief UI complete. Real Claude use is deferred to F6 only after founder access and a ceiling. |
| T3.4a/b, T3.5 | Projected 1–80 km area API/UI, URL/history/race handling, counties, offline resilience, gestures and dark theme complete. |
| G3 | Feature freeze: all decided features are demoable offline; full matrix and held-out evaluation green; G3 tag pending this report's commit. |
| T4.1–T4.3, G4, D.1–D.3 | Not started. Founder amendment 5 caps judging at two rounds on frozen `g3`, then P0/P1 and small local P2 fixes, VERIFY, sanitizer, README and final delivery. T4.4 confirmation round skipped by founder. |
| F1–F7, T5.0–T5.5, H0–H9 | Claude and founder work after Codex delivery; not started by this lead. Nothing was pushed, deployed, submitted, sent or purchased. |

## Verification and judgments

G3 VERIFY summary: `C:\Users\lucia\dev\gridlock-runs\verify\20260926-165341-069\summary.json` — **exit 0, 674 passed, 0 failed, 0 skipped, baseline 674**, tested commit `efc5283`. The earlier 16:44 VERIFY folder is empty because a model-capacity stop interrupted that process; the complete 16:53 run supersedes it. Pytest reported 32 `record_property`/xunit2 warnings; assertions passed. The full audit lane gate on the same product passed **674 suite + 19 shell + 99 audits**. The lead independently reran a complete default scene and exact 44 px scratch proof. The manifest and selected-template evaluation passed **31/31**, covering all ten held-out cases.

G1a type review's two HIGH findings and G1 Python review's false GA-only cross-state bonus were corrected and confirmed. G1/G2 tags exist. G2 domain, test and silent-failure reports were filed on frozen copies; no G2 P0/P1 remained. Their assigned P2/P3 findings were reproduced and closed before G3, including rank-3 source wording, truthful empty/unknown states, print selection, response races, offline/Google readiness and real gestures. Scoped T1.6, T2.6, T2.9, T3.2, T3.3a and T3.4b security reviews have no open P0–P3 after their recorded corrections. The T1.7 copy review was ready with notes; its one P3 source-marker lint gap is closed by T1.4b.

The two Codex judging rounds have not started. Every verified open finding from them will be listed here with severity, affected view/viewport and screenshot path when available. No confirmation round will run under founder amendment 5.

## Parked work and founder decisions

No decided feature was cut or hidden from the offline demo. Historical failed branches are superseded by merged repairs. The optional Google switch remains hidden without a configured key or online state; a missing external PMTiles archive produces a visible outline fallback. The runtime exposes four total agent slots, including the lead, despite the founder's requested ceiling of eight.

- **SERTP/CEII (Q2):** the publicly posted SERTP overview has page headers marked `(CEII)` while the spec both acknowledges that overview and says to use nothing marked CEII. The unattended default is the already loaded, cited public overview with no new transcription from marked passages. Founder/Sperry must decide acceptability before public release.
- **People and external services:** team roster, roles, Discord tags and licence are unknown; no person or contact was invented. Claude access and a spend ceiling are not approved, so briefs remain offline templates. A real Google browser key, provider restrictions, CSP host completeness and live roadmap/satellite loading were not tested.
- **Source checks:** Okatie remains inferred until the founder checks a route map. The loaded plans contain no Thomson–Vogtle project by name; adding one requires a verified source. Phone overview zoom 5.5 is a founder acceptance decision.
- **Known nonblocking review notes:** G1a nested Pydantic mutability and exported schema cross-field limits remain documented. Pipeline publication replaces seven artifacts sequentially, so a late failure could leave mixed output; no mismatch was observed in this build.

No Claude-owned file was edited. Proposed changes for Claude after delivery: correct `PROJECT-PROFILE.md`'s description of VERIFY (the actual script writes JSON from compileall and pytest; quick-gate separately repeats shell and audits), and resolve the SPEC/Q2 source-classification tension with the founder. Do not infer consent from this report.

## Lessons and resume

2026-09-26 — Source-backed state geometry must drive the first-view check; a small synthetic rectangle hid a real two-state requirement.

2026-09-26 — Request freshness, URL authority and print selection need separate checks for delayed responses and history changes.

2026-09-26 — Contrast-safe borders, chips and line width preserve timeline emphasis without fading source-backed text or map lines.

2026-09-26 — A strict audit needs equality and just-below scratch proofs; a 0.01 allowance weakened measured thresholds.

The lead session ID is the `thread_id` in the newest `C:\Users\lucia\dev\gridlock-runs\codex\*-lead.jsonl`. On a capacity interruption, resume that session, then read `MISSION.md`, `TRACKER.md`, `tasks/todo.md`, git status/tags and the newest VERIFY summary. At this G3 checkpoint no sub-agent is running; all builder test servers and browsers are stopped. The lead continues until the local `delivered` tag exists.
