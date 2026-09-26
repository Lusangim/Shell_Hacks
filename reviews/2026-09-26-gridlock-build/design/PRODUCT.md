# Product

<!-- impeccable:product-schema 1 -->

Written 2026-09-26 by the gridlock-design agent for impeccable's direction round (SPEC Q9). Every fact
below is taken from `SPEC.md` v3 (features decided by the founder, 2026-09-26), `PROJECT-PROFILE.md`,
`gridlock-data/README.md` and the UI contract. No interview round was run in this file: the founder
had already decided users, features and constraints in SPEC.md, and this agent has no question tool of
its own. Lines marked (inferred) are this agent's reading, not a founder statement. This file lives in
the design folder, not at the repo root, so no other lane's files change; the round's scripts find it
through `IMPECCABLE_CONTEXT_DIR`.

## Platform

web

## Stack

Decided in SPEC.md: static HTML + CSS + vanilla JS ES modules, no build step; Leaflet 1.9.4 vendored
(SVG renderer); local GeoJSON basemap (state and county outlines, city labels), no remote tiles; FastAPI
on 127.0.0.1 behind it. System font stack only.

## Users

- A transmission planner at a utility, a regional planning forum (SERTP), or a state regulator, asking
  "where could neighbouring utilities share crews, equipment, land and permits?"
- Judges: Round 1 is one general judge with a 3-minute live demo at the team's table; Sperry Tech
  judges its challenge separately; Round 2 is 3 to 5 minutes for top projects.

## Product Purpose

GridLock places two neighbouring utilities' public planned transmission projects on one map, finds the
pairs from different utilities whose nearest points are within 40 km and whose timelines overlap, and
ranks them as coordination opportunities. Scope: Georgia and South Carolina; the core story is the
SC to GA border (Savannah, Augusta): Dominion Energy South Carolina against Georgia Power, Georgia
Transmission Corp. and MEAG Power. Success, in the founder's words: "complete from front to backend ...
working with no bugs and have a clean UI".

## Positioning

The mechanism: every project keeps its source document and page and an accuracy label (exact,
approximate, unknown), every pair is placed in one of four distance bands (touching, under 1.6 km,
under 8 km, under 40 km) and ranked by a transparent score (band, timeline, accuracy, cross-state
weight; savings are shown, not scored), across a state line, from public filings only.
Prior art (SPEC.md): PaverOps does street-level project sharing inside one membership; GridLock does it
for transmission, across state lines, from public filings.

## Operating Context

- Source documents: the DESC SCRTP 2026 to 2030 project list (54 projects, one per PDF page) and the
  SERTP 2025 Regional Transmission Plan (Southern area projects from p. 60).
- Planners work with plan PDFs, system maps, one-line diagrams and spreadsheets (inferred).
- The demo runs on a laptop at a table in a lit hall, possibly on a venue projector (UI contract
  chooses a light default from that scene).

## Capabilities and Constraints

Decided features (all in scope): map with both utilities' projects; overlap detection by distance and
timeline; ranked list; savings range with its assumptions on every overlap (or the reason there is
none); timeline slider; source document and page per project; accuracy label; city search; filters
(utility, voltage, year, project type, distance band); CSV export and print to PDF; pick-an-area
explorer (40 km circle); AI-drafted coordination brief per overlap (or a template brief).
Constraints: works offline and with no AI access; 0 external requests at runtime; WCAG 2.1 AA; 1440 and
390 px, light and dark; data shown verbatim (project names keep their dashes); unknown locations are
never drawn at invented coordinates.
Terminology (glossary, PROJECT-PROFILE.md): project, utility, overlap, coordination opportunity,
distance band, why they touch, in-service year, accuracy, source, savings estimate, coordination brief,
cross-state.

## Brand Commitments

Name: GridLock. No logo, palette or typeface has been committed. The UI contract fixes the system font
stack, the token roles, the utility-palette rules and the copy rules (no em or en dashes in the
product's own words, no buzzwords, no "BETA" stamps).

## Evidence on Hand

Data pack v0 (2026-09-26 01:30, `gridlock-data/README.md`): 230 GA/SC projects kept, 181 placed (42
exact, 139 approximate), 49 unknown; 477 pairs within 40 km, 44 cross-state. These counts will change
as the pipeline is rebuilt; nothing here may be quoted as final. No testimonials, customers,
endorsements or measured savings exist and none may be shown.

## Product Principles

1. Show the source: every fact on screen can be traced to a document and page, or says it cannot.
2. Uncertainty is visible: approximate stays approximate, unknown stays unknown, estimates say estimate.
3. The ranked opportunity comes first: arrival goes straight to the ranked pairs, no tour.
4. The tool should disappear into the task (impeccable Operate mode).

## Accessibility & Inclusion

WCAG 2.1 AA via the UI contract's scripted audit gate: text 4.5:1, lines and controls 3:1 in both
themes, colour never the only code (utilities, bands and accuracy also carry text, line style or
glyph), keyboard path without the map, 44 px touch targets at 390 px, reduced motion honoured.
