# T4.2 round two: every user-facing word

Lead archive note: this main-copy report retains five screenshots of the two verified findings and the two JSON evidence files. Other screenshots and probe scripts were inspected by the judge but were not retained in the archive.

Verdict: **ready with notes**. Clarity: **7.5/10** (7 = solid usable product; 8 = professional copy with accurate edge-state wording throughout). Two verified P2 defects prevent an unqualified 8. No P0, P1 or P3 findings. I did not build this product.

## Scope and evidence

- Frozen worktree: `C:\Users\lucia\dev\gridlock-wt\judge-copy-r2`; initial and final HEAD `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc` (`g3`). No sync, product edits or commit.
- Mode achieved: live Chromium against the real local API on **8785**, screenshots and source review. AI and Google off, external browser requests blocked, server outbound socket guard enabled. Both scripts stopped their own server and closed Chromium. Final listener check found no listener on 8785. Git status contained only this review folder.
- Read the assigned brief, reviewer/judge roles, GridLock skill sections 0/7, workflow router, SPEC contracts/overlap/style, profile glossary/rules/traps, G3 tracker/delivery, DIRECTION-v2 readable-text requirement, UI contract, definition of done, house patterns, and checklists A/D/E/H.
- Read authored HTML/JS wording, CSS text generation search, tour content and callers, brief template, print rendering, API/status/error callers, and relevant existing tests. Source text and names are distinct from authored prose; their punctuation is not a copy defect.
- `walk.py` and `focused.py` both exited 0. They exercised 1440×1000, 768×1000 and 390×844: real pair/project/unknown detail, savings, filtered/empty views, selected area, tour, print and local error responses. Detailed machine evidence: `evidence.json`, `focused-evidence.json`.
- Runtime scan rendered all **230 project + 489 pair views = 719 views**, checking **3,394 detail bullet lists**. No over-three-bullet block or forbidden internal ID/enum/path in their computed fields. This scan does not cover native search option values; that separate surface yielded JCOPY-02.
- Print prepared all **489 ranked rows**, opened source/evidence disclosures, preserved the selected pair and displayed estimate assumptions. This was browser print-media inspection, not a physical printer run or full PDF pagination audit.
- Tour: 11 real steps completed at desktop and phone with pair/brief available, including source, savings and brief. Filtered no-pair entry also completed without fabricated pair evidence. Area itself was exercised separately; direct-area entry does not expose the search-origin area tour target.
- No full VERIFY or canonical pytest suite was rerun by this judge; the runtime scripts are independent reproduction/inspection checks. No live Google, generated AI, clipboard operating-system integration, or cross-browser claims are made.

## What works well

The main detail answers lead with distance or a savings range, then at most three compact bullets. The phone savings view visibly retains “Possible saving (estimate): $54,000 to $161,000”, the dated 1% to 3% team assumption, and “Not verified: the plans do not show shared work.” This communicates uncertainty without hiding it in the disclosure.

Unknown location detail says “Location unknown; proximity cannot be assessed.” A filtered-out deep link says “This pair is outside the current filters; its public-plan detail is shown below.” These are accurate distinctions. Area totals explicitly include overlaps with at least one project in the circle and explain that unknown locations cannot be screened.

The offline brief is visibly labelled Template, limits contact suggestions to the two utility organizations, and has no fabricated individual names, emails or telephone numbers. Brief and area failures name the failed operation and a concrete retry action. Unknown overlap links direct the reader back to ranked overlaps.

### Real value traced end to end

For `desc-p41__sertp-p107-9bc088`, the local SCRTP PDF's real page 41 contains project 6888, Deerfield and **$5,376,418**. The API retains `cost_usd=5376418`; project/pair and print show `$5,376,418`. Applying the stated 1% to 3% screening assumption gives $53,764.18 to $161,292.54, rounded in the product to **$54,000 to $161,000**. The rendered savings agrees. Source link is `/api/sources/desc-scrtp-2026-2030#page=41`.

The project's exact name “Okatie – McIntosh 115kV Tie: Add Series Reactor” and full description were compared to their API fields in rendered `data-src` nodes, including the source en dash. The source disclosure retains the Deerfield construction description rather than inventing shared construction at McIntosh. The source PDF was read locally solely for this claim; no external fetch or new source transcription occurred. The lint's exact-name exemption in `tests/e2e/audits/checks.py:65` preserves these source names while checking surrounding brief prose.

## Verified defects

### JCOPY-01 — P2: filtered emptiness is described as an empty source dataset

**Exact text:** “No projects in the loaded plans.”

**Owner/location:** WEB, `web/js/project-detail.js:134`, `filterProjects()`. The caller `renderProjects(features, pairs, hasFilters)` at lines 138–160 stores only filtered features; `web/js/app.js` calls it from `renderFiltered()`. Thus `projects.length === 0` does not establish that the loaded plans are empty.

**Trigger and reproduction:** Open `/?year_min=2199`, wait for current results, then choose Projects. The real dataset contains 230 projects, but the current filter returns zero. The project view incorrectly claims there are no projects in the loaded plans. Reproduced at 1440, 768 and 390 widths. Exact runtime text is in `evidence.json` under the three `*_empty_projects` keys.

**Impact:** A planner can mistake an intentionally narrow filter for missing source coverage and is given no recovery instruction in this empty project message. The adjacent overlap empty message correctly identifies filters, making the discrepancy especially visible.

**Screenshots:** `1440-empty-projects.png`, `390-empty-projects.png` (also 768).

**Correction:** Use the existing `filtered` state to say “No projects match the current filters. Clear filters to see all projects.” Keep the actual empty-dataset wording for an unfiltered empty response. Do not change the search-only “No projects match this search.” or failed-load message.

**Acceptance check:** With real data, `?year_min=2199` → Projects must identify current filters; clearing filters restores 230 projects. Separately retain `tests/e2e/test_project_detail.py:151`'s truly empty unfiltered response and failed-load distinction. Add a search-only zero-match case. Verify desktop and phone. This is a local copy branch; no contract change needed.

### JCOPY-02 — P2: duplicate search choices expose internal project IDs

**Exact text:** “WANSLEY 500 KV, OVERSTRESSED BREAKER REPLACEMENTS (project: sertp-p133-9ca229)” and its second choice ending `(project: sertp-p133-a3bd5b)`.

**Owner/location:** WEB-2, `web/js/search.js:72–78`. `search()` uses `result.ref` as the visible duplicate suffix and assigns it to both option value and label. `server/app.py:125` deliberately supplies the internal project ID as `SearchResult.ref`; it is appropriate for identity but is not readable source prose.

**Trigger and reproduction:** Search `WANSLEY 500 KV`. The real API returns two same-name entries. Both DOM option values/labels include `sertp-p…`. The same issue occurs for the two “GTC: MCDONOUGH – SOUTH GRIFFIN 115 KV TRANSMISSION LINE, REBUILD” results, using `sertp-p103-f47086` and `sertp-p123-f7ecfd`. Exact values are recorded in both evidence JSON files. Desktop and phone screenshots show the app-generated first option value entered in the search control with its ID suffix. Chromium's native datalist popup is not painted in page screenshots, so the complete option-label evidence is the DOM capture, not the popup image.

**Impact:** The founder's DIRECTION-v2 “Never on screen: internal IDs” rule is violated in a normal search path. Hash fragments do not help a reader distinguish the records.

**Screenshots:** `1440-duplicate-search.png` (two genuine matches), `1440-duplicate-selected.png`, `390-duplicate-selected.png` (generated option value in input). These screenshots support copy exposure only; no separate selection failure is alleged.

**Correction:** Keep internal refs in the choices map and present a readable duplicate suffix. A local ordinal such as “project 1 of 2”/“project 2 of 2” is sufficient without fabricating facts; if available from already loaded fields, document/page or utility/year can help further. Preserve the source name verbatim.

**Acceptance check:** For both real duplicate queries, two unique readable choices remain; neither their displayed labels/values nor the filled search input contains internal IDs. Choose each result independently and verify the original corresponding coordinates/ref remain selected. Keep duplicate place labels distinguishable too. `tests/e2e/test_search.py:312–327` currently requires the refs inside visible strings: replace that stale presentation assertion with stronger checks of readable labels plus distinct correct selection, rather than dropping distinctness coverage. Verify desktop and phone. No schema change is required for an ordinal display fix.

## Essential screenshot index

| Evidence | Files |
|---|---|
| Two verified wording defects | `1440-empty-projects.png`, `390-empty-projects.png`, `1440-duplicate-selected.png`, `390-duplicate-selected.png` |
| Pair and estimate wording | `1440-pair.png`, `390-pair.png`, `1440-saving.png`, `390-saving.png` |
| Unknown / area / filtered pair | `390-unknown.png`, `390-area.png`, `1440-filtered-pair.png` |
| Tour with real source citation | `1440-tour-source.png`, `390-tour-source.png` |
| Print and failures | `print-selected.png`, `brief-error.png`, `area-error.png`, `invalid-pair.png` |

All files are in this judgment's folder. The remaining screenshots cover corresponding tablet/phone/desktop views and intermediate tour steps. Brief content and Template status were checked in DOM; the `*-brief.png` overview frames show only the beginning of that panel and are not full brief evidence.

## Closeout

Verified defects: P0 0 · P1 0 · P2 2 · P3 0. No preference or founder-decision findings are added. Top findings (only two substantiated): **JCOPY-01 filtered-empty claim; JCOPY-02 duplicate-search internal IDs**. Verdict remains **ready with notes**, with both small local P2 fixes recommended before delivery.

2026-09-26 — A complete detail-copy scan still misses native form option values; inspect duplicate search labels and filtered empty states as separate surfaces.

Final HEAD: `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc`. Processes/browser stopped; only review artifacts written.

material improvement still available: yes
