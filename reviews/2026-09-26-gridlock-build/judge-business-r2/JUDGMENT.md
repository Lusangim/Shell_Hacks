# T4.2 round two — business / hackathon fit

Lead archive note: this main-copy report retains the seven essential screenshots named below. Other screenshots and local probe scripts were inspected by the judge but were not retained in the archive.

Reviewed 2026-09-26, beginning 17:33 EDT. Independent judge; I did not build this product.

**Verdict: required challenge deliverables and the rough-estimate bonus are demonstrable; two P2 honesty gaps remain, one independently duplicated by the domain judge. Business/fit score: 7.5/10.** Anchor: 7 is a solid working student product, 8 is professional screening software with consistent evidence through handoff. The local demonstration is strong enough for 8; the exported estimate loses its assumptions and inferred ownership loses its qualifier, so I cannot give 8 yet. No P0/P1 found. This is not a submission-readiness verdict.

## Scope, mode and sources

- Live Chromium through installed Playwright, local server on 8784, AI and Google off, requests restricted to the local origin. Visually inspected screenshots at 1440×900, 768×900 and 390×844. No external service, credential or real generation used.
- Frozen copy: `C:\Users\lucia\dev\gridlock-wt\judge-business-r2`. Initial and final HEAD: `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc`. No sync, commit or product edit.
- Read the assigned brief, role, CLAUDE, SPEC, PROJECT-PROFILE business lens, G3 TRACKER/DELIVERY, gridlock-build §0/§7, review-checklists §A/§H, definition of done, README, methodology, assumptions, relevant rendering/export implementation and export tests. Applied the read-only Lucky workflow routing rules.
- Source check: local DESC PDF page 41 and SERTP PDF page 107 against the top pair. Challenge fit is against the challenge text preserved in SPEC; the current organiser website was not fetched under the no-network instruction.
- Exercised cold entry, search, ranked selection, detail, source links via API tests, evidence disclosure, brief, CSV download, print rendering, empty filters, invalid deep link, hostile/501-character/non-Latin search, Savannah area summary and mobile entry. Two independent browser scripts completed. Focused canonical suite: `tests/api/test_detail_export.py`, **20 passed in 2.12s**, zero failures/skips. No full VERIFY claimed.
- Not exercised: real Google/Claude, actual human delivery of a spoken pitch, physical printer/native print dialog, every filter combination, tour end to end, exhaustive accessibility/security, every source page. Other judges own those lenses. Screenshot `11-area-1440.png` caught a zoom animation frame; that transient blur is not a finding.

## Cold demonstration and genuine strengths

Fresh browser context: ranked list ready in **1.28 seconds**. Search Savannah → Enter → open first pair took three actions, and detail plus Template brief were ready **2.11 seconds after navigation**. These are automated browser readiness measurements, not a fabricated human reading time. The click budget is comfortably inside the SPEC's six actions. Opening Pair evidence is one more click; scrolling the panel exposes source, saving and next action.

A truthful three-minute demonstration can use these verified beats:

1. Show the two-state interactive map and 489 ranked candidates. Explain that a candidate is a screening lead, not an agreed joint project; 97 of 230 projects are not in computed pairs and 49 have unknown locations.
2. Search Savannah and open rank 1. The named tie-line endpoint meets the mapped McIntosh point, and both projects enter service in 2028. Open Pair evidence: the DESC work is at Deerfield, whose location is not stated. Zero mapped distance does not establish the same work site.
3. Show the DESC page-41 budget of $5,376,418 and the $54,000–$161,000 possible saving. Independently, $5,376,418 × 0.01 = $53,764.18 and × 0.03 = $161,292.54, rounded to the nearest $1,000. The percentage is explicitly a team assumption; partner cost is unknown and excluded. No realized saving is supported.
4. Show the Template brief and safe action: ask the two organisations' planning functions to verify current schedules and the work locations before proposing shared scope. Print keeps the evidence and caveats. Do not sum pair savings or call 489 pairs 489 unique construction jobs.

The demo's value is concrete: it joins two plan editions, names a candidate, connects it to actual PDF pages, gives a bounded screening number, and makes the next investigation explicit. The map/list interaction is real, not a static mockup. The brief remains usable with AI off and does not invent a person or contact details.

Source inspection confirms the DESC project name, date, stated work and $5,376,418 total; SERTP p.107 confirms McIntosh relay work and 2028, with no project cost shown. It does not independently establish Georgia Power ownership, addressed below. The app correctly exposes different location confidence and does not claim shared construction limits. Screen and print preserve the Deerfield limitation. The print rendering opens evidence disclosures and retains source page numbers.

CSV download contained all **489** records with rank, pair identities, page citations, source relationship evidence, timing and geometry confidence. The first CSV range equals the displayed range. The empty filter path says to clear filters; invalid links say to choose a ranked pair. Hostile text, a 501-character string and non-Latin unmatched input returned safe no-match states. Savannah's area tool returned 17 projects and 40 overlaps with at least one project in the area, with the independent-of-list-filters caveat. No document overflow at 768 or 390; no page errors on the principal demo.

As a small independent distance sanity check, I used the scalar haversine formula with mean Earth radius 6371.0088 km on five point-to-point pairs, without calling the pipeline. Three pairs sharing the same two station coordinates gave 7.535 km versus the app's WGS84 7.522327 km; two other pairs gave 7.298 km versus 7.313525 km. All remain in the under-8-km band; these sub-0.22% spherical/ellipsoidal differences are expected. This is a sanity check of five pair records (two distinct coordinate pairs), not a substitute for the domain judge's five full geometry checks. Pair IDs and coordinates are emitted by `probes.py`.

## Challenge and decided-feature fit

| Requirement | Observed result |
|---|---|
| Interactive UI with both utilities and highlighted overlaps | Met: offline map, selectable rank-1 pair, mapped line and point, detail and labels. |
| Ranked opportunities | Met: 489 ranked rows and matching CSV order; no claim that these are confirmed agreements. |
| Rough cost/impact estimate for at least one opportunity | Met on screen/brief/print: top-pair range, cost source, team fraction and caveats. CSV caveat loss is JBUS-01. |
| Geographic and temporal evidence | Met for demonstrated pair: shared named endpoint and 2028/2028, separate confidence and work-location warnings. |
| Source document/page and accuracy | Present in detail/brief/print and export. Ownership inference presentation is the domain duplicate below. |
| Search, filters, timeline, area, export, brief | Present; search, empty-filter path, area, CSV and print exercised here. Timeline shown, broad interaction coverage left to UI/reliability judges. |
| Named challenge examples | Methodology explicitly distinguishes Jasper/Okatie/McIntosh/Urquhart matches from absent Bluffton/Thomson–Vogtle. No invented hand-entry. |
| README/demo/Devpost/source docs | README remains an old preview; D.2 already schedules its rewrite. Full methodology, source/licence document, demo script and Devpost are T5 shipping work, not falsely reported as G3 product defects. Only the draft named-example methodology exists in `docs/` at this freeze. |

The guide's expectation that most projects may not overlap is not a licence to force the data distribution. The app's 97-of-230 display is honest; do not pitch a majority as having no overlap. Q2 source classification and newer SERTP editions remain disclosed limitations.

## Verified defects

### JBUS-01 — P2: CSV drops the evidence needed to interpret savings

**Location:** `server/app.py:35` (CSV_COLUMNS), `server/app.py:248` / `:257` (_csv_row). Read callers `export_csv`, `/api/export/overlaps.csv`, `web/js/export.js` download, and the API/browser export tests. The browser downloads the server bytes without enriching them.

**Trigger/reproduction:** at 1440×900, load the unfiltered app → Legend and reports → Export CSV; parse its real UTF-8 BOM download. There are 489 rows, **201** with Savings status `range`. Row 1 has `Savings low USD=54000`, `Savings high USD=161000`, `Savings status=range`. Its full set of fields is:

`Rank, Overlap ID, Project A, Utility A, Project B, Utility B, Band, Distance km, Touch reason, Why they touch, In-service year A, In-service year B, Year gap, Accuracy A, Accuracy B, Source A, Source page A, Source B, Source page B, Savings status, Savings low USD, Savings high USD, Coordination status`.

The entire downloaded CSV contains none of `estimate`, `1%`, `3%`, `reference cost`, `team assumption`, or `partner cost`. The API has `savings.basis` and `assumption_ids`; CSV discards both. The source pages identify construction plans, not a source for the invented-by-team efficiency percentage. Blank Coordination status does not disclose the estimate's basis.

**Impact:** the intended conflict-matrix handoff detaches 201 numerical ranges from their assumptions and scope, allowing a recipient to mistake a team screening calculation for source-supported savings. This violates the standing estimate-with-assumptions bar across sibling outputs. This is a product export defect, independent of the future README rewrite.

**Correction:** preserve current numeric and identity fields; add an explicit estimate qualification, readable savings basis, applicable team assumptions (including the mileage proxy where used), and shared-saving-not-verified caveat. Keep missing/non-range amounts empty and retain CSV formula protection. No frozen Project/Overlap schema change is necessary.

**Acceptance check:** assert the real rank-1 exported row labels its estimate, retains the $5,376,418 known-scope basis/unknown partner restriction, team 1%–3% assumption and no-verified-saving caveat. Assert a real mileage-proxy row includes the $1m–$3m-per-mile team proxy. Check non-range reasons and blank amounts, all existing numeric values/citations/order, filtered exports, and browser-download byte parity. Extend the current column-superset check; do not weaken existing checks.

**Evidence:** `walk.py` actual download output and `probes.py` whole-CSV checks. Screenshots `03-brief-1440.png`, `05-brief-768.png` and `06-print-1440.png` show the qualifications retained by the sibling views. CSV itself is tabular bytes, so there is no misleading invented UI screenshot of it.

### Corroborated JDOMAIN-01 — P2: inferred ownership appears as a stated utility

**Duplicate, not a second correction request:** independently reproduced on rank 1. `/api/projects/sertp-p107-9bc088` has `utility_basis=inferred_from_location`; `projectSummary` (`web/js/project-detail.js:57`) renders only `props.utility`, and the CSV exports only Utility B. The live detail, brief and print say Georgia Power without the inference qualifier, while SERTP p.107 identifies the Southern balancing authority area. This weakens the claim that a particular organisation is source-confirmed as the counterparty. Follow the domain judge's correction/check: preserve the canonical utility field for matching but show an inference qualifier wherever the utility is presented or exported; stated ownership stays unqualified. Evidence: `walk.py` TOP_PAIR output, `02-pair-1440.png`, `04-pair-390.png`, `06-print-1440.png`. Count this once across the pass.

## Concerns, preferences and founder decisions

- Existing Q2: source-page classification tension remains a founder/Sperry decision before public release. This review adds no new data ingestion and does not re-propose the settled unattended default.
- Existing D.2/T5 work: current README is inaccurate for the new app and still makes the old source-classification claim. Correct it in its already scheduled rewrite, along with the exact startup and offline instructions. A missing pitch/Devpost/source document is a shipping prerequisite, not a newly discovered G3 product regression.
- Preference only: an explicit first sentence describing the planner's job would improve a cold general judge's introduction. The tour and concrete demo already provide a usable path; no P2 assigned for this preference.

## Closeout

Top findings/items: (1) JBUS-01 P2 CSV estimate context; (2) corroborated JDOMAIN-01 P2 utility inference; (3) D.2 README pending; (4) T5 demo/source/Devpost package pending; (5) Q2 founder source decision. Only the first two are verified product defects. Unique new severity counts: P0 0, P1 0, P2 1, P3 0; one additional P2 duplicate.

Evidence folder: `reviews/2026-09-26-gridlock-build/judge-business-r2/`, containing this judgment, two reproducible local browser probes and thirteen screenshots. Essential images: `01-cold-1440.png` (desktop value entry), `07-cold-390.png` (phone entry), `08-evidence-390.png` (phone source limitation), `05-brief-768.png` (tablet estimate and action), `06-print-1440.png` (expanded paper evidence), `09-empty-390.png` (empty result), `10-invalid-390.png` (invalid link). Browser contexts were closed by both completed probes. The owned server session was stopped; at 17:37:48 EDT no listener remained on 8784. Final HEAD remained `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc`. An untracked `debug.log` was seen by filename in git status and was not opened, copied or edited; its origin was not investigated.

2026-09-26 — A range stays honest only when the exported handoff keeps the same assumptions and unknowns as the interactive explanation.

material improvement still available: yes
