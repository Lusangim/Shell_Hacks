# T1.7 independent copy judgment

2026-09-26, completed after the 14:30 EDT clock check. Frozen HEAD verified as `36bd32ef4a159f521490899fc02a2b85939bdca8`; worktree `judge-copy-t17-r1`; port 8785. I did not build these surfaces.

**Verdict: ready with notes.** No concrete authored-copy violation found in the reviewed output. Counts: P0 0, P1 0, P2 0, P3 1. The note below concerns future lint coverage, not an incorrect sentence currently shown to a planner.

## Finding

**[P3] Authored summary prose is exempted from the own-copy lint** · `web/js/overlap-detail.js:59`–64, `web/js/project-detail.js:40`, `web/js/brief.js:14`–16; exclusion at `tests/e2e/audits/checks.py:64` and `tests/e2e/test_readable_details.py:167` · Owner: WEB (coordinate test changes with LEAD).

The current McIntosh estimate sentence, “Based on the stated plan costs shown above; unstated partner costs are excluded.”, is authored copy but receives `data-src="estimate_scope"`. The generic block answer and brief bullet helpers likewise attach source markers to authored sentences. Both own-copy lint implementations exclude anything beneath a `data-src` element. Consequently, their green result does not establish that these sentences meet the own-copy rules.

I reproduced this with a browser-only mutation: replacing the estimate-scope sentence with `seamless` returned `{'own': [], 'visible': []}` from the existing `TEXT_LINT_JS`; removing only its source marker returned `{'own': ['seamless'], 'visible': []}`. No product file was modified. The original sentence itself is appropriate, which is why this is P3 rather than a material copy defect.

Suggested fix: distinguish authored text from verbatim source text, or explicitly include authored summary fields in the lint. Preserve exemptions for actual source names/descriptions and their punctuation. Acceptance check: a forbidden word or authored dash in an estimate/brief summary is detected; a verbatim source project name containing an en dash remains exempt.

## What is good and what was traced

- Project, pair, savings and brief blocks put their answer ahead of short bullets and disclosures. Raw source descriptions remain available, and print opens the disclosures automatically. The changes to old assertions replace IDs/enums with their intended readable equivalents; the reviewed diffs retain factual checks and add meaningful selection/race coverage.
- The real `desc-p41__sertp-p107-9bc088` API response and live browser view agree: rank 1; 2028 schedules (`12/31/2028` and `2028` preserved); Dominion plan cost $5,376,418; Georgia Power cost not stated; $54,000 to $161,000 possible saving explicitly labelled estimate; dated team assumption of 1% to 3%; sharing not verified. Independently applying those percentages and rounding to $1,000 gives the displayed bounds.
- Citations remain SCRTP Planned Facilities 2026-2030 $2M & Above, p. 41, and SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. 107. The API preserves the source description of Deerfield construction and the distinction between the tie-line endpoint and the actual work location. The UI retains approximate location and possibly-touching wording. The p. 111 sibling also retains the Goshen–Georgia Pacific work-limit caution in detail and print.
- Unknown location, placed-with-no-pair, and filtered-with-no-pair states use different explanations. A failed or stale link cannot retain a prior selected pair in the checked paths. The no-estimate reasons for missing costs, excessive timing gaps, and unknown years are explicit in the renderers; real no-cost brief behavior was exercised.
- All 489 printed table rows preserve API rank order, names, utilities, exact distances, bands and source document/pages. Selected source descriptions and savings evidence are visible in print media; planner coordination-status fields remain blank. Human-readable reports remove internal references while CSV remains an interchange artifact.
- Brief template/cached/stale/none labels and failures are explicit. Cached status says “AI-drafted from public plan data. Check before use.”; other cases display “Template”. Retry stays tied to the selected pair. Contacts are restricted to the pair's organizations. Copy includes the visible assumption/date, uncertainty and source links.

## Verification I ran

All test commands set `GRIDLOCK_TEST_PORT=8785`, `GRIDLOCK_AI=off`, `GRIDLOCK_GOOGLE=off`, the installed Playwright browser path, and `PYTHONDONTWRITEBYTECODE=1`; Python was invoked only through `& $env:GRIDLOCK_PY`.

Focused command:

```text
& $env:GRIDLOCK_PY -m pytest -q -p no:cacheprovider tests/e2e/test_readable_details.py tests/e2e/test_brief.py tests/e2e/test_export.py::test_print_readable_selected_and_full_ranked_evidence tests/e2e/test_export.py::test_approximate_distant_pair_print_does_not_claim_possibly_touching tests/e2e/test_export.py::test_mcintosh_detail_and_print_preserve_work_location_limits tests/e2e/audits/test_quick_gate.py::test_authored_color_and_visible_copy_lint -k 'not answer_first_blocks'
```

Result: **31 passed, 2 deselected in 138.26 seconds; no failed or skipped checks.** The deselected checks are the two screenshot-writing answer-first cases; they were not changed or weakened. The passing run includes the complete 719-view forbidden-pattern scan (230 projects plus 489 pairs), all four approximate distance bands, filtered/unknown/placed states, link history and errors, 17 brief tests, five print tests, and the default copy lint.

Separately ran a direct local API/browser trace of the real McIntosh record and the browser-only lint probe above. The first lint-probe attempt encountered `ERR_CONNECTION_REFUSED` because the completed pytest fixture had stopped its server; reran once using the existing fixture's own isolated lifecycle, and the probe passed. Its server and browser were closed in `finally` blocks. The direct trace and pytest browsers were also closed. No persistent server was started.

## Read versus not rerun

Read every authored rendering string in `project-detail.js`, `overlap-detail.js`, `export.js`, and `brief.js`, plus relevant HTML and CSS, app/list callers, API detail/brief routes, template wording, geometry/sharing/savings wording, tests and the T1.7 before/after reports. Read the brief, judge instructions, gridlock-build judge sections, glossary, contracts/overlap rules/style, definition of done, house patterns, UI contract, design direction and review checklists A/D/E. The old root `DIRECTION.md` path was absent; its committed design-folder version and the brief's overriding DIRECTION-v2 were read.

I did not independently reread source PDF pages or rerun the full VERIFY gate, actual Letter PDF generation, or the two deselected screenshot tests. Source parity here means API/source-metadata-to-rendered-output parity, not a new domain extraction audit. Unknown-year wording and some export failures were traced by reading; the passing checks are only those named above. Existing test-managed temporary trace output was produced by the brief fixture; the only authored repository file is this judgment.

2026-09-26 lesson: A full rendered-record scan can verify data preservation while still missing authored-copy lint coverage when presentation text is labelled as source data.

material improvement still available: no
