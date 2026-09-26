# G2 silent-failure judgment

Frozen HEAD: `d355f75c05e3d3cd563ed955949a70219a4d4159` (confirmed). Reviewed 2026-09-26, 12:45–12:49 EDT. Independent reviewer; no product, test, or artifact changes.

Mode: code review plus read-only Python artifact/count queries. No browser, server, test suite, pipeline build, network request, or credential access was run by this reviewer. Python used the assigned interpreter with `-B`; AI and Google were off and the assigned port was 8783.

The supplied VERIFY summary reports exit 0, **344 passed / 0 failed / 0 skipped**, baseline 344, at `cfc300e`. Its difference from the reviewed HEAD consists only of `DELIVERY.md`, `TRACKER.md`, and `tasks/todo.md`; the tested product and tests match this frozen copy. This is supplied gate evidence, not a suite rerun by this reviewer.

## New findings

### [P2 / MEDIUM] Filtered or unlocated projects are declared to have no nearby overlap

Locations: `web/js/project-detail.js:134–136`, sibling `web/js/list.js:87–90`, and aggregate `web/js/app.js:95–99`. Caller: `web/js/app.js:77–82` passes the filtered projects and pairs into the project view.

Concrete trigger: filter utilities to **Dominion Energy SC**, open Projects, then open `desc-p41` (the Okatie–McIntosh project). The read-only API function query finds **14** pairs for that project without filters and **0** under the Dominion-only filter. The project remains in the filtered project collection, but `renderDetail` displays **“This project has no overlap within 40 km.”** The map-click sibling makes the same claim from the same filtered pair collection. Filtering both members is correct; describing a filtered absence as an unconditional geographic absence is false.

A second trigger is opening `desc-p3`: the committed feature has `geometry: null` and `accuracy: unknown`, yet the same empty-related-pairs branch asserts no overlap within 40 km. The initial aggregate makes the same overclaim: the displayed **97** unpaired projects comprise **48 placed projects with no computed pair + 49 projects whose location is unknown**. `pipeline/build_all.py:236` correctly counts absent pair membership; the UI incorrectly describes all of them as assessed geographic negatives.

Correction: distinguish “no pairs under current filters” from “location unknown; proximity cannot be assessed.” Describe the aggregate as projects not represented in computed pairs, with the unknown-location count visible, or split placed/unlocated counts. Preserve the frozen count contract and source geometry. Apply the wording to the project panel and map-click status together.

Acceptance checks:

- Dominion-only filtering followed by opening `desc-p41` says no pairs match the filters; clearing filters restores its 14 related pairs.
- `desc-p3` says its unknown location prevents proximity assessment and never asserts no overlap within 40 km.
- The default aggregate distinguishes 48 placed unpaired projects and 49 unknown-location projects, or uses wording that explicitly represents absence from computed pairs without claiming all 97 were geographically assessed.
- Existing `desc-p1` coverage remains truthful for its placed, unpaired case. Extend `tests/e2e/test_project_detail.py` and the map-click path; do not remove its source/cost/keyboard assertions.

### [P2 / MEDIUM] Detail restored from a link or history does not restore the pair used by print

Locations: `web/js/overlap-detail.js:129–160` and `169–178`; callers `web/js/app.js:83–86`, `web/js/list.js:97–104`; print consumers `web/js/export.js:198–216` and `64–70`.

Concrete fresh-link trigger: open `/?band=lt_40km#overlap=desc-p41__sertp-p107-9bc088`. The named pair is a valid touching pair, so it is absent from the filtered list. `restorePairSelection` returns false before setting `state.selectedOverlapId`. The detail request succeeds and displays the pair outside current filters, but `open` never writes the selected ID. Print reads the still-null ID, skips the detail fetch, and emits **“No overlap selected. Choose a ranked pair to include its detail.”** This omits the visibly opened pair.

Concrete history trigger: click pair A, use Back to ranked overlaps, click pair B, then use browser Back twice. The hash listener fetches and renders A, while `state.selectedOverlapId` remains B because only list selection/restoration writes that state. Print therefore fetches and prints **B while A is the current visible detail**. The existing history test verifies URL/panel visibility, but not selected identity or report content.

These outcomes are traced through the full callers and consumers; they were not exercised in a browser in this read-only review.

Correction: make successful detail/link/history restoration update the canonical selected-pair identity and applicable highlight state, with request sequencing so stale responses cannot replace the current selection. Invalid/stale links must not silently retain a different pair as though it were the opened detail. Ensure print and filter-status consumers use the same identity as the visible detail.

Acceptance checks:

- Fresh filtered-out deep link above prints that pair's two projects and ID, marked outside current filters; it does not print “No overlap selected.”
- A → list → B → browser Back twice restores A in the visible detail, selected state, and print output. Forward restores B consistently.
- Rapid A/B navigation followed by delayed response completion preserves the latest pair; invalid/stale links do not print an unrelated previously selected pair as the current detail.
- Extend existing history/detail/export tests while retaining their error, injection, filter, and race assertions.

New finding totals: **P0 0 · P1 0 · P2 2 · P3 0**. Both have concrete source/data triggers and false visible claims. No CRITICAL/HIGH finding was identified in this sweep.

## Stage-count reconciliation

The read-only extraction functions parsed both committed PDFs in memory; they wrote no CSV. CSV, disposition IDs, placement report, GeoJSON, overlaps and metadata were then counted independently. Every source ID appears exactly once in the dispositions, and kept IDs equal project-feature IDs.

| Stage / metadata field | Independent result | Reconciliation |
|---|---:|---|
| PDF project markers | 513 | 54 DESC + 459 SERTP |
| Explicit pre-CSV exclusions | 32 | TVA “In- Service” entries on pp. 171–181; recorded extraction exclusions |
| `source_rows` | 481 | 54 DESC CSV + 427 SERTP CSV; 513 − 32 |
| `dropped_outside_selected_balancing_area` | 101 | Disposition count |
| `placement_candidates` | 380 | 481 − 101; placement report rows |
| `dropped_outside_ga_sc_footprint` | 69 | Disposition count |
| `dropped_unlocated_outside_selected_area` | 77 | Disposition count |
| `dropped_powersouth_excluded` | 4 | Disposition count |
| `kept` | 230 | 481 − 101 − 69 − 77 − 4; unique feature IDs |
| `placed` | 181 | Non-null geometries |
| `kept_unmapped` | 49 | Null geometries; 230 − 181 |
| `dropped_unmapped` | 79 | 77 unprefixed Southern + 2 excluded PowerSouth |
| `unmapped` / `unmapped_count` | 128 | 49 kept + 79 dropped; unknown rows in placement report |
| `unmapped_reasons` | 49 / 77 / 2 | `kept_not_located` / `unprefixed_southern_not_located` / `powersouth_not_located_excluded`; exact metadata match |
| Accuracy | 42 exact / 139 approximate / 49 unknown | Sum 230; exact metadata match |
| `overlaps` | 489 | Unique committed pairs |
| `cross_state` | 43 | True flags counted in pairs |
| Band counts | 62 / 3 / 19 / 405 | touching / under 1.6 / under 8 / under 40 km; sum 489 |
| `no_overlap_count` | 97 | 48 placed unpaired + 49 unlocated; correct membership count, misleading UI wording above |
| `places` | 1,150 | Committed Census place rows |
| `state_outlines` | 2 | Basemap outline features |
| `city_labels` | 801 | Basemap label features |
| `stale_brief_count` | 0 | G2 has no merged brief-serving/cache implementation; all 489 pair statuses are `none` |

Utility counts also match exactly: Dalton Utilities 3; Dominion Energy SC 54; Georgia ITS (joint) 3; Georgia Power 91; Georgia Transmission Corp. 66; MEAG Power 13. Sum 230.

Savings statuses are 201 range, 214 timing-too-far, 74 no-cost (sum 489). Non-range outputs retain null bounds and explanatory bases. Two source date strings remain visible verbatim with null derived years: `desc-p1` `04/31/26` and `desc-p5` `06/31/2026`; no fabricated date was substituted.

## Sweep observations and existing items

- Required API artifacts fail startup on missing/invalid JSON; request failures return explicit non-200 error bodies. The frontend checks response status before treating results as data and guards filtered/detail/search races.
- Unknown geometry is excluded from distance calculations, retained in the project collection, and listed with an explanation. No empty geometry was converted into a zero-distance touching pair in the reviewed artifacts.
- Savings load dated team assumptions, preserve printed plan totals and cost flags, and return explicit null-bound statuses when timing/cost information does not support a range.
- Map configuration/archive failures are presented through the basemap status and outline fallback. Export failures disable or visibly reject the requested report; filter revision and selection-change guards prevent completed stale export requests from reporting success. The separate link/history identity gap is finding 2.
- The brief cache/template implementation is held outside this frozen G2 commit. It cannot be independently judged here; no brief or generation control is exposed, and pair statuses remain `none`. The current area control draws and labels a 40 km circle; it does not claim an unimplemented area result count.
- Known T1.7 wording issue, not newly discovered here: `web/js/overlap-detail.js:72` says “possibly touching” for every approximate pair. The exact committed input `desc-p41__sertp-p110-2ad81c` is `lt_40km`, **27.537598849227063 km**, approximate. `web/js/export.js:80–83` already restricts that wording to the touching band. Keep the existing WEB correction in scope.
- Known publication MEDIUM, not a duplicate new finding: `pipeline/build_all.py:256–257` replaces seven files sequentially. Staging validates before replacement, but a late replacement failure can still leave mixed artifacts. The supplied delivery report already records this limitation.
- The source-classification question in SPEC/Q2 remains a founder decision. This review did not reinterpret the source or change classification policy.
- Read-only sweep included `pipeline/`, `server/`, `web/js/`, and `scripts/`. The optional network refresh script was read but never executed. No live online/Google behavior or Phase 3 held branch is certified by this judgment.

2026-09-26 — A reconciled count of absent computed pairs does not establish geographic absence when filters or unknown geometry excluded evidence.

material improvement still available: yes
