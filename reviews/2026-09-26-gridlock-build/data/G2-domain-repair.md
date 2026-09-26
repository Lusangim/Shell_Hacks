# DATA — G2 domain wording repair (JDOMAIN-02)

2026-09-26. Branch `wt/data-g2-domain`, base `1b0288e`. Main and lane HEAD were equal immediately before the lane gate. All commands ran in this lane worktree. Tests/build used port 8796, AI off and Google off; the quick gate owns its documented +3000/+6000 smoke/audit ports.

## Task and files

Qualify rank 3's named full-line endpoint with the source's actual 6.7-mile Goshen (Savannah)–Georgia Pacific (Rincon) work section. Preserve the Deerfield location caveat and source pages. Shared-endpoint opportunities now ask users to verify work locations before reviewing possible coordination, with shared assets still unverified.

- `pipeline/overlap_geometry.py`: rank-3 explanation and generic shared-endpoint opportunity.
- `data/build/overlaps.json`: offline regeneration; 28 `can_share` values and one `touch_detail` value changed.
- `docs/METHODOLOGY.md`: matching Savannah table evidence and cautious review prose.
- `tests/pipeline/test_bands_touch.py`: source-section, reversed-input, opportunity and built-artifact checks.
- `tests/api/test_detail_export.py`: rank 1/3 artifact-detail-CSV evidence parity.
- `tests/e2e/test_export.py`: rank 1/3 browser detail-print evidence/opportunity parity and source-page links.
- This report.

The lead explicitly extended ownership to the two API/e2e test files. No product API/export code, contract, schema, geometry, project source field or other generated artifact changed; `meta.json` was byte-stable and is not staged.

## Acceptance and RED/GREEN evidence

| Acceptance | Check and RED evidence | GREEN evidence |
| --- | --- | --- |
| Identify rank 3's exact work section, distinguish full named line endpoint, retain Deerfield and pages 41/111 | `test_goshen_section_is_distinct_from_named_mcintosh_endpoint[False/True]`: both failed because `Goshen (Savannah)–Georgia Pacific (Rincon)` was absent | Both pass with section, 6.7-mile length, full-line distinction, explicit lack of established McIntosh work, Deerfield and page assertions |
| Ranks 1/3 and all shared-endpoint opportunities require work-location verification; assets stay unverified | `test_shared_endpoint_opportunity_requires_work_location_verification` and strengthened built-pair check failed: expected `Verify work locations`, actual `Coordinate work at the named endpoint; shared assets unverified.` | Generic function and built-pair checks pass; 28 shared-endpoint artifact opportunities carry the cautious wording |
| Detail, CSV and print use regenerated artifact evidence | Two new API cases and two browser cases failed on missing `Verify work locations` before source changes | API detail equals its artifact; CSV `Why they touch` equals artifact evidence; browser detail and selected print equal API evidence/opportunity and preserve page links |
| Preserve classification, distance/band/rank, costs, geometry and verbatim descriptions | Existing artifact is the comparison baseline; no new source transcription beyond the judgment's section identification | Read-only comparison of every before/after overlap allowed only `can_share` and `touch_detail`; only rank 3 changed the latter. `projects.geojson` and all other generated files have no Git diff |
| Methodology matches source-backed evidence | Old rank-3 table repeated the incomplete explanation | Read-only check found exact rank 1/3 artifact `touch_detail` strings in the methodology; new prose distinguishes full-line endpoint from scheduled section |
| Offline deterministic rebuild, unchanged counts and top ten | Existing regression check preserved in full | `test_offline_rebuild_preserves_counts_pairs_and_bytes` passes after two rebuilds, asserting 481 source rows, 230 kept, 181 placed, 489 overlaps, 43 cross-state, byte identity and exact top-ten project IDs/order |

RED commands/results:

- `pytest tests/pipeline/test_bands_touch.py -q`: **4 failed, 16 passed**. Failures were the two section cases, generic opportunity and built-pair opportunity.
- `pytest tests/api/test_detail_export.py tests/e2e/test_export.py -q -k 'mcintosh_evidence or mcintosh_detail_and_print'`: **4 failed, 28 deselected**, all due to the old endpoint imperative.

GREEN commands/results:

- `python -m pipeline.build_all` through `GRIDLOCK_PY`: exit 0, offline; counts **481 source / 230 kept / 181 placed / 489 overlaps / 43 cross-state**.
- `pytest tests/pipeline/test_bands_touch.py tests/pipeline/test_rebuild_regression.py tests/api/test_detail_export.py tests/e2e/test_export.py -q`: **54 passed in 39.46s**, zero failed/skipped.
- Two additional runs of `pytest tests/e2e/test_export.py -q -k mcintosh_detail_and_print`: **2 passed, 10 deselected** each (5.21s, 5.44s). New browser cases each passed three consecutive GREEN runs in total.
- Read-only complete overlap comparison: **28 opportunity strings + 1 evidence string changed; every other value and top-ten ID/order preserved**. Both Savannah table explanations exactly match artifacts.
- `git diff --check`: exit 0.
- `scripts/quick-gate.ps1 -Repo <lane worktree>`: **QUICK GATE PASS**, exit 0. Compile succeeded; full suite **351 passed in 375.00s**, shell smoke **19 passed in 23.45s**, audits **18 passed in 42.99s**; zero failures/skips. Gate execution exceeded its nominal five-minute target; no check was omitted.

## Deviations, other lanes and questions

No implementation deviations. API/e2e checks were added with lead authorization. CSV already exports source evidence in `Why they touch`; it has no opportunity column, so its existing layout is preserved. No For API/WEB/WEB-2 patch is needed.

An untracked `debug.log` appeared during browser tests. The lead directed that it remain untracked and not be removed or staged. All fixture-owned servers/browser sessions ended with their test runs; the final port check confirmed the three gate ports are free.

Q2 classification remains the founder's decision. This repair neither reclassifies source material nor claims clearance. No new section geometry, map verification, source passage or physical McIntosh work location was inferred.

2026-09-26 lesson: Shared named endpoints need explicit work-section limits before they can support a coordination action.
