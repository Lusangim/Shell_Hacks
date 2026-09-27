# UI-improvement pass with impeccable (GridLock, Claude Opus agent, after Codex delivers)

GridLock (ShellHacks 2026, Sperry Tech challenge) is a local web app. It finds where neighbouring electric
utilities' planned transmission projects come close in place and time, on a modern street map of Georgia
and South Carolina. It has a ranked list of pairs, the source document and page for every project, a
savings estimate and a guided tour. Codex built it and delivered commit `3551fdb` (tag `delivered`). The
founder asked for a UI-improvement pass with impeccable. You are that pass. There are no final judges:
Claude reviews everything else at the same time in its own copy (data, server, docs, scripts), then
reviews your diff and merges it. Refer to the user as "the founder".

## Where you work
- **Your copy:** `C:\Users\lucia\dev\gridlock-runs\final\ui`, on branch `ui/impeccable`. It is Codex's
  delivered commit `3551fdb`, plus GitHub main's setup scripts, plus Claude's data change (`data-c`),
  starting at `8b5598d`. Edit and commit only there. Never touch `C:\Users\lucia\dev\gridlock`
  (the Codex working copy), anything under OneDrive, or `%USERPROFILE%\.codex\`. Never push.
- **Python:** `$env:GRIDLOCK_PY` = `%USERPROFILE%\dev\gridlock-venv\Scripts\python.exe`. Windows PowerShell
  5.1: no `&&`; use absolute paths.
- **Run the app to look at it:** `$env:GRIDLOCK_GOOGLE='off'; $env:GRIDLOCK_AI='off'`, then
  `scripts\start.ps1 -Port 8801 -NoBrowser` in the background. Stop it when you finish, and prove it is
  yours first. Never open or read `gridlock-assets\google-maps-key.txt`.
- **Quick gate:** `$env:GRIDLOCK_TEST_PORT='8802'; scripts\quick-gate.ps1 -Repo <your copy>`. It also uses
  ports 11802 and 14802.
- **Screenshots:** Playwright Chromium is installed at `%USERPROFILE%\dev\ms-playwright`. Save to
  `C:\Users\lucia\dev\gridlock-runs\final\ui-shots\` as `before-<view>-<1440|390>-<light|dark>.png` and
  `after-...`.

## Read first
1. `reviews/2026-09-26-gridlock-build/design/DIRECTION-v2.md`: the visual contract. **The brief wins.**
2. `.claude/skills/gridlock-build/references/ui-contract.md` (+ `house-patterns.md`): tokens and audit
   thresholds.
3. `reviews/2026-09-26-gridlock-build/DELIVERY.md`: open findings. Every UI and design item there is your
   backlog.
4. `SPEC.md` § Boundaries and the glossary in `PROJECT-PROFILE.md`: honesty rules, one term per concept.
5. Impeccable, **read-only** from the founder's vault:
   `C:\Users\lucia\OneDrive\Desktop\Lucky Systems\.claude\skills\impeccable\`. Read SKILL.md, then the
   references for the commands you use (`critique.md`, `audit.md`, `polish.md`, `operate.md`,
   `craft-floor.md`, plus `layout`, `typeset`, `clarify`, `adapt` or `distill` as needed).

## Impeccable, safely
- The vault is read-only: never write inside it. Its scripts write only to `<your copy>\.impeccable\` and
  `~\.impeccable\`. Before running any of them, set `IMPECCABLE_NO_UPDATE_CHECK=1` (otherwise
  `context.mjs` calls impeccable.style) and `IMPECCABLE_NO_STALENESS_CHECK=1`.
- Add `.impeccable/` to `<your copy>\.git\info\exclude` so it is never committed.
- Run scripts as `node "<vault>\impeccable\scripts\<script>"` with cwd = your copy. Node 24 is installed;
  install nothing.
- Never run `npx`, `live`, hooks, `pin`, `init` or `document`, and create no PRODUCT.md or DESIGN.md.
  SPEC.md plus DIRECTION-v2 are the product context.

## The founder's ask: fixes and aesthetics
The founder: "also let the UI check potentially make UI improvements and aesthetics". So this pass does
more than fix defects. Make the app look and feel better too:
- typography hierarchy and rhythm;
- spacing and alignment;
- panel and list surfaces;
- the header and controls;
- icons;
- colour accents outside the utility palette;
- the tour card;
- empty and loading states;
- purposeful micro-interactions that respect `prefers-reduced-motion`.

Use impeccable's enhance commands where the critique supports them: `typeset`, `layout`, `colorize`,
`bolder` or `quieter`, `delight`, `animate`. The direction is to elevate the existing modern-map look,
not to replace it. It stays an Operate tool: scanning and clarity come before decoration.

## How (impeccable's bounded passes; mode Operate; refine and elevate, not replace)
1. **Setup:** run `context.mjs` once. With no PRODUCT.md, proceed as a refinement of the incumbent code.
2. **Evaluate once:**
   - Run `critique` across the demo path, plus `audit` including `scripts\detect.mjs --json web`.
   - Cover 1440 and 390 px, light and dark.
   - Views: first view · search · ranked pair list · pair detail · project detail with source document and
     page · savings estimate · guided tour · states (loading, empty, error, street-map file missing →
     outline fallback).
   - Take the "before" screenshots now.
3. **Fix and elevate in one batch:**
   - Run `polish` with the critique as its backlog, plus `layout`, `typeset`, `clarify`, `adapt` or
     `distill` where the critique points.
   - Add the aesthetic improvements the critique supports (see "The founder's ask" above).
   - Include the two open P3 items from DELIVERY.md (verify each first):
     - JUD-03: selected map labels wrap into narrow columns (selected pair map, 1440 light and dark;
       `reviews/2026-09-26-gridlock-build/judge-user-design-r1/top-pair-stable-light.png`);
     - JA11Y-03: a successful brief retry loses keyboard focus (brief error and retry, 1440 light;
       `reviews/2026-09-26-gridlock-build/judge-a11y-r2/1440-light-brief-retry-focus-lost.png`).
   - Claude's preview notes (verify each first):
     - ranked-list rows print long verbatim names plus source text and read dense;
     - long map labels;
     - the header buttons wrap at 1440 ("Take the tour");
     - the tour card's position;
     - check that scrolling the detail panel never moves the map;
     - approximate *points* (84 filled circle markers, `web/js/map.js:60` dashArray) probably look the
       same as exact ones, because a dash on a small filled dot barely shows. Give approximate points a
       colour-independent look that is clear at a glance (for example a hollow ring), and add a small map
       key: solid line = exact, dashed = approximate, dot = single site.
4. **Confirm with at most one more inspection round**, then stop polishing.

## Hard rules
- **Elevate, don't replace.** Keep DIRECTION-v2's world: the modern Google-style map, the utility
  palette, the layout model, behaviour and routes. Within that world, aesthetic improvements are
  wanted, and token values may be refined as long as every audit threshold still passes.
- **Data honesty:**
  - Never change a number, name, date, distance, source text, document or page.
  - Keep "estimate", "AI-drafted" and uncertainty labels visible.
  - Add no claims. Copy edits are for clarity and glossary terms only, and follow the readable-text rule:
    answer first, ≤ 3 short bullets, raw detail behind a disclosure, no IDs, enum values or paths on
    screen.
- **Utility colours:** the colours are colour-blind-checked (lightness-stepped). Change them only if an
  audit threshold fails, then re-run the palette and contrast audits. Each utility line stays ≥ 3:1
  against the map's land colour in both themes.
- **Accessibility, WCAG 2.2 AA:**
  - a full keyboard path without the map, and visible focus;
  - targets ≥ 24 px (≥ 44 px on phone);
  - text contrast ≥ 4.5:1 and UI contrast ≥ 3:1;
  - `prefers-reduced-motion` honoured, and live regions kept.
- **Offline and CSP:**
  - works with non-local requests blocked;
  - no CDN, no internet fonts, no new dependency;
  - the CSP is unchanged.
- **Stability:** no layout shift (the CLS audit stays green); no heavy animation.
- **Files:** `web/` plus tests for what you change. Change nothing under `pipeline/`, `server/` or
  `data/`. Claude edits those in parallel, so staying inside `web/` keeps the merge clean. A fix that
  needs server text or data becomes an item for Claude in your report.
- **New data fields, already in your copy** (Claude's founder-approved data change; see
  `docs/METHODOLOGY.md` § How project locations are drawn):
  - `Project.town_only`: true when the only location is a Census town centre (43 projects);
  - `Overlap.town_capped`: true when a town-centre location alone would have made a pair look closer,
    so the pair counts as "under 40 km" (15 pairs, each with a note in `touch_detail`).

  Render them clearly and without relying on colour:
  - a distinct map look for town-only projects, such as a dashed hollow ring (exact = solid dot,
    approximate = hollow ring);
  - "Town-level location" wording in the tooltip, list row and project detail;
  - a visible note on capped pairs;
  - a small map key covering solid = exact, dashed or hollow = approximate, town only.

  Add e2e checks for each. Some routed projects are now MultiLineStrings; make sure their highlight and
  fit-to-bounds work.
- **Savings text is changing in parallel.** At the founder's request, Claude is replacing the savings
  estimate and adding it to the ranking. Leave these strings to Claude, who updates them after your
  merge:
  - the savings assumption labels in `web/js/overlap-detail.js`, `web/js/export.js` and
    `web/js/brief.js` (the `coordination_fraction_v1` / `line_cost_per_mile_v1` maps);
  - the tour's "How pairs are ranked" step text in `web/js/tour-content.js`.

  Styling around them is yours.
- **Tests:** never weaken, skip or delete a check.
  - If an assertion pins a layout detail you changed on purpose, update it so it still checks the rule,
    and list the change with its reason.
  - Add a check for each behaviour you add.

## Done when
- The quick gate is green on `ui/impeccable`: quote suite / shell / audit totals against the baseline.
- There are before and after screenshots of every changed view (1440 and 390, light and dark).
- The work is committed as `UI: <what>`, a few coherent commits, each ending with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Report (≤ 60 lines):**
  - what changed and why, per view;
  - the critique scores before and after;
  - the audit and detector results;
  - each test you changed and why;
  - items for Claude (server or data);
  - what you chose not to do.
- **No time limit** (founder). You are done when the work is done:
  - every item in the backlog above is fixed or explained;
  - the one evaluate → fix-in-one-batch → at-most-one-confirmation cycle is complete;
  - the quick gate is green.

  Don't start open-ended extra polishing rounds beyond that. Impeccable's own rule is bounded passes,
  not a loop.
