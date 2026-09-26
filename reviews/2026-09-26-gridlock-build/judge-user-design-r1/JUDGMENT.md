# G3 round 1: first-week user and design

Lead archive note: this main-copy report retains `control-proof.json`, `probes.json`, `state-checks.json` and seven essential screenshots. Other matrix screenshots and the generated CSV/PDF were inspected by the judge but were not retained in the archive.

2026-09-26. Independent judge; no product code changed. Frozen HEAD confirmed before and after review: `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc`. Copy: `C:\Users\lucia\dev\gridlock-wt\judge-user-design-r1`; localhost port **8782**, AI and Google off. Mode achieved: **live Chromium interaction, screenshots, DOM measurements, generated CSV/PDF and source inspection**. No real Google or Claude service used.

**Verdict: small corrections needed. P0: 0; P1: 0; P2: 2; P3: 1.** First-week user **7/10**, design **7/10** (7 = solid junior; 8 = professional). The actual planning task works quickly and the uncertainty language is strong. First-visit controls and the tour still fall short of professional finish.

## Scope and evidence

Read the assigned brief, CLAUDE, SPEC, PROJECT-PROFILE, G3 TRACKER/DELIVERY, house patterns, definition of done, DIRECTION-v2, ui-contract and review checklists A/H, judge role and build skill 0/7. DIRECTION-v2 supersedes the earlier no-tour and wall-map style requirements. The accepted phone zoom minimum, optional Google check, source-classification question and real Claude access were not reopened.

Exercised 390×844, 768×900 and 1440×900 in both themes: default, top pair, brief, search happy/empty/error, filters empty/recovery, area/radius, late year, project empty/detail, invalid pair URL and repeated pair selection. Also walked the tour through completion by keyboard at all six combinations, inspected row hover/focus, generated CSV and Letter PDF at desktop dark, and checked failed brief/area retries. Screenshots cover each matrix scene. `state-checks.json` records 48 observations; `probes.json` records six tour and hit-test runs. The latter's trial-click result can pick an alternative click position or fail on a disabled minimum-zoom button; **use `control-proof.json` for the definitive center-pointer reproduction**.

No formal pytest/VERIFY suite was run by this judge; G3's recorded 674-pass result was read, not represented as this judge's run. The custom live scripts completed after two harness corrections: collapsing the phone sheet before clicking its covered timeline, and selecting a visible project row after filtering. Those harness mistakes are not product findings. No uncaught page errors occurred. Default horizontal overflow was **0 px in all six combinations**. The scripts are evidence helpers in this report folder only.

Not exercised: venue projector, a human participant study, actual screen reader, physical touch device/pinch, real cloud services, every one of 489 detail screens, every PDF page visually, or source-PDF numeric validation (domain judge's lens). Reduced motion was used for the matrix; the initial desktop selection was observed with normal motion. These limits prevent a claim of exhaustive accessibility or rendering certification.

## Cold three-minute task

Agent-led first visit at 1440×900 light: first pair opened at **17.3 seconds / 1 click**. General task completed at **52.6 seconds / 5 clicks**, plus two panel scroll operations: open #1, back, Take the tour, Next, Next. Timer includes tool turnaround and inspection; this is not a measured human completion time.

- Top pair: Dominion's **Okatie – McIntosh 115kV Tie: Add Series Reactor** and Georgia Power's **MCINTOSH 230 KV, BREAKER CONTROL RELAY UPGRADES**.
- Evidence shown: mapped 0.0 km shared named endpoint; 2028/2028 timing; approximate pair location; source pages 41/107.
- Ranking explanation located in tour step 3: distance band, timing, accuracy and cross-state factor; savings excluded. Exact numeric score/weights are not displayed in this path, so this establishes the general factors, not a numerical rank-1-versus-rank-2 comparison.
- Caveats: mapped endpoint proximity does not confirm shared work; locations need source-drawing checks; neither source confirms a joint project or saving.
- Safe next action: compare the plans and verify work locations/current schedules with both organizations before proposing shared scope. Template brief states this clearly and gives a labelled $54,000–$161,000 estimate with its 1%–3% assumption.

## What works well

1. **The map communicates the intended product.** Both states are visible, project overlays stand out from muted streets, dashed/solid encoding survives dark mode, and selecting a pair fits its geographic context. See `cold-desktop-light.png`, `default-390-light.png`, `default-768-light.png`.
2. **Evidence is readable and cautious.** The detail leads with an answer and three short bullets, then disclosures. Sources, approximate locations, missing partner cost and screening assumptions remain explicit. The template never pretends to be generated AI. See `top-pair-stable-light.png`, `brief-1440-dark.png`.
3. **Recovery works.** Each theme/width recovered from a search 503 to Savannah; the real Savannah area showed 17 projects/40 overlaps. Empty filters cleared back to 489 pairs. Script text, 501-character and non-Latin inputs remained text and produced honest empty states. Brief and area 503 retries recovered. See `search-error-1440-light.png`, `filters-empty-768-dark.png`, `area-390-light.png`.
4. **Output is usable.** CSV parsed as 489 data rows plus header. The generated Letter PDF has 127 pages and 489 ranked rows in the print DOM; its first screen includes date, filters, selected pair, full evidence and sources on light paper from dark mode. Native controls are excluded. This confirms generation/content and first-page presentation, not a visual review of all 127 pages.
5. **Keyboard treatment is deliberate.** Row focus is obvious, Enter opens the pair, tour completion returns focus to its launcher in all six combinations, Escape closes area, and range Home/End reaches 1/80 km. See `row-focus-dark.png`.

## Verified defects

### JUD-01 — P2 — First-visit invitation covers zoom controls

**Owner:** WEB-2 tour CSS, with WEB map integration check. **Lines:** `web/css/tour.css:1` positions the invitation at top 112/right 16/z-index 1400; `web/css/tour.css:20` moves it to top 64 on phones. `web/css/app.css:203–204` supplies the 44 px zoom controls. Callers read: `setupTour()` in `web/js/tour.js` and its initialization in `web/js/app.js:178`, map initialization/controls and first-visit tests in `tests/e2e/test_tour.py`.

**Trigger:** fresh storage, `/`, first visit. At 390×844 light the invitation covers **95.45% of zoom-in** (control x328/y84/w44/h44; invitation y64–126). At 768×900 and 1440×900 light it covers **100% of zoom-out** (y128–172; invitation y112–174). Screenshots show the same overlap in dark mode. `elementFromPoint` at the covered control center returns `tour-dismiss`. An actual center-pointer click dismisses the invitation instead of operating zoom, at all three widths.

**Impact:** the first screen hides a principal map operation and turns its expected target into a different action. A dismissal or another zoom method works around it; this is P2, not a blocked core workflow. The first-visit tests verify Projects reachability and only phone zoom geometry versus the panel, so they miss invitation-versus-zoom overlap.

**Correction:** place the invitation in a reserved region that cannot overlap either zoom button (or in header flow at every width), retaining dismissal and phone two-row preview.

**Acceptance:** fresh-storage 390/768/1440, both themes: invitation intersection area with both zoom controls is zero; each enabled control receives a real pointer center click and changes zoom without dismissing or launching the tour. Preserve title/Projects reachability and existing phone geometry checks.

**Essential evidence:** `first-visit-390-light.png`, `first-visit-1440-light.png`, `control-proof.json`. Dark counterparts are available in this folder.

### JUD-02 — P2 — Fresh tour permanently omits two built features

**Owner:** WEB-2 tour. **Lines:** `web/js/tour.js:148` filters steps once at tour start based on current visibility. `web/js/tour-content.js:27` (area) and `:29` (brief) lack preparation. Pair/source steps explicitly prepare their targets at `web/js/tour.js:110–115`. Full tour module, content, `web/js/search.js`, `web/js/overlap-detail.js`, `web/js/brief.js`, app initialization and tour tests were read.

**Trigger:** fresh `/`, start tour before choosing a place/pair, then advance to completion. Every width/theme route presents the same ten substantive steps, **without “Explore an area” or “Read a coordination brief.”** The brief is successfully loaded when the tour opens the top pair later, but the earlier filter has already removed its step. The area control starts hidden until a search result is selected. Both features were separately exercised successfully.

**Impact:** the founder-requested walkthrough does not explain the complete built demo to the first visitor. DIRECTION-v2 explicitly lists both features and permits skipping features not built yet; these features are built. Existing `test_keyboard_tour_walk_and_focus_return` asserts the ten other titles and permits 8–12, so its passing result does not guard these omissions.

**Correction:** retain built conditional steps and prepare their actual targets as the tour reaches them. Brief can use pair preparation plus readiness; the area step should demonstrate a real selectable place/area while preserving or restoring the visitor's state. Alternatively anchor the area explanation to an always-available entry point with truthful instructions, without silently removing the step.

**Acceptance:** from fresh default storage in all six viewport/theme combinations, a full tour includes both titles and a real relevant target; brief is labelled Template; the area step has an actionable explanation. Preserve search/filter state and focus return, and continue safely through genuinely unavailable targets or failed API requests.

**Essential evidence:** `probes.json` (complete title arrays), `tour-desktop-9.png` and `tour-desktop-10.png` (filters directly followed by export), plus `area-390-light.png` proving the area is built. The separately captured brief proves its availability.

## Substantiated usability gap

### JUD-03 — P3 — Selected map labels wrap into narrow vertical columns

**Owner:** WEB. **Lines:** `web/css/app.css:146` sets only a maximum tooltip width and normal wrapping; `:150` allows breaking anywhere. `web/js/map.js:30–50` renders name/utility/accuracy/full citation; `:223` binds it and `:261` opens both selected labels. `web/js/list.js` and overlap-detail callers were read.

**Trigger:** select rank 1 at 1440×900, either theme, after map fit settles. Measured labels are **92.6/93.5 px wide** and **303.5/323.1 px tall**. “MCINTOSH” breaks as “MCINTOS / H”; much of the vertical label is the repeated source title. This is a steady layout, not the captured intermediate zoom frame.

**Impact:** poor label scanning on the map and unnecessary map occlusion. The full panel evidence remains readable, so severity is P3. The desktop ranked row is also tall, but no separate defect is claimed for dense source text.

**Correction:** use a sensible viewport-bounded tooltip width and consider shortening only the displayed citation label while keeping full source/page accessible. Preserve verbatim project data and prevent collisions/offscreen placement on phones.

**Acceptance:** rank-1 settled labels at 1440/768 both themes should not split ordinary words such as MCINTOSH when usable map width is available; the full names/source remain reachable, with no phone overflow.

**Essential evidence:** `top-pair-stable-light.png` and `brief-1440-dark.png`.

## Scores and preferences

Nielsen heuristic assessment (0 poor to 4 strong, **31/40**): system status 4; real-world match 4; user control 3; consistency 3; error prevention 3; recognition 3; efficiency 3; restrained presentation 2; recovery 4; help 2. Losses chiefly come from JUD-01/02, tall tooltips and ranking explanation being available only through the tour.

Cognitive-load checks: clear primary task **yes**; answer-first detail **yes**; uncertainty proximity **yes**; source traceability **yes**; progressive disclosure **yes**; control discoverability **mixed**; geographic label scanning **mixed**; complete onboarding **no**. Alex can follow the ranked workflow; Sam has visible focus and a list route; Casey has functioning phone controls after expanding/collapsing the sheet, with the first-visit zoom defect above.

Technical assessment, separate from visual taste: **16/20 provisional** across accessibility 3/4, performance 3/4, responsiveness 3/4, themes 4/4, implementation integrity 3/4. This is scoped live-review evidence, not a replacement for the formal auditor matrix. The UI is specific to planning/maps rather than a generic landing-page template.

**Preference, not an additional defect:** a compact “How ranking works” disclosure beside Ranked overlaps would make the reasoning easier to discover than replaying tour step 3. No new architecture or scope is required by this suggestion, and it does not drive the verdict.

No new founder decision is required to correct JUD-01/02. No product edits, commits, installs or external actions were made. Chromium emitted a small GPU mailbox `debug.log` at the worktree root during review; it was moved into this evidence folder as `chromium-gpu.log`, leaving only this folder untracked. No corresponding page error or persistent screenshot failure was observed. The dedicated review browser was closed and port 8782 server stopped at completion.

## Handoff and compact evidence set

Copy only these if minimizing review artifacts: `JUDGMENT.md`, `control-proof.json`, `probes.json`, `state-checks.json`, `first-visit-390-light.png`, `first-visit-1440-light.png`, `tour-desktop-9.png`, `tour-desktop-10.png`, `top-pair-stable-light.png`, `area-390-light.png`, `search-error-1440-light.png`, `row-focus-dark.png`, `print-dark-first-page.png`. The CSV, 127-page PDF and rest of the matrix may remain in this frozen evidence folder.

2026-09-26 lesson: check onboarding against controls and future tour state, not only the elements visible when onboarding begins.

Compact summary: two local P2 fixes (invitation/zoom collision; omitted area/brief tour steps), one P3 map-label readability gap; all evidence in `reviews/2026-09-26-gridlock-build/judge-user-design-r1/`.

**material improvement still available: yes**
