# GridLock delivery report

**In progress — G4 judged corrections passed, 2026-09-26 20:39 EDT.** Main VERIFY passed on `39eecd9` with 716 passed, zero failed and zero skipped against baseline 716; tag `g4` exists. All nine unique P2 findings from the founder-capped two judging rounds have corrections merged and tested. Two P3 UI notes remain for Claude's final review. README startup validation is complete; sanitizer and final delivery remain.

## What works now

- The local app shows a modern offline map of Georgia and South Carolina, 489 ranked public-plan overlaps, source-backed project and pair details, search, filters, timeline, area explorer, CSV, Letter print and a guided tour. All 24 audit scene combinations passed at 1440/390 px in light/dark themes.
- The data pipeline keeps 230 of 481 input rows, places 181 projects, explains 128 unplaced rows, and records 43 cross-state overlaps. Unknown and inferred locations stay labelled; costs and savings retain their basis and caveats.
- Briefs are graded offline templates by default. The 30-case real-ID evaluation has 20 development and 10 held-out cases; all 30 selected templates and all 489 built-overlap templates passed the grader. No real Claude call or spend occurred.
- The local PMTiles map is optional on a fresh clone: when its separate archive is absent, the app visibly falls back to state outlines. Optional Google map controls require a configured browser key and an online browser; every build test and server run kept Google off and never opened the real key.
- To run: `SETUP.cmd -Offline` with the prepared local environment, then `START.cmd -Port 8770 -NoBrowser`; to verify, set `GRIDLOCK_GOOGLE=off` and run `VERIFY.cmd` with a free `GRIDLOCK_TEST_PORT`. The rewritten README describes the current app. Offline setup passed; START served `/` and 489 overlaps with HTTP 200, then port 8770 was confirmed free.

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
| G3 | Feature freeze: all decided features are demoable offline; full matrix and held-out evaluation green; `g3` tag points to `8d83ad0`. |
| T4.1–T4.2 | Complete: six fresh judges on frozen `g3`, two rounds as capped by the founder; 0 P0/P1, nine unique P2 and two P3 findings. Judgments and essential screenshots are committed under `judge-*/`. |
| T4.3, G4 | Complete. WEB `8f70b2b`, WEB-2 `fa008a2` and API `ed82d4d` merged after RED/GREEN checks and lane gates; API's final synced gate passed 716 suite + 19 shell + 99 audits, lead reran 33 focused cases, task-local security review found zero P0–P3. Main VERIFY 716/716, tag `g4` on `39eecd9`. T4.4 confirmation skipped by founder. |
| D.1 | Sanitizer on the delivery candidate is pending; no files have been pushed or published. |
| D.2 | Complete: README reflects the delivered app and 716-test baseline; offline setup passed, START served `/` and 489 overlaps with HTTP 200 on 8770 and stopped cleanly, and G4 VERIFY passed. |
| D.3 | Final delivery report, exact-commit sanitizer and `delivered` tag remain. |
| F1–F7, T5.0–T5.5, H0–H9 | Claude and founder work after Codex delivery; not started by this lead. Nothing was pushed, deployed, submitted, sent or purchased. |

## Verification and judgments

G4 VERIFY summary: `C:\Users\lucia\dev\gridlock-runs\verify\20260926-201457-009\summary.json` — **exit 0, 716 passed, 0 failed, 0 skipped, baseline 716**, tested main commit `39eecd9`. Pytest reported 32 `record_property`/xunit2 warnings; assertions passed. The synced API lane quick gate passed **716 suite + 19 shell + 99 audits**. The lead independently reran 33 focused API cases after its branch commit. G3 VERIFY remains at `C:\Users\lucia\dev\gridlock-runs\verify\20260926-165341-069\summary.json` (674/674); the empty 16:44 G3 folder was superseded by that completed run. The manifest and selected-template evaluation passed **31/31**, covering all ten held-out cases.

G1a type review's two HIGH findings and G1 Python review's false GA-only cross-state bonus were corrected and confirmed. G1/G2 tags exist. G2 domain, test and silent-failure reports were filed on frozen copies; no G2 P0/P1 remained. Their assigned P2/P3 findings were reproduced and closed before G3, including rank-3 source wording, truthful empty/unknown states, print selection, response races, offline/Google readiness and real gestures. Scoped T1.6, T2.6, T2.9, T3.2, T3.3a and T3.4b security reviews have no open P0–P3 after their recorded corrections. The T1.7 copy review was ready with notes; its one P3 source-marker lint gap is closed by T1.4b.

Both Codex judging rounds ran against the same frozen `g3` commit. The domain judge independently matched all 489 ranks/savings results, five distances and the top-ten source pages (7/10). First-week user/design reached the cold task in 52.6 seconds/five clicks (7/10 each). Reliability/security ran 242 focused tests plus 36 independent probes with no verified security defect (7/10 and 8/10). Business/hackathon fit demonstrated the challenge path and 20 focused tests (7.5/10). Copy scanned 719 detail views and 3,394 bullet blocks (ready with notes, 7.5/10). Accessibility exercised six keyboard size/theme journeys (not ready, 7/10; screen-reader wording inferred from DOM, not heard). The six original judgments are filed under `judge-*/JUDGMENT.md`; no confirmation round will run under founder amendment 5.

| G3 judging finding · G4 status | Severity · owner | View / viewport · essential screenshot |
|---|---|---|
| JDOMAIN-01 inferred utility shown as stated · **fixed** | P2 · WEB/WEB-2/API | Rank/pair/project/map/print/CSV/Template, 1440 and 390 · [inferred utility](judge-domain-r1/inferred-utility-1440.png) |
| JDOMAIN-02 stored cost discrepancies absent from project summary · **fixed** | P2 · WEB | Project/pair/selected print, 1440 and 390 · [desktop](judge-domain-r1/flagged-cost-1440.png), [phone](judge-domain-r1/flagged-cost-390.png) |
| JUD-01 first-visit invitation intercepts zoom clicks · **fixed** | P2 · WEB-2 | Default, 1440/768/390 light and dark · [desktop](judge-user-design-r1/first-visit-1440-light.png), [phone](judge-user-design-r1/first-visit-390-light.png) |
| JUD-02 fresh tour omits built area and brief steps · **fixed** | P2 · WEB-2 | Tour, all six viewport/theme combinations · [step 9](judge-user-design-r1/tour-desktop-9.png), [step 10](judge-user-design-r1/tour-desktop-10.png) |
| JREL-01 collapsed phone search hides no-match/error status (also JA11Y-02) · **fixed** | P2 · WEB | Search, 390×844 · [empty](judge-reliability-r1/JREL-01-empty-390x844.png), [503](judge-reliability-r1/JREL-01-503-390x844.png) |
| JBUS-01 CSV savings ranges omit estimate assumptions and caveat · **fixed** | P2 · API | CSV download (489 rows); sibling brief/print at 768/1440 · [brief](judge-business-r2/05-brief-768.png), [print](judge-business-r2/06-print-1440.png) |
| JCOPY-01 filtered Projects falsely says no projects loaded · **fixed** | P2 · WEB | `?year_min=2199` Projects, 1440/390 · [desktop](judge-copy-r2/1440-empty-projects.png), [phone](judge-copy-r2/390-empty-projects.png) |
| JCOPY-02 duplicate search choices show internal project IDs · **fixed** | P2 · WEB-2 | Search, 1440/390 · [desktop](judge-copy-r2/1440-duplicate-selected.png), [phone](judge-copy-r2/390-duplicate-selected.png); DOM values in [evidence](judge-copy-r2/focused-evidence.json) |
| JA11Y-01 expanded phone sheet covers keyboard-focused timeline · **fixed** | P2 · WEB | Timeline with expanded pair/area sheet, 390 light/dark · [light](judge-a11y-r2/390-light-expanded-timeline.png), [dark](judge-a11y-r2/390-dark-expanded-timeline.png) |
| JUD-03 selected map labels wrap into narrow columns · **open** | P3 · WEB | Selected pair map, 1440 light/dark · [selected map](judge-user-design-r1/top-pair-stable-light.png) |
| JA11Y-03 successful brief retry loses keyboard focus · **open** | P3 · WEB | Brief error/retry, 1440 light · [focus lost](judge-a11y-r2/1440-light-brief-retry-focus-lost.png) |

All nine P2s are fixed in T4.3, with task reports and RED/GREEN evidence under `web-t43/`, `web2-t43/` and `api-t43/`. The two P3s remain open for Claude's post-delivery UI pass. Duplicated findings are counted once. A fresh task-local security read found zero P0–P3 on the correction diff; see `T4.3-security.md`. No third Codex judging round was run.

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

2026-09-26 — Longer attribution text can push an otherwise valid brief across its word limit; run the real selected-template evaluation after a wording correction.

2026-09-26 — CSV recipients need the dated assumption, basis and caveat next to the amount, even when the browser explains them.

The lead session ID is the `thread_id` in the newest `C:\Users\lucia\dev\gridlock-runs\codex\*-lead.jsonl`. On a capacity interruption, resume that session, then read `MISSION.md`, `TRACKER.md`, `tasks/todo.md`, git status/tags and the newest VERIFY summary. At this G4 checkpoint no sub-agent is running; builder and VERIFY test servers and browsers are stopped. The lead continues through D.1–D.3 until the local `delivered` tag exists.
