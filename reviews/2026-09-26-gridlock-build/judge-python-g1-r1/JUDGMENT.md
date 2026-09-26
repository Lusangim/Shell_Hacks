# G1 Python gate review — round 1

Frozen commit: `cf95aa70753c04d594c78796b09ce6486fe4bf1e`. Mode: code and committed-artifact inspection; no test suite run.

## Findings

- **[HIGH] A Georgia-only pair is published as cross-state and receives the cross-state score bonus · `pipeline/find_overlaps.py:59-61` ·** The code sets `cross_state` from the presence of Dominion Energy SC in the utility names, although each project's state is already in `feats[i]["properties"]` / `feats[j]["properties"]`. In committed `data/build/projects.geojson`, `desc-p26` (Dominion Energy SC, source page 26) and `sertp-p150-ef263c` (MEAG Power, source page 150) both have `state="GA"`. Their committed overlap `desc-p26__sertp-p150-ef263c` has `cross_state=true`, `score=0.096`, and rank 323. Across the 477 committed overlaps, 44 are flagged cross-state but only 43 have different known states; none of these pairs has a null state. `server/app.py:187-205` serves and filters this flag without recalculation, so the cross-state view contains a Georgia-only opportunity and its rank gets a 1.5 multiplier. The schema validates the field's boolean type but does not compare it to the referenced projects. **Fix:** derive the flag from the two known project states, specify the null-state rule, and add a real-artifact regression asserting this pair is Georgia-only and the count matches state comparisons.
- **[MEDIUM] A failed publish can leave a mixed artifact set · `pipeline/build_all.py:254-255` ·** `build()` stages all files, then replaces `projects.geojson`, `placement_report.csv`, `overlaps.json`, `source_rows.json`, `places.json`, `basemap.json`, and `meta.json` one by one. If a later `os.replace` fails (for example, an artifact is held open on Windows or the destination becomes unwritable), earlier replacements remain while later files are from the previous build. `server/app.py:61-81` loads these files as one logical dataset; its ID checks may catch changed IDs but do not prove that unchanged IDs' project attributes, pair scores, and metadata come from the same build. **Fix:** publish a validated versioned artifact directory through one pointer/swap, or use a manifest hash and refuse a mixed set at startup; add a failure-injection test at a later replacement.

Counts: 0 CRITICAL, 1 HIGH, 1 MEDIUM, 0 LOW.

## Tests checked

- `tests/pipeline/test_build_extras.py` pins counts and tests production loading; `test_rebuild_regression.py` verifies two successful rebuilds are byte-identical. Neither checks failed publication or state-derived cross-state truth.
- `tests/api/test_core.py` covers response models, filters, invalid query responses, host restriction, and startup rejection of invalid artifacts using synthetic fixtures. The `cross_state=true` fixture is self-consistent, so it does not expose the production misclassification.
- `tests/pipeline/test_fields.py`, `test_completeness.py`, `test_ids.py`, and `test_source_hash.py` cover sampled printed fields, all source-row markers, citations/IDs, and stable input hashes. I read these checks; I did not run them. The lead reports G1 VERIFY 135/135, zero skipped.

## Residual risk

The current overlap script still measures distance in EPSG:5070 (`pipeline/find_overlaps.py:6-7,23-25,53`) and uses inclusive band thresholds; the brief says the separate DATA T2.1 branch changes this to geodesic nearest-point distances. This frozen review cannot verify that branch. No new finding is charged for that already assigned correction.

Verdict: **not ready** until the HIGH finding is corrected and verified. The medium finding should be fixed or explicitly tracked before delivery.

material improvement still available: yes

