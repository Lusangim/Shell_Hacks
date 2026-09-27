# Final inspected review — 2026-09-27

**Verdict: ready, pending the lead's test gate.** No unresolved blocking defects were found in the inspected product.

Scope: accumulated presentation changes from `56c37ca`, milestones `463d91b`, `ecafe33`, `f192509`, and the final uncommitted phone layout and keyboard repairs. Reviewed shell disclosures and focus order, retained feature hooks, pair detail and brief presentation, marker lifecycle, geometry helper, responsive CSS, and changed tests.

## Findings closed

- **HIGH — Filters keyboard entrance:** confirmed the actual `web/js/shell.js:46` repair exempts More while focus traverses Filters → More → filter panel. Activating More still closes Filters. `tests/e2e/test_map_protagonist.py:50` exercises Enter → Tab → Tab → first filter control → Escape at 390 and 1440 px, asserting visible controls and restored Filters focus.
- **MEDIUM — Impact popover obscured subsequent keyboard targets:** confirmed the actual shell handler closes the disclosure on outside focus or pointer interaction. Escape closes it, restores summary focus, and stops propagation to underlying area controls.
- Earlier More Tab-exit, project Back focus, and covered phone/tablet map-focus findings were also resolved in the inspected code.

## Evidence and limits

Inspected screenshots in `gridlock-runs/codex/ (outside the repository): `:

- `redesign-m3-1440-light-detail.png`
- `redesign-final-320-light.png`, `redesign-final-320-light-detail.png`, `redesign-final-320-dark.png`
- `redesign-final-390-light.png` (known pre-final wordmark-hiding snapshot; final rule reviewed in CSS)
- `redesign-final-700-light.png`
- `redesign-final-701-light-detail.png`
- `redesign-final-1099-dark-detail.png`

The inspected layouts support the requested desktop panes, tablet sheet, phone list and full-height detail. Source/evidence blocks, tracker storage logic, brief loading/retry logic and export content remain preserved. No test weakening was identified in this review; separate audit-restoration work and final runtime results remain the lead's verification responsibility.

This reviewer ran **no tests, browsers or servers**, and changed no product files. Contrast, layout-shift measurements and full behavioral certification depend on the lead's test gate. The geometry implementation follows this reviewer's earlier proposal, so its review is a confirmation rather than an independent second implementation review.

## Late repair addendum

Re-read the actual late changes to `web/js/map.js`, `web/index.html`, and `web/css/protagonist.css` after the lead's runtime findings. **Verdict remains ready, pending runtime verification.**

- The per-refresh palette reads the current root utility/casing tokens before SVG writes. Existing callers can omit it and retain the prior token lookup. `highlightPair` still restyles every project and casing, including unselected features, so removing the preceding duplicate project restyle does not omit that work. Styling formulas, geometry, ranks and source data are unchanged.
- The phone highlighted-pair control retains its original accessible name and action. The revised positions and narrow-screen label address its reported collision with the timeline; actual hit testing and viewport behavior remain the lead's responsibility.
- No additional functional blocker was identified by static inspection. The reported test totals and timing/hit-test outcomes were not independently executed or verified by this reviewer.

### Label-placement performance follow-up

Inspected the actual `preserveLabels` change in `map.js` and its timeline caller. **Ready, pending the affected runtime gate.** Normal selection still defaults to full placement. Style-only refreshes skip placement only when selected layer count and identities match the last placed set; replacement layers and changed selections still place labels. Map movement, resize and sheet refresh paths retain their existing placement calls. Theme refresh still recolours all project/casing layers, halos and the rank marker, while tooltip colours follow CSS tokens; inspected tooltip typography does not vary by theme. No additional blocker was identified. The reported 61.9 ms measurement was supplied by the lead, not measured by this reviewer.

material improvement still available: no
