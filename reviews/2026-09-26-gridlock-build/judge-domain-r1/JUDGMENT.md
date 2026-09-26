# G3 domain judgment — T4.1 round 1

Lead archive note: this main-copy report retains the three essential screenshots named below. Other screenshots cited in the original frozen review were inspected by the judge but were not retained in the archive.

2026-09-26, 17:26 EDT. Independent transmission-planner lens; I did not build the app.

**Verdict: two P2 presentation gaps; no P0/P1 found. Domain score: 7/10.** The numerical screening and source trail are strong, but known uncertainty in utility attribution and printed costs does not consistently reach the planner. On the required anchors, this exceeds a tutorial (4–5) and meets solid junior work (7); the two omitted qualifications keep it below professional completeness (8).

## Copy, mode, and coverage

- Frozen worktree: `C:\Users\lucia\dev\gridlock-wt\judge-domain-r1`.
- HEAD checked before work: `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc`. Never synced or committed.
- Live browser mode achieved: local server on **8781**, Chromium through installed Python Playwright, plus direct local API responses and local PDF text extraction. Screenshots were personally inspected. All commands used `GRIDLOCK_AI=off`, `GRIDLOCK_GOOGLE=off`; server used the existing outbound socket guard. No external request, key, installation, paid generation, or source mutation.
- Read the judge role; CLAUDE; SPEC contracts/overlap/code rules and remaining context; PROJECT-PROFILE; G3 TRACKER and DELIVERY; gridlock-build §0/§7; review-checklists §A/§H; definition of done; Lucky workflow; and the relevant pipeline, API, detail/list/map/brief/print callers and browser tests.
- Independently exercised overview, Savannah city search and 40 km explorer, top-ten pair details, local source links, project details, approximate placements, GA-only caveats, template brief readiness, selected-pair print preparation, CSV, cross-state/year filters, empty results, malformed overlap link, and search empty/501-character/script-like/non-Latin inputs. Injected a local search 503 to verify an honest error message.
- Viewports: 1440×900, 768×900, 390×900, light theme. Top-pair evidence and flagged-cost project walked at all three widths. No page errors or horizontal document overflow in those three runs. Initial first-row readiness measured 1.47 s / 1.03 s / 1.05 s respectively in this session; these are single observations, not performance guarantees.
- Did not repeat the full VERIFY suite, judge live Google/Claude, verify real-world construction boundaries, exhaustively inspect every source page, or conduct the separate accessibility/design/security lenses. Dark mode, every control's keyboard state, and every feature's full error matrix were not independently covered by this domain pass. No pytest total is claimed.

## What works, with independent evidence

### Distance and ranking

I re-derived five distances without importing pipeline helpers or calling Shapely nearest-points. I projected vertices with EPSG:5070, found each closest segment point using the clamped dot product `t=max(0,min(1,(P-A)·(B-A)/|B-A|²))`, inverse-projected that point, and applied WGS84 geodesic inverse distance. Point pairs and common endpoints are the corresponding degenerate cases. This checks implementation independently while retaining the specified projection/geodesic libraries; it does not validate the underlying real-world locations.

| Rank | Pair | Independent km | Artifact km | Band |
|---:|---|---:|---:|---|
| 1 | `desc-p41__sertp-p107-9bc088` | 0 | 0 | touching |
| 4 | `desc-p41__sertp-p113-5484a4` | 0.734739854605 | 0.734739854605 | under 1.6 km |
| 18 | `sertp-p123-09973f__sertp-p133-9ca229` | 7.522327099401 | 7.522327099401 | under 8 km |
| 47 | `sertp-p123-6a22d5__sertp-p133-9ca229` | 13.691547142057 | 13.691547142057 | under 40 km |
| 2 | `sertp-p68-a0289a__sertp-p72-81610d` | 0 | 0 | touching |

The rank-4 closest point is the McIntosh endpoint (-81.1751124, 32.3521162), to West McIntosh (-81.1824528, 32.3543695). Rank 18 compares Wansley (-85.0335749584, 33.4123378808) to Heard County (-84.9977699922, 33.3515296284). Rank 47 compares Wansley to Dresden (-84.9054815572, 33.3515880660). All five differences were 0 m at returned precision.

I independently recalculated **all 489** band assignments and scores from the spec's constants, two accuracy factors, year-gap factors, and known-state bonus: zero mismatches. Sorting by descending score, ascending distance, then ID reproduces the entire artifact order. CSV contains 489 rows and its top ten IDs match the live/API/artifact order. The live cross-state filter returns 43 pairs.

### Top ten, source pages, and savings

The top ten contain 14 unique projects. Each name and description matches its cited local PDF page after whitespace normalization; each stated year matches the page. Voltages agree with the names/descriptions in those same source rows. DESC p.41 prints the retained $5,376,418 cost; SERTP costs remain null. All ten live pair views rendered the correct names; all 20 project citation links returned local `200 application/pdf` with the recorded page fragments.

| Rank | Source pages | Years | Score | Savings |
|---:|---|---|---:|---|
| 1 | DESC 41 / SERTP 107 | 2028 / 2028 | 4.8 | $54,000–$161,000 estimate |
| 2 | SERTP 68 / 72 | 2026 / 2026 | 4.0 | no usable cost/mileage |
| 3 | DESC 41 / SERTP 111 | 2028 / 2028 | 3.84 | $54,000–$161,000 estimate |
| 4 | DESC 41 / SERTP 113 | 2028 / 2028 | 3.6 | $54,000–$161,000 estimate |
| 5 | SERTP 124 / 133 | 2029 / 2029 | 3.2 | $50,000–$450,000 proxy estimate |
| 6 | SERTP 124 / 133 | 2029 / 2029 | 3.2 | $50,000–$450,000 proxy estimate |
| 7 | SERTP 68 / 72 | 2026 / 2026 | 3.2 | no usable cost/mileage |
| 8 | SERTP 72 / 72 | 2026 / 2026 | 3.2 | $165,000–$1,485,000 proxy estimate |
| 9 | SERTP 82 / 92 | 2027 / 2027 | 3.2 | no usable cost/mileage |
| 10 | SERTP 114 / 124 | 2029 / 2029 | 2.56 | $50,000–$450,000 proxy estimate |

The two Wansley rows on p.133 preserve distinct six-breaker and ten-breaker descriptions despite identical names; this is source duplication, not an invented duplicate. The 5-mile Tenaska line and 16.5-mile LaGrange line mileage support the stated proxy arithmetic.

All 489 savings statuses/bounds independently matched Decimal half-up $1,000 rounding and the stored team assumptions: **201 ranges, 74 no-cost, 214 timing-too-far**, zero mismatches. Example: $5,376,418 × 1%/3% = $53,764.18/$161,292.54, rounded to $54,000/$161,000. Five miles × $1M/$3M × 1%/3% gives $50,000/$450,000. These remain expressly team assumptions rather than measured savings.

### Source-conservative wording and planner flow

- The top McIntosh pair identifies a **shared named endpoint**, and expanded evidence explicitly distinguishes the unknown Deerfield work location from the McIntosh 230 kV relay bus. Rank 3 explicitly limits SERTP work to the 6.7-mile Goshen (Savannah)–Georgia Pacific (Rincon) section and says the full-line endpoint establishes no work at McIntosh. These repaired caveats are present at runtime.
- Savannah Goshen is at (-81.2094724, 32.2487012); the separate MEAG Goshen record is at (-81.9953118, 33.3197599), avoiding the known Savannah/Augusta collision.
- Approximate pair detail immediately says “possibly touching” or “distance is approximate”; source descriptions and placement evidence remain expandable. Exact location does not claim exact construction limits.
- GA-only pairs 2 and 5 expose the Integrated Transmission System caveat in Pair evidence. Selected-pair print retains it and opens source disclosures. The Savannah explorer reports 17 projects and 40 pairs with at least one project in the 40 km area, with its independence from list filters stated.
- The core route is short: fill Savannah, Enter, open a pair, open Pair evidence. The view loads without a key; brief origin is Template; absent cost stays “not stated.” Error/empty cases did not turn failed loads into fabricated data.

## Findings

### Verified defect — JDOMAIN-01 [P2]: inferred utility attribution is presented as stated

**Lines/callers:** `web/js/project-detail.js:58` and `:153` output `props.utility`; `web/js/list.js:64`, `web/js/map.js:40`, `web/js/export.js:48`, and `server/app.py:251`–252 do the same in list/map/print/CSV. `projectSummary` is called by project `renderDetail` (`project-detail.js:170` onward), `renderOverlapDetail`, and selected-pair print. The pipeline explicitly sets `utility_basis="inferred_from_location"` at `pipeline/place_projects.py:285`–287. No web JS reads `utility_basis`.

**Trigger and observed result:** open rank 1, or Projects → search “MCINTOSH 230 KV” → its relay project (`sertp-p107-9bc088`). Its API/artifact says `utility="Georgia Power"`, `utility_basis="inferred_from_location"`. Every visible and expanded project field labels the owner simply “Georgia Power”; there is no attribution warning. Its CSV utility cell and print utility likewise omit the qualification. The same stored condition affects **78 of 230** projects. This is distinct from geometry accuracy: the McIntosh location is exact, while its utility attribution is inferred.

**Views/viewport/evidence:** rank list and pair/project detail at 1440×900; top-pair details also walked at 768×900 and 390×900. `inferred-utility-1440.png`, `overview-1440.png`, `evidence-768.png`, `evidence-390.png`, `print-pair5-1440.png`. The DOM with all disclosures open still contains no attribution qualifier.

**Impact and basis:** a planner can mistake a location-based attribution for the utility named by the source. This conflicts with the profile glossary's explicit “Georgia Power (inferred)” convention and the contract's separate attribution basis. It matters directly to interpreting the leading opportunity and choosing which organization to approach. The existing location caveat does not cover ownership inference.

**Concrete correction:** preserve canonical utility values for filters, contacts, and schemas, but display a human label such as “Georgia Power (inferred)” wherever this project's utility is presented; explain that the plan names Southern Company and the utility is inferred from location. Carry the qualifier into exported/printed project attribution without changing the frozen contract.

**Acceptance:** real McIntosh input and an explicitly stated SAV input produce different attribution labels in list, map tooltip, project/pair detail, print, and CSV. The former includes “inferred”; the latter does not. Filtering and canonical contact matching still work. Cover 390 and 1440 widths.

### Substantiated usability gap — JDOMAIN-02 [P2]: recorded cost discrepancies disappear from project detail

**Lines/callers:** `web/js/project-detail.js:62`–64 renders only the plan amount. `projectSummary` at `:53`–79 never reads `cost_flags`; `renderDetail` uses that summary. The API/artifact supplies the flags correctly. Pair savings can carry a flag in expanded basis text, but that does not restore the standalone project's missing warning.

**Trigger and observed result:** Projects → Eastover–Sumter (`desc-p4`, project ID 6846 A), then open both Source text and Location sources. It displays **Plan cost: $1,238,443** with no qualification. Local DESC PDF p.4 prints previous $88,443, 2026 $1,150,000, 2027 $850,000 and later zeroes: their sum is **$2,088,443**, an **$850,000** discrepancy. The artifact explicitly contains `printed_total_differs_from_sum` and `below_list_threshold`; neither is rendered. The printed amount itself is correctly preserved.

**Views/viewport/evidence:** standalone project detail at 1440×900, 768×900, 390×900, with every disclosure open. `flagged-cost-1440.png`, `flagged-cost-768.png`, `flagged-cost-390.png`. Nine retained projects carry the discrepancy flag; ten carry at least one cost flag.

**Impact and basis:** the app has already detected contradictory source cost information but leaves the planner to rediscover it in the PDF. The known $850,000 discrepancy is material to using the displayed amount in screening discussions. SPEC's source-data contract and T1.1 explicitly preserve these flags; the honesty requirement calls for estimates and source caveats to remain visible.

**Concrete correction:** retain $1,238,443 and show a concise adjacent warning such as “Printed total differs from the year columns; verify the source.” Render the below-threshold flag in understandable wording as well. Use the same shared project summary in project, overlap, and selected print views; do not recompute or replace the source total.

**Acceptance:** `desc-p4` shows the printed total and both warnings at 390/1440; an unflagged project such as `desc-p41` does not gain warnings. The warnings remain in selected print detail when a flagged project participates in a pair. Existing numerical cost/savings assertions remain unchanged.

## Preferences and founder decisions

- No additional preference is promoted to a defect. Narrow selected-map labels were relayed to the design lens with `top-pair-1440.png`; this domain pass does not double-count that visual concern.
- Source classification/Q2, Okatie's inferred location, and obtaining Thomson–Vogtle material are already documented founder/source decisions. No new evidence here changes their disposition. No secure source was fetched and no new source passage was added to product artifacts.

## Evidence and closeout

All evidence is in this report's folder. **Essential screenshots to preserve:** JDOMAIN-01: `inferred-utility-1440.png`; JDOMAIN-02: `flagged-cost-1440.png` and `flagged-cost-390.png`. The report contains the calculations and source checks, so the remaining audit images are optional.

Additional audit screenshots: `savannah-area-1440.png`, `pair-2-1440.png`, `pair-3-1440.png`, `pair-5-1440.png`, `search-no-match-1440.png`, `search-error-1440.png`, `invalid-link-1440.png`, `empty-filters-1440.png`. Browser processes opened by this judgment were closed. Server PID 40368 was stopped; no listener remains on 8781. Final HEAD is still `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc`; git status contains only this judgment/evidence directory.

2026-09-26 lesson: correct stored provenance is insufficient when shared presentation components omit its qualifiers.

Compact summary: numerical/source screening passed; 0 P0, 0 P1, **2 P2**, 0 P3. Top findings are inferred utility labels and hidden cost warnings; there are no third through fifth findings. Evidence folder: `reviews/2026-09-26-gridlock-build/judge-domain-r1/`.

**material improvement still available: yes**
