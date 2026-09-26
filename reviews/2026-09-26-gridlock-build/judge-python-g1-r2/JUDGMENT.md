# G1 Python confirmation review — round 2

Frozen commit: `09346fa24cddb023b111ffa2da91cba211d80d54`. Mode: read-only code, source-referenced project, test, and committed-artifact inspection; no test suite run. The lead reported VERIFY 139/139, zero failed or skipped.

## Findings

No new CRITICAL or HIGH finding. The round-1 HIGH cross-state misclassification is closed. `pipeline/find_overlaps.py:59-66` now compares both known project states, withholds the 1.5 score multiplier when either state is missing, and applies the cautious Georgia pair note. The `desc-p26` and `sertp-p150-ef263c` project records cite source pages 26 and 150 and both carry `state="GA"`. Their overlap is now `cross_state=false`, score 0.064 (was 0.096), rank 385 (was 323). A genuine SC/GA pair, `desc-p41__sertp-p107-9bc088`, remains cross-state with score 4.8.

Independent inspection of the committed artifacts found 477 overlaps, 43 cross-state flags, 43 in `meta.json`, zero flag/state mismatches, and zero pairs with a missing state. Compared with the frozen round-1 artifact, exactly one flag and score changed; 434 Georgia pair notes and 63 ranks changed as expected, and the top ten IDs did not change. `server/app.py:187-205` filters and serves the corrected flag.

The existing **[MEDIUM] mixed artifact publication risk** at `pipeline/build_all.py:254-255` is unchanged and tracked for later. It did not rise in severity in this repair.

Counts: 0 CRITICAL, 0 HIGH, 1 previously reported MEDIUM, 0 new LOW. **G1 CRITICAL/HIGH remaining: none.**

## Tests checked

- `tests/pipeline/test_cross_state.py:28-75` pins the real GA/GA and SC/GA pairs, score and rank effect, all 477 flags against project states, the 43 count, and a synthetic missing-state pair with no bonus or claim. I read the tests and did not run them.
- `tests/pipeline/test_build_extras.py:56-59` and `tests/pipeline/test_rebuild_regression.py:49-58` expect 43 while preserving stage totals and rebuild checks. The builder reported red `2 failed, 1 passed`, then green `9 passed`, and lane gate 139 suite, 17 shell, 18 audit; these are reported results, not runs from this review.

## Residual risk

The MEDIUM multi-file publication concern remains. This review did not inspect the pending T2.1 geodesic branch; this frozen commit still uses projected distance. The cross-state repair introduced no new CRITICAL/HIGH finding.

Verdict: **ready with notes** for G1.

material improvement still available: no
