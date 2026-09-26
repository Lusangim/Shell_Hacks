# UI contract — GridLock

Distilled 2026-09-26 by a read-only research agent from the founder's workflow vault's interface skills (`impeccable`
+ its references, `taste-skill`, `emil-design-eng`, `apple-design`, `pick-ui-library`, `prototype`,
`animate`, `review-animations`), the Lucky website example, Addy Osmani's `frontend-ui-engineering` and
`accessibility-checklist.md`. Short source keys in brackets (`op` operate.md, `cf` craft-floor.md, `col`
colorize.md, `lay` layout.md, `typ` typeset.md, `hard` harden.md, `clar` clarify.md, `onb` onboard.md,
`dis` distill.md, `pol` polish.md, `aud` audit.md, `crit` critique.md, `std` STANDARDS.md, `a11y`
accessibility checklist, `fue` frontend-ui-engineering). **[own]** = the agent's or root's judgment.
Mode: impeccable **Operate** — "The tool should disappear into the task" (op).

## Open founder decision (SPEC Q9) — design direction
impeccable's `new-work.md` treats a new product surface as a new visual world: before artifact code, a
direction round (`concept-seed.mjs` roll → decision page → founder locks one) is required "whatever the
harness, the model, or the time pressure". Its only other door is the **standing exit** — the category
standard played straight, benchmarked against two or three named products — which the skill says is the
user's choice and must not be recommended by the agent. Cost of the round: ~45–60 min agent time +
~10 min founder; its scripts live in the read-only vault, so they are either read first to prove they
write nothing there, or copied (without `node_modules`) into this repo and run here (Node 24).
The founder chose the round (2026-09-26). If they are away when every other launch task is done, the
assigned direction is used and the founder is told (the skill's own unattended rule). Output:
`reviews/.../design/DIRECTION.md`, with its utility palette checked by Claude with the `dataviz` validator.

## Tokens (defined once in `web/css/tokens.css`; no colour literal anywhere else — aud)
- **Colour roles** (OKLCH; lower chroma near white/black; no stacked translucency — col, op): canvas ·
  panel (slightly cooler or warmer than canvas) · text primary / secondary · one accent (primary action,
  current selection, state only) · focus · border · success / warning / error / info · data categories.
- **Utilities (4 main + 2 minor):** separated by **lightness**, not only hue; each line ≥ 3:1 against the
  basemap in both themes; utility named in every row, tooltip and legend; simulate colour-vision
  deficiencies (col, a11y). Dominion Energy SC is in every cross-state pair → most distinct value [own].
  Build and check the palette with the session's `dataviz` skill validator.
- **Distance bands:** one hue in lightness steps + text label + ordered glyph; never colour alone,
  never red/green (col, a11y).
- **Type:** system stack only — `system-ui, -apple-system, "Segoe UI", sans-serif` (adding Roboto /
  Arial / Helvetica / Inter trips the detector). Scale 12 / 14 / 16 / 20 / 24 px (span ≥ 2.0 for the
  detector; steps ~1.2 — op). Body 16, dense 14; floors 11 functional, 12 body, 16 for inputs at phone
  width (iOS zoom — typ, hard). `font-variant-numeric: tabular-nums` on all figures (typ, cf). Line height
  ≥ 1.3; body letter-spacing ≤ 0.05em.
- **Space:** 4-px base: 4 · 8 · 12 · 16 · 24 · 32 · 48; more space above a heading than below; ≥ 12 px
  inside bordered boxes; ≥ 16 px from the screen edge (lay, cf).
- **Radius:** 4 px controls, 8 px panels — one rule, documented [own values; taste "shape lock"].
- **Elevation:** map < docked panel < floating map controls < sheet; tinted soft shadows; a surface
  uses a border or a shadow, not both; dark mode raises with lighter fills (cf, col).
- **Native controls themed:** `accent-color`, selection, caret, focus rings; scrollbar colour only (cf, op).

## Layout
- **Desktop (≥ 1024 px):** full-bleed map; persistent side panel (search, filters, ranked list, export);
  the overlap detail **replaces the list inside the panel** — not a modal, no dimming (op, apple); the
  timeline sits along the map's bottom edge.
- **Phone (390 px):** map at `100dvh` with safe-area insets; list, filters and detail in a bottom sheet
  with explicit expand/collapse buttons; same structure, no feature dropped (adapt).
- Popups escape clipping via `<dialog>` / popover / `position: fixed` (op). DOM order = visual order =
  tab order (lay). The ranked list is the map's accessible twin: every map feature is reachable from it;
  search also opens the 40 km explorer, so the explorer works without a mouse [own].
- `<noscript>` notice (a map app cannot work without JavaScript — accepted deviation from hard).

## Density and content
- Dense is fine in Operate (op); group with spacing and hairline dividers, **no cards inside panels**, no
  coloured side stripes thicker than 1 px (cf). Row = utility swatch drawn as a line sample (solid/dashed).
- ≤ 4 visible options per decision: band + utility filters visible; the rest under "More filters" (crit).
- Ranges rounded to the precision of their assumptions (taste). Truncate only when full text stays reachable.
- **Copy:** the product's **own** wording (labels, headings, help, messages, the brief's prose) has no em
  or en dashes, no buzzwords ("seamless", "unleash", "revolutionize"…), no "BETA" stamps (taste, reg).
  **Data is shown verbatim** — project names and descriptions keep their dashes (211 of 326 Georgia names
  contain one); elements that render data carry `data-src="<field>"` and are exempt from the copy lint.
  Plain words a transmission planner uses.

## States (every surface)
- **Loading:** skeleton rows naming the operation, not spinners (op, clar).
- **Empty, each distinct:** no match for filters (name them + one "Clear filters"); no project in the
  chosen year; nothing inside the 40 km circle; place not in GA/SC (clar, onb).
- **Error:** what failed + how to recover; a failed AI call or asset never blanks the map or panel (hard).
- **Arrival:** straight into the ranked opportunities; no tour (onb "time to value").
- **Reload:** filters, year and selection in the URL; a mid-demo reload restores the scene (fue).

## Uncertainty and AI content — shown, never hidden
- Accuracy twice: line style (solid exact · dashed approximate) **and** a text label in list, detail and
  legend (col). Unknown locations are never drawn at invented coordinates: "Location unknown (n)" list.
- A pair takes the weaker accuracy of its two projects; an approximate "touching" reads "possibly
  touching" (clar) [own].
- Every project shows its source document + page. Savings always a range with assumptions **inline**,
  not on hover (dis).
- Brief header text label: **"AI-drafted from public plan data. Check before use."** (or "Template"),
  visible without scrolling; text, not colour or tooltip; the same wording everywhere. Facts cite a source or say "not in source documents";
  contacts are organisations/planning functions, never generated names. "Copy brief" — **no Send** button.
- Footer: "Independent student project; not affiliated with Dominion Energy, Georgia Power, Southern
  Company, GTC, MEAG or Sperry Tech. Estimates are for discussion only."

## Motion
- **One designed moment:** choosing an opportunity fits the map to the pair, 200–500 ms on the drawer
  curve `cubic-bezier(0.32,0.72,0,1)`; the pair gets a neutral outline, not a glow (cf, std).
- Slider, filters and keyboard actions: **no animation**; the map updates on every `input` (emil, apple).
- Durations: press 100–160 ms · tooltip 125–200 · dropdown 150–250 · sheet ≤ 500 · anything else < 300.
  Transform and opacity only; no `transition: all`, no `scale(0)`, no ease-in, no bounce (std).
  Easing out `cubic-bezier(0.23,1,0.32,1)`, in-out `(0.77,0,0.175,1)`.
- Hover effects only under `(hover: hover) and (pointer: fine)`. Reduced motion = fewer and gentler, not
  zero (map jumps instead of flying; fades replace slides); no global 0.01 ms kill switch (emil, aud).
- Never: pulsing markers, staged page-load sequences (reg, op).

## Themes
- Both designed; tokens remapped, never inverted (col). Default chosen from the scene: a lit demo room and
  a projector → **light** default [own]; dark via `prefers-color-scheme` + a toggle applied by
  `web/js/theme-init.js`, an **external** script loaded in `<head>` before the stylesheets paint (an inline
  script would break CSP `default-src 'self'`); no flash. No pure `#000`/`#fff`. Light-on-dark text gets slightly more
  line height and weight (typ). The basemap is drawn from the same tokens.

## Libraries (no build step; pick-ui-library is React-first, so these are outside its list — rule 4)
- **Map: Leaflet 1.9.4**, vendored. SVG renderer → tokens style lines, `dashArray` draws approximate
  lines, axe and the auditors can inspect features, markers take focus, the map prints. Leaflet renders
  strings passed to `bindTooltip` / `bindPopup` as HTML — always pass a DOM node filled with
  `textContent`; the malicious-string fixture runs through a tooltip in e2e. MapLibre rejected:
  WebGL canvas is invisible to the DOM, axe and keyboard; needs self-hosted glyphs; larger [own].
- **Basemap: local GeoJSON** (state + county outlines, city labels) coloured from tokens — no remote
  tiles at runtime (OSM's tile policy forbids bulk offline caching; the audit gate allows 0 external
  requests). CSP can then be `default-src 'self'`.
- **Controls:** native `<input type="range">` + `<output>` + `aria-valuetext` ("2029, 12 projects, 3
  overlaps"); search `<input type="search" list>` + `<datalist>` first, an ARIA 1.2 combobox only if
  needed; `<dialog>`, popover and a `role="status"` live region (op, a11y). No chart library; a per-year
  count strip, if any, is hand-written SVG with a matching `<table>` (visualize).
- **Icons:** a handful of inline SVGs in one stroke width (Tabler, MIT, pasted as SVG text) — no emoji,
  no icon font (cf, taste).
- **Motion:** CSS transitions, `@starting-style`, Web Animations API — no library.

## Scripted audit gate (merge gate; out-ranks visual judgment — Lucky website example)
Port the four website auditors from the founder's vault (`02_WEBSITE/build-notes/tools/audit-{contrast,
keyboard-motion,mobile-a11y,svg-geometry}.js`, read-only originals) into `tests/e2e/audits/` — their in-page JavaScript
runs unchanged inside Python Playwright's `page.evaluate` — and fix three flaws found in them: they scan
only inside `<main>` (put map and panels inside it); contrast assumes white when no background is set
(set `body` backgrounds; text over the map sits on ≥ 0.85-alpha backing); focus check accepts any
existing `box-shadow` (compare focused vs unfocused styles).
**States:** default · filters with no results · detail with brief · area explorer · a late year ·
an error. **Each at** 1440×900 and 390×844, light and dark.

| # | Check | Pass |
|---|---|---|
| 1 | Page + console errors across the demo path | 0 |
| 2 | Requests to anything but the local server | 0 |
| 3 | axe-core, WCAG 2.0/2.1 A + AA | 0 violations |
| 4 | Text contrast | ≥ 4.5:1 (≥ 3:1 only for ≥ 24 px or ≥ 18.66 px bold) |
| 5 | Lines, legend samples, focus rings, control borders | ≥ 3:1, both themes |
| 6 | Visible focus at every tab stop (no 25-stop cap) | 0 misses |
| 7 | Keyboard only: search a city → open top pair → read brief → export → change year with arrows → Esc | all pass; focus returns; no trap; no positive tabindex; skip link + target exist; ARIA refs resolve |
| 8 | Filter change updates a `role="status"` count | announced |
| 9 | Touch targets at 390 px | ≥ 44×44 (resize Leaflet zoom buttons) |
| 10 | Horizontal overflow at 768, 390 and 320 px | page width ≤ viewport + 1 px |
| 11 | Font floors | 11 functional · 12 body · 16 inputs on phone · 9 effective map labels |
| 12 | Longest real names + a 100-character test name | full text reachable, 0 overflow |
| 13 | Reduced motion | 0 hidden text; 0 endless animations |
| 14 | Motion lint | 0 `transition: all` / ease-in / layout-property transitions; UI ≤ 300 ms, sheet ≤ 500 |
| 15 | Code + copy lint | 0 colours outside `tokens.css`; in the product's own text (elements without `data-src`): 0 em/en dashes, 0 buzzwords; anywhere: 0 visible `undefined`, `NaN`, `null`, `[object` |
| 16 | Structure | one h1; no skipped heading levels; `lang`; `<title>`; named map region; every control labelled |
| 17 | AI and optional endpoints blocked | map and list still work, error shown, 0 uncaught errors |
| 18 | Speed and stability | main content < 2.5 s; slider response < 200 ms; layout shift < 0.1 |
| 19 | Print preview | no controls printed; filters, date, sources, full text included |
| 20 | impeccable `detect.mjs --json` (optional; run only after reading the script proves it writes nothing in the Lucky folder) | exit 0, or each finding verified / recorded false positive |
| 21 | Number of checks | never below the last accepted run; nothing weakened |

**Human checks:** squint test; colour-blind simulation + grayscale keep utilities, bands and line styles
apart; dashed lines readable on a phone; the AI label visible without scrolling; motion at 2–5× slow;
full copy read; the 3-minute demo by mouse, keyboard and touch in both themes; the venue projector.

## Critique procedure (Phase 4 design judge)
1. Auditors pass first. 2. Two assessments in parallel sub-agents — **A** design review before seeing
detector output (fit to GridLock, Nielsen's 10 heuristics 0–4, 8-item cognitive-load list, personas Alex
power user · Sam keyboard + screen reader · Casey phone; 2–3 strengths, 3–5 priority issues) and **B**
detector evidence. 3. Merge: score /40 (36+ excellent … < 12 critical), severities P0–P3 (anything a
user would contact support about ≥ P1). 4. Report, then 2–4 option questions. 5. Technical audit /20
(a11y, performance, responsiveness, theming, implementation integrity), kept separate. 6. Fix in order:
broken or misleading paths → missing states → layout drift → visuals and motion → cleanup; one fix brief
per surface. 7. Budget: one inspection round, one fix batch, at most one confirming round. 8. Final
review by a fresh reviewer, never the builder.
