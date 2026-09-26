# T4.2 round-two accessibility judgment

Lead archive note: this main-copy report retains ten screenshots of the verified findings and P3 focus note. Other viewport/theme walkthrough images, CSV/PDF evidence and scripts were inspected by the judge but were not retained in the archive.

Date: 2026-09-26. Verdict: **not ready** against the stated WCAG 2.2 AA / UI contract. Accessibility score: **7/10** (solid working keyboard foundation; below the 8/10 professional anchor because a normal phone state completely conceals focused controls).

Independent judge; I did not build the product. Frozen worktree: `C:\Users\lucia\dev\gridlock-wt\judge-a11y-r2`. Initial and final HEAD: `8d83ad0a95c67909bebb9e802a6d4ffba2468bcc` (`g3`). Port 8786 only. AI and Google off; browser requests restricted to that loopback origin; no credentials, installations, outward actions, product edits or commits.

## Mode and evidence limits

Mode achieved: **live Chromium browser**, driven through Python Playwright keyboard input, with DOM/ARIA snapshots, hit testing, screenshots, grayscale emulation and print CSS rendering. No real screen reader was available. All announcement wording below is inferred from accessibility-tree / live-region evidence, **not heard through NVDA, JAWS or VoiceOver**. This is a scoped accessibility judgment, not a full conformance certification.

Read: brief; gridlock-build sections 0/7; accessibility and judge roles; SPEC; PROJECT-PROFILE; CLAUDE; frozen tracker and DELIVERY; definition of done; house patterns; UI contract; DIRECTION-v2; review-checklists A/F/H; relevant complete application modules and their tests. The Lucky workflow was read from its absolute vault path, without edits.

Starting evidence: frozen DELIVERY records G3 VERIFY exit 0, **674 passed / 0 failed / 0 skipped**, 24 scene combinations green, plus shell/audit gate totals. Those are inherited gate results, **not a suite rerun by this judge**. This session performed six live size/theme keyboard journeys and targeted reproductions. The only harness error was a Playwright wait expressed as a JavaScript string that CSP rejected; changing the wait to a locator assertion resolved the harness issue. It was not counted as a product defect.

Walked 390×844, 768×900 and 1440×900 in light and dark: skip link → ranked pair → detail/brief → Back; Projects → filtered project → detail → Back; Savannah search → area → radius arrow → Escape; Filters → utility checkbox → empty result; tour entry/Next/Escape; timeline arrows. Also traversed all ten tour steps by Tab/Enter at 390 dark; all 489 ranked rows to the timeline at 390 light; brief disclosures and Copy reachability; keyboard CSV download and print preparation; 503 search, brief and project-load failures; brief retry recovery; zero-result area; non-Latin, literal `<script>` and 501-character search queries; 320 px reflow; grayscale list/detail; reduced motion.

Print evidence is Chromium print-media rendering and a two-page Letter PDF, not an OS print-dialog or PDF tagging audit. No real assistive technology, touch hardware, venue projector, external Google mode, full 200% text-resize matrix, or exhaustive dragging-alternative audit was performed.

## What is good

- The skip link reaches `#opportunities`; Enter on a ranked pair focuses Back to ranked overlaps. Back returns to the selected row in all six journeys. Project opening focuses its Back button, and returning restores the project row. The core job works without map input.
- Native labels, fieldsets, disclosures, ranges and buttons provide useful semantics. Filter changes expose an explicit result count. Area radius announces a km value, and Escape returns to Explore this area with `Area cleared.`
- Tour cards are named dialogs with count/title/body descriptions. All ten steps were keyboard operable at 390 dark; completion and Escape returned focus to Take the tour. There was no keyboard trap in the exercised routes.
- Bands have text and glyphs; utilities have written names; approximate/exact location has text plus dashed/solid geometry. In grayscale, the selected pair still has labelled evidence and distinguishable location styles. This was a manual colour-independent meaning check, not a new contrast-ratio measurement.
- The six default layouts and 320 px pair detail had zero page-width overflow. Exposed controls had visible focus in the inspected screenshots, except the expanded-phone background controls below.
- CSV downloaded through the keyboard with a current-filter status. Print preparation retained source citations, full disclosed evidence, filters/date and column headers; print media exposed zero buttons and black report text even when initiated in dark mode. Evidence: `keyboard-export.csv`, `1440-dark-print.png`, `print-first-two-pages.pdf`.
- Search edge inputs retained all 489 ranked rows and returned explicit no-match text at desktop. Brief and full-load 503 states exposed meaningful status and a retry control. Reduced-motion mode was active for these walks; map code selects nonanimated fitting and the inspected page had zero active Web Animations.

## Verified defects

### JA11Y-01 — P2: expanded phone sheet completely covers keyboard-focused timeline

**Location:** `web/css/app.css:15` gives timeline z-index 600; `:25` gives panel 1100; `:211` expands the sheet to 90dvh while `:213` leaves timeline positioned above the 58dvh collapsed sheet. Callers were read: sheet expansion in `web/js/app.js`, pair/project auto-expansion and area entry; the timeline remains enabled in `web/index.html:180` and its input handler in `web/js/timeline.js` remains active.

**Reproduction:** fresh 390×844, light or dark, tour invitation present. Press Tab 12 times to Expand opportunities, Enter, then Shift+Tab 14 times to In-service year. With the invitation already dismissed, the equivalent counts are 10 and 12. A second independent trigger is opening a pair, then traversing to the timeline. Focus is `#timeline-year`, at **x=87.30, y=229.19, width=207.42, height=44**. The opaque expanded sheet starts at y≈84 and covers the entire control. All nine sampled interior hit-test points resolve to sheet/header content. The screenshot shows no timeline or focus ring. ArrowRight still changes the year to `2027: 39 projects entering service, 107 pairs in the year window`.

`scrollIntoView({block:'center'})` leaves the control rectangle and all nine covering elements unchanged. Escape also leaves `aria-expanded=true` and does not reveal focus. The corresponding default collapsed 390 view and 768/1440 views expose the timeline normally.

**Evidence:** [light expanded](390-light-expanded-timeline.png), [dark expanded](390-dark-expanded-timeline.png), [light after scrollIntoView](390-light-timeline-after-scroll.png), [dark after scrollIntoView](390-dark-timeline-after-scroll.png), [pair-path reproduction](390-light-timeline-obscured.png). The original pair-path walk took 491 Tab presses from Copy brief to the slider, demonstrating that ordinary sequential focus reaches the concealed control.

**Impact / criterion:** sighted keyboard users lose their location and can change an invisible year. **WCAG 2.4.11 Focus Not Obscured (Minimum), AA: fail.** The focus indicator is also invisible in this state (2.4.7). This is not a 2.4.13 AAA appearance claim. The user-opened-content exception does not solve the observed state: Escape and scrolling do not expose the control without moving focus away to Collapse opportunities.

**Correction:** keep the timeline exposed in the expanded layout, or collapse/reposition the sheet when a background control receives focus. Audit the same expanded state for zoom, map action and attribution controls as part of the repair; do not only raise the focus outline behind the opaque sheet.

**Acceptance:** actual keyboard entry from fresh and pair/area-expanded states at 390 light/dark; each timeline button/range is visibly exposed on focus and arrows update an on-screen value. Include rendered occlusion/hit testing or screenshot evidence; checking only `outline-style` and DOM visibility does not detect this defect. Preserve the passing 768/1440 routes.

### JA11Y-02 — P2 corroboration of JREL-01: collapsed phone search feedback is hidden

**Location:** `web/css/app.css:230` applies `display:none` to `.search-state` in the collapsed phone sheet. The authored live region is `web/index.html:113`; `web/js/search.js:30–36,81,85,124` writes loading, match, empty and failure messages exclusively there until successful selection.

**Reproduction:** 390×844 collapsed sheet, dark; Tab to Search a city or project, type `zzzz-no-such-place`, Enter. DOM text becomes `No local matches for zzzz-no-such-place`; element visibility is false; its ARIA snapshot is the empty string; the visible general status remains `489 ranked opportunities loaded.` Intercept only local `/api/search?*` with 503 and type Savannah: DOM message becomes `Search unavailable. Check the local server and try again.`, still hidden. Main list remains operable.

**Evidence:** [empty search](390-dark-search-empty.png), [search failure](390-dark-search-error.png). The same CSS covers both themes. This independently corroborates the reliability judge's **JREL-01** and should share its correction, not create a duplicate repair.

**Impact / criterion:** phone users receive neither visible nor accessible feedback for failed/no-match searches. Verified **UI-contract status/error-state failure**. WCAG 4.1.3 is the relevant status-announcement check for the repair. Because this implementation hides the message from every user, this finding is not being used alone as proof of a formal 4.1.3 violation based on a visible status that only assistive technology misses.

**Correction / acceptance:** retain a visible, accessible status near search or expand the sheet upon search activity. Check loading, matches, zero matches and 503 in both phone themes: status visible, present in the accessibility tree and announced by a real screen reader; recovery with a subsequent valid query works.

## Substantiated usability note

### JA11Y-03 — P3: successful brief retry loses its keyboard position

**Location:** `web/js/brief.js:83–89` hides the panel/retry in `clear()`; `:92` calls it when opening; `:123` invokes that path from the focused Retry brief button. There is no focus handoff when the result replaces the error.

**Reproduction:** 1440×900 light, locally intercept `/api/briefs/*` with 503; open top pair and Tab to Retry brief. Remove interception and Enter. The brief loads and the live status says `Brief ready. Check the source documents before use.` But `document.activeElement` becomes BODY. Next Tab focuses ranked overlap #1, after the whole brief, rather than its recovered content/control. Reproduced twice.

**Evidence:** [error and focused retry](1440-light-brief-error.png), [focus lost on recovery](1440-light-brief-retry-focus-lost.png), [next Tab skips brief](1440-light-brief-retry-next-tab.png).

**Impact / correction:** the task succeeds, but the reader loses their keyboard position at precisely the recovered content. On an explicit retry, focus a stable brief heading/container or a suitable result control after loading. Acceptance: retry success leaves a visible focus target in the brief; retry failure keeps a usable retry target. This is a UI-contract focus-management note; **no standalone WCAG 2.4.3 failure is asserted** because the status still announces completion and the content remains reachable.

## DOM/ARIA announcement evidence by surface

These are expected accessible descriptions, not heard announcements. Native semantics are preferred; ARIA is used to expose state or dynamic results.

| Surface | Evidence / expected accessible output | Rationale and criterion |
|---|---|---|
| List | Named Ranked overlaps region, ordered list, rank/utility/name/evidence in row buttons; `489 ranked opportunities loaded.` | Heading/region names identify purpose; `aria-pressed` exposes selected pair; `role=status` announces counts. 1.3.1, 2.4.6, 4.1.2 supported. |
| Pair detail | Focused `Back to ranked overlaps`; heading `Overlap #1`; public-plan screening status; named source links and native evidence disclosures. | Explicit focus handoff and headings expose the replacement content. 2.4.3 supported in normal entry/back path. |
| Project detail | Focused `Back to projects`; full Okatie project heading; source link and location text. | Filter input has native label; selected project status supplies its name. 1.3.1/4.1.2 supported. |
| Filters | Expanded state on Filters; Utilities fieldset; native checked states; `0 ranked opportunities match filters. 3 projects shown.` | `aria-expanded` describes disclosure; live count reports filtering without moving focus. 4.1.2/4.1.3 supported. |
| Timeline | Label `In-service year`, native range bounds, `2027: 39 projects entering service, 107 pairs in the year window`; All years / Play years pressed state. | `aria-valuetext` supplies useful meaning beyond numeric value. 4.1.2 supported; expanded-phone 2.4.11 failure above. |
| Search | Labelled native datalist search; matches/no-match/error statuses at desktop; successful selection updates general status. | Native suggestions avoid custom combobox focus handling. Collapsed phone feedback absent, JA11Y-02. |
| Area | Named Selected area region; `Area radius` range with `40 km` / `41 km`; `17 projects in area; 40 overlaps with at least one project in area.`; named terms/counts. | Region heading, native range, `aria-valuetext` and status expose circle data without map use. Escape returns to entry. |
| Brief | Named Coordination brief region, Template, topic headings and disclosures, source links, `Brief ready. Check the source documents before use.` | `aria-busy` indicates loading and `role=status` announces result; automatic load does not steal focus from pair. Retry note above. |
| Tour | Named `GridLock tour` dialog; count, heading and body in `aria-describedby`; each step receives focus. | Focused nonmodal explanatory card is announced as one context; Escape/finish return to launch. |
| Export/print | Named buttons; `CSV download prepared with the current filters.` and `Report prepared. Choose Letter paper in the print dialog.`; report table caption and scoped column headings. | Live status provides progress; native table semantics associate print columns. |

Keyboard access/no-trap (2.1.1/2.1.2), labels/roles (4.1.2), ordinary focus return/order (2.4.3), inspected reflow (1.4.10) and colour-independent list/detail meaning (1.4.1) were supported in the exercised paths. Contrast (1.4.3/1.4.11) and target sizing (2.5.8 plus the stronger phone 44px contract) rely on the recorded G3 automated measurements with this session's visual corroboration; they were not remeasured exhaustively. Reduced motion was honored in the tested journeys; animation-from-interaction criterion 2.3.3 is AAA, not an AA failure criterion.

## Result, cleanup and lesson

Counts: **P0 0, P1 0, P2 2 (one new, one JREL-01 corroboration), P3 1**. No preferences or founder decisions were promoted to defects. Top findings, in order: JA11Y-01 hidden phone timeline focus; JA11Y-02 hidden phone search status (JREL-01); JA11Y-03 brief retry focus loss. No fourth/fifth finding is invented.

Evidence folder: this directory. Screenshots `{390,768,1440}-{light,dark}-{detail,project,area,filter,tour,timeline}.png` document the six main journeys. The isolated judge browser and server were closed by the harness; final HEAD remains the frozen G3 commit. Only this evidence directory is untracked; product files are unchanged.

2026-09-26 lesson: a passing focus-outline probe does not prove visible focus when an opaque responsive panel covers the control; test rendered occlusion after expanding the sheet.

material improvement still available: yes
