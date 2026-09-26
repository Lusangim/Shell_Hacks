# DIRECTION — GridLock visual direction (locked 2026-09-26)

**The System Wall Map, with The Plan Sheet's working details.** Written by Claude from the direction round's
decision page (`decision-page.html`, `decision-payload.json`, `PRODUCT.md` in this folder).

## The founder's words
- "no we want the second option the system map remember the notion it wants it to be an interactive map"
- "but also have it take inspiration from the plan sheet a combination of both no need to run another
  design round direction just get it ready to start working"

The Notion Hacker Guide requires an **interactive** UI showing both utilities' planned projects and
visually highlighting overlaps — pan, zoom, click; never a static image.

## THESIS
The wall map every transmission planning office keeps, made live: line weight shows voltage, colour shows
utility, the state line is drawn heavy — and every opportunity reads like a page of the plans it came
from: labelled fields, a citation you can open, one highlighter mark on the pair you are looking at.

## OWN-WORLD
**Materials:** map paper, a legend box and title block, voltage line weights, named substations (Wall Map);
labelled fields, page citations, ink vs pencil, one highlighter mark, tally-board figures, hatched bands,
a status line that states every change (Plan Sheet and its six raises).

**Colour lives only on data.** Chrome and text stay achromatic (ink, pencil, rules); colour appears only on
map lines, band hatches and the single highlighter fill. Every colour is a token in `web/css/tokens.css`.

| Token | Light (projector default) | Dark (the wall map at night) |
|---|---|---|
| canvas (map paper) | `#f4f6f4` | `#16191c` |
| panel | `#ffffff` | `#1d2125` |
| ink (text, exact lines' casing, focus) | `#23282e` | `#e8ecef` |
| pencil (secondary text, approximate labels) | `#5b6670` | `#a7b1ba` |
| rule (hairlines, borders) | `#c3c9cf` | `#3a4148` |
| Georgia Power | `#004280` | `#b3d8ff` |
| MEAG Power | `#863e7f` | `#b071a9` |
| Dominion Energy SC | `#c04e29` | `#f78c67` |
| Georgia Transmission Corp. | `#24998d` | `#7ad0c5` |
| Minor utilities — Dalton Utilities, Georgia ITS (joint): 3 projects each, one shared colour, always named | `#74655b` | `#a6998f` |
| highlighter fill (behind ink text only) | `#f2e64d` | `#5a5210` with text `#f7f3cf` |

"Georgia Power (inferred)" uses Georgia Power's colour and always carries "(inferred)" in text.

**Palette check (Claude, 2026-09-26; `palette_check.py` + `palette_design.py` in this folder, an equivalent
of the dataviz validator, which was not found on disk):** every utility colour ≥ 3:1 against the canvas —
light 9.25 / 6.43 / 4.43 / **3.21** (GTC, the floor: never lighten it) / 5.15; dark 11.92 / 4.86 / 7.48 /
9.80 / 6.37. Lightness steps (CIELAB L*): light 28 / 38 / 48 / 57 / 44, dark 85 / 56 / 69 / 78 / 64 (GP /
MEAG / DESC / GTC / minor). Closest pair after colour-vision simulation (Machado 2009, CIE76 ΔE): light —
protan 9.9 (Georgia Power / MEAG), deutan 18.0, tritan 24.2; dark — 17.6 / 17.5 / 17.2. Ink on panel
14.85:1 (dark 13.63:1); pencil text 5.87:1 (7.44:1); highlight text on fill 11.45:1 (7.05:1).
Dominion Energy SC — in every cross-state pair — is the only warm hue.

**Lines.** Weight by voltage: 500 kV and up 6 px · 230 kV 4 px · 115 kV 3 px · 69 kV, lower or not stated
2 px (never thinner). Every project line gets a 1 px canvas-coloured casing so it holds 3:1 on a projector.
**Ink vs pencil:** an exact location is a solid line with an ink label; an approximate location is a dashed
line with a pencil label, on the map, in the list and in the detail; an unknown location is never drawn —
it is listed in the "Location unknown (n)" drawer with its reason.
**State line:** heavy ink long-dash-dot, labelled "SC" and "GA" on either side; counties as rule hairlines;
city labels in small caps.
**Named substations:** small ink squares, labelled from a mid zoom level.
**Distance bands** never by colour alone: an ink hatch density (touching solid · under 1.6 km dense ·
under 8 km medium · under 40 km sparse) + an ordered glyph + the text label, in list chips, the detail and
the print view.

**Type:** system stack only (`system-ui, -apple-system, "Segoe UI", sans-serif`); scale 12 / 14 / 16 / 20 /
24 px; field labels in small caps at 12 px with letter-spacing ≤ 0.05em (the title-block voice); every
figure `tabular-nums`, right-aligned, unit in a lighter weight (the tally-board raise).
**Shape:** radius 4 px controls, 8 px panels; the legend box and title block are ruled (1 px rule), not
shadowed.

## STORY
A planner walks up to the wall map, finds the border, puts a finger on the two lines that meet — and the
map answers: who owns each line, when each enters service, how far apart they are, where that is written
(document and page), how sure we are of the location, and what coordinating could save. GridLock is that
wall map, for two utilities' public plans at once.

## FIRST VIEWPORT
**1440 px:** the SC–GA border region full-bleed at wall-map scale (Savannah to Augusta in frame), light
paper. Docked on the left, a 420 px panel drawn as the map's **title block and legend**:
1. Title block: "GridLock", "Coordination opportunities", the loaded plan editions with their dates (from
   `/api/meta`), "N of M projects have no overlap within 40 km", and the one-line **status line**
   (`aria-live="polite"`, a plain sentence for every change).
2. Legend box (collapsible): utilities with swatch and name; voltage weights; ink = exact, pencil =
   approximate; band hatches and glyphs; the state line.
3. City search, then the filters (utility, voltage, year, type, band, cross-state).
4. The ranked list, read like the plan's summary table: rank, the two utilities, band chip, km, both
   in-service years, accuracy — figures right-aligned; rank 1 in bold; nothing selected until a click.
The **timeline slider** (in-service years 2026 to 2035, plus "All years") runs along the bottom edge of the
map. Selecting a pair (list row or map line) fits both projects in view (instant under reduced motion),
puts the **highlighter** behind the list row and behind printed labels on hairline leaders for both
projects, draws the nearest-points connector with its distance and band, and opens the pair detail.

**Pair detail = a two-column project sheet:** left the DESC project, right the Georgia project; labelled
fields (name verbatim, utility, in-service, voltage, type, cost or "not stated", accuracy, source as an
openable citation such as "SERTP 2025, p. 133"), then distance, band, why they touch, timeline, savings
range or its reason with the assumptions, and the coordination brief card.

**390 px:** the map fills the screen; the panel becomes a bottom sheet whose peek shows the title block,
the status line and the first two ranked rows; the legend opens from a "Legend" button; the timeline sits
above the sheet; every target ≥ 44 px.

## FORM
Roll seed key `3a040ed5` · scope: direction · impeccable Operate mode · dealt by impeccable.style's roll
service (pool `c3b204a1eed6`). Pick: **The System Wall Map** (impeccable's pick) combined with **The Plan
Sheet** (the roll's pick) and the six rules the declined worlds raised into it, on the founder's
instruction; no second round. Held-back directions were not shown.

## What the WEB lane must not miss
- Interactive map first: pan, zoom, click, keyboard; overlaps visibly highlighted.
- No colour literal outside `tokens.css`; both themes remap every token, the basemap included (no flash).
- The highlighter yellow is only ever a fill behind ink text — never a line or text colour. A selected row
  also gets a 3 px ink rule on its left edge, so selection never depends on colour.
- Keep the Georgia Transmission line colour as dark as specified (3.21:1 is the floor) and keep the 1 px
  casing on every project line.
- Utilities are named in every row, tooltip and legend; the two minor utilities share a colour but never a
  name.
- Unknown locations are never drawn at invented coordinates.
- The ranked list is a complete keyboard path that never needs the map; Tab can always leave the map.
- Tooltips and printed labels are DOM nodes filled with `textContent`; data strings stay verbatim (their
  dashes kept); the product's own words use no em or en dashes.
- Reduced motion honoured; local basemap only (no tiles); counties from the Census 2024 KML (T3.5).
