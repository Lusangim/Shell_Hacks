# DATA G1 repair — cross-state truth

Task: Close the G1 Python review HIGH finding by deriving cross-state from both projects' sourced state fields, rebuilding the overlap artifacts, and pinning the observed score/rank effects.

## Files changed

- `pipeline/find_overlaps.py`
- `data/build/overlaps.json`, `data/build/meta.json`
- `tests/pipeline/test_cross_state.py`
- `tests/pipeline/test_build_extras.py`, `tests/pipeline/test_rebuild_regression.py`
- This report

## Acceptance evidence

1. **Real GA/GA pair, true SC/GA pair, score multiplier and note:** New `tests/pipeline/test_cross_state.py` ran RED before the code change: `2 failed, 1 passed`; `desc-p26__sertp-p150-ef263c` asserted `cross_state is False` but got `True`. The genuine `desc-p41__sertp-p107-9bc088` passed. After the change, the affected suite ran GREEN: `9 passed in 12.43s`. The GA/GA pair is now `cross_state=false`, score 0.064 (was 0.096), rank 385 (was 323), and has the SPEC's cautious Georgia ITS note; the SC/GA pair remains cross-state with score 4.8 and no note. The synthetic null-state test verifies no cross-state claim or 1.5 bonus when one state is unknown.
2. **All published pairs and count:** The RED all-pairs check identified `desc-p26__sertp-p150-ef263c`: `assert True is False`. After rebuild, every pair flag agrees with the two project states; cross-state count is 43 (was 44). All 434 GA/GA pairs carry the cautious note; the 43 SC/GA pairs have no note.
3. **Stage counts, rank and top ten:** Rebuild preserved 481 source rows, 230 kept projects, 181 placed projects, and 477 overlaps. The two previous exact-count checks failed on `assert 43 == 44` after the code correction; updating them to the verified 43 made the affected suite green. The existing `TOP_TEN` regression passes unchanged, and the first ten IDs were inspected against the pre-change list.
4. **Full lane gate:** `$env:GRIDLOCK_TEST_PORT='8777'; & 'scripts/quick-gate.ps1'` passed: 139 suite tests, 17 shell tests, 18 audit tests, `QUICK GATE PASS`. `git diff --check` was clean.

Declared deviations: None. The G1 review's separate MEDIUM atomic multi-file publication concern was not changed under this brief.

For DATA patches: None.

Open questions: None for this repair. With a missing state, the new rule conservatively sets `cross_state=false`; none of the 477 published pairs has a missing state.

2026-09-26 — Derive pair geography from the two project records; utility branding is an unreliable proxy for state.
