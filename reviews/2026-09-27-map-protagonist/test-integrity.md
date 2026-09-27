# Test integrity review

2026-09-27. Scope: test changes from `56c37ca` through the redesign working tree. Reviewed 20 test/support files: 18 existing test modules, the new `test_map_protagonist.py`, and `ui_helpers.py`.

## Verdict

Ready for runtime verification. No deleted test functions, new skips, relaxed audit thresholds, or remaining unintended assertion losses found after the repairs below. This is a test-integrity review; the reviewer wrote the migrations and does not claim independent authorship review.

## Assertion migrations

- More actions now open the actual disclosure before use and close it before reaching covered content. Keyboard journeys assert Search, Filters, More, then the appropriate list or area action; delayed-shell checks still prove disabled Filters is skipped.
- Desktop assertions require the list to remain present beside the right detail pane. Phone height expectations changed from 58dvh to the new 48dvh layout with the original pixel tolerance retained.
- Screen headings changed to `Pair N`; print expectations retain `Overlap #N`. Summary distance includes accuracy, and score keeps its numeric value without the old prefix.
- Sources, savings, evidence, and coordination checks open their native disclosures. All seven original detail blocks, API values, source links, estimate warnings, and hostile-text checks remain covered.
- Brief journeys use Open brief and Back to pair detail. Existing copy, retry, stale-response, navigation cleanup, source, and wording assertions remain intact.
- Map key uses native keyboard expansion. Impact checks retain complete API parity and add keyboard access to the untruncated figure and budget caveat.
- Tour return focus targets More. Projects reachability uses an actual hit test because the menu intentionally overlays the invitation; the actual click, focus result, and initial zoom/invitation checks remain.
- Existing data parity, filters/history, tracker persistence, CSV bytes, print evidence, error recovery, contrast thresholds, target sizes, overflow limits, and layout-shift limits were preserved.

## Coverage restored during review

1. Closing detail and More before the global focus sweep had stopped measuring their controls. The matrix now additionally focuses every visible enabled control while detail, brief, More, and Filters are open, collecting focus-ring contrast results with the existing probe. The original whole-page sweep remains.
2. The capped-distance warning must remain visible before opening evidence. The location test now checks the overview warning first, then retains the expanded evidence and print checks.
3. The matrix audits expanded Filters separately and closes it before map-key/page disclosure actions. This prevents an open dropdown from intercepting clicks while increasing coverage of the filter surface.

The matrix separately gathers detail, expanded brief, expanded Filters, list/page disclosures, and More measurements. It preserves selected-detail text before closing the pane for print validation and adds brief axe, copy, and overflow checks.

## Evidence limits

The reviewer read source and diffs and ran `git diff --check`; no browser, server, or test suite was executed by this reviewer. Runtime passes and isolated failure repetitions belong to the root agent's verification record. The final full-suite run initially collected an earlier matrix revision, so the restored focus and filter coverage requires the root agent's fresh matrix run.

Lesson: when controls move into disclosures or independent panes, preserve both their user navigation path and the audit state in which their focus and content are measured.

material improvement still available: no
