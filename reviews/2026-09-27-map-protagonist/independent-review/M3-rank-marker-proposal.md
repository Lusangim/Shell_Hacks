# M3 rank-marker patch proposal

Prepared read-only against product files on 2026-09-27. This proposal is not applied or tested.

The helper takes Cartesian GeoJSON geometries. The integration projects into Leaflet's EPSG:3857
plane, where the map draws straight segments, then unprojects the nearest-points midpoint.
This is a visual anchor only: it does not calculate, change or replace the API's distance or score.
If a selected project's geometry is missing or unsupported, no marker is drawn.

The helper considers interior segment intersections before endpoint projections. Consequently,
crossing lines anchor at their actual crossing, and collinear/degenerate cases are covered without
connecting unrelated MultiLineString parts. Ties use the first valid candidate in source order.
Runtime is O(number of segments A × number of segments B), once per selection/style refresh.

## Proposed helper: web/js/nearest-geometry.js

```javascript
// Cartesian coordinates only; callers choose the display projection.
function segments(geometry) {
  const valid = (point) => Array.isArray(point) && point.length >= 2
    && Number.isFinite(point[0]) && Number.isFinite(point[1]);
  if (geometry?.type === "Point") return valid(geometry.coordinates)
    ? [[geometry.coordinates, geometry.coordinates]] : [];
  const lines = geometry?.type === "LineString" ? [geometry.coordinates]
    : geometry?.type === "MultiLineString" ? geometry.coordinates : [];
  if (!Array.isArray(lines)) return [];
  return lines.flatMap((line) => {
    if (!Array.isArray(line)) return [];
    if (line.length === 1 && valid(line[0])) return [[line[0], line[0]]];
    return line.slice(1).flatMap((point, index) => valid(line[index]) && valid(point)
      ? [[line[index], point]] : []);
  });
}

const subtract = (a, b) => [a[0] - b[0], a[1] - b[1]];
const cross = (a, b) => a[0] * b[1] - a[1] * b[0];
const at = (a, delta, t) => [a[0] + delta[0] * t, a[1] + delta[1] * t];

function projectOnSegment(point, a, b) {
  const delta = subtract(b, a);
  const lengthSquared = delta[0] ** 2 + delta[1] ** 2;
  if (lengthSquared === 0) return a;
  const offset = subtract(point, a);
  const t = Math.max(0, Math.min(1,
    (offset[0] * delta[0] + offset[1] * delta[1]) / lengthSquared));
  return at(a, delta, t);
}

export function nearestGeometryMidpoint(first, second) {
  let best = null;
  let minimum = Infinity;
  const firstSegments = segments(first);
  const secondSegments = segments(second);
  for (const [a, b] of firstSegments) {
    for (const [c, d] of secondSegments) {
      const ab = subtract(b, a);
      const cd = subtract(d, c);
      const denominator = cross(ab, cd);
      if (denominator !== 0) {
        const offset = subtract(c, a);
        const t = cross(offset, cd) / denominator;
        const u = cross(offset, ab) / denominator;
        if (t >= 0 && t <= 1 && u >= 0 && u <= 1) return at(a, ab, t);
      }
      const candidates = [[a, projectOnSegment(a, c, d)], [b, projectOnSegment(b, c, d)],
        [projectOnSegment(c, a, b), c], [projectOnSegment(d, a, b), d]];
      for (const [p, q] of candidates) {
        const distanceSquared = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2;
        if (distanceSquared < minimum) {
          minimum = distanceSquared;
          best = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
        }
      }
    }
  }
  return best;
}
```

## map.js integration

Add the helper import:

```javascript
import { nearestGeometryMidpoint } from "./nearest-geometry.js";
```

In `initializeMap`, after creating the halo pane:

```javascript
map.createPane("rankPane").style.zIndex = 620;
map.getPane("rankPane").style.pointerEvents = "none";
```

Add `pairRankMarker: null` beside `haloLayer` in `web/js/state.js`.
Add the following functions in `map.js` alongside `drawHalo`:

```javascript
function projectedGeometry(geometry) {
  if (!geometry) return null;
  const point = (coordinate) => {
    if (!Array.isArray(coordinate) || !Number.isFinite(coordinate[0])
      || !Number.isFinite(coordinate[1])) return null;
    const projected = L.CRS.EPSG3857.project(L.latLng(coordinate[1], coordinate[0]));
    return [projected.x, projected.y];
  };
  if (geometry.type === "Point") return { type: "Point", coordinates: point(geometry.coordinates) };
  if (geometry.type === "LineString") return {
    type: "LineString", coordinates: geometry.coordinates.map(point),
  };
  if (geometry.type === "MultiLineString") return {
    type: "MultiLineString", coordinates: geometry.coordinates.map((line) => line.map(point)),
  };
  return null;
}

function drawRankMarker(overlap, layers) {
  state.pairRankMarker?.remove();
  state.pairRankMarker = null;
  if (!overlap || !Number.isInteger(overlap.rank) || overlap.rank < 1 || layers.length !== 2) return;
  const midpoint = nearestGeometryMidpoint(
    projectedGeometry(layers[0].feature.geometry), projectedGeometry(layers[1].feature.geometry));
  if (!midpoint) return;
  const location = L.CRS.EPSG3857.unproject(L.point(midpoint[0], midpoint[1]));
  const label = document.createElement("span");
  label.textContent = String(overlap.rank);
  label.dataset.src = "rank";
  const icon = L.divIcon({ html: label, className: "pair-rank-marker",
    iconSize: [36, 36], iconAnchor: [18, 18] });
  state.pairRankMarker = L.marker(location, {
    icon, pane: "rankPane", interactive: false, keyboard: false,
  }).addTo(state.map);
  const element = state.pairRankMarker.getElement();
  element.dataset.testid = "pair-rank-marker";
  element.setAttribute("aria-hidden", "true");
}
```

Call `drawRankMarker(null, [])` immediately after `drawHalo([])` in `renderMap`.
Call `drawRankMarker(overlap, selected)` after `drawHalo(selected)` in `highlightPair`.
Clear the marker before the early return in `highlightPair` if no project layer exists:

```javascript
if (!state.projectLayers) { drawRankMarker(null, []); return; }
```

`refreshProjectStyles` already calls `highlightPair`, so theme changes rebuild the marker while its
colours also update directly through tokens. Existing halos, labels and selected line styling stay intact.
For a pair outside filters, this follows existing highlight behavior: do not invent geometry for missing layers.

## CSS proposal

Use dedicated marker tokens in `tokens.css`. Suggested light and dark values are the same because the
founder's marker is dark in both themes; a panel-coloured ring separates it from the dark basemap.
These values require the existing contrast audit; no contrast measurement has been run here.

```css
/* Add to both theme blocks in tokens.css. */
--rank-marker: #23282e;
--rank-marker-ink: #ffffff;
```

```css
/* protagonist.css */
.pair-rank-marker {
  display: grid;
  place-items: center;
  border: 2px solid var(--panel);
  border-radius: 50%;
  background: var(--rank-marker);
  color: var(--rank-marker-ink);
  box-shadow: var(--card-shadow);
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  pointer-events: none;
}
```

## Tests to write and run before applying product changes

Add tests to `tests/e2e/test_map_protagonist.py` (same browser fixture and port 8779 as the app suite).
Import the pure helper with `page.evaluate("async cases => { const module = await import('/web/js/nearest-geometry.js'); ... }")`.
Use these hand-calculated fixtures; compare both coordinates with `pytest.approx`, never compute expected
points by calling the production algorithm:

| A | B | Expected midpoint | Defect caught |
|---|---|---|---|
| Point `[0,0]` | Point `[4,2]` | `[2,1]` | coordinate order / midpoint |
| Point `[2,3]` | Line `[[0,0],[4,0]]` | `[2,1.5]` | interior perpendicular projection |
| Point `[7,3]` | Line `[[0,0],[4,0]]` | `[5.5,1.5]` | endpoint clamping |
| Line `[[-2,-2],[2,2]]` | Line `[[-2,2],[2,-2]]` | `[0,0]` | crossing inside both segments |
| Line `[[0,0],[4,0]]` | Line `[[2,0],[6,0]]` | `[4,0]` | collinear overlapping segments; deterministic tie |
| Line `[[0,0],[4,0]]` | Line `[[0,2],[4,2]]` | `[0,1]` | parallel non-crossing lines |
| Line `[[1,1],[1,1]]` | Point `[3,1]` | `[2,1]` | zero-length segment |
| MultiLine `[[[0,0],[1,0]],[[9,0],[10,0]]]` | Point `[5,1]` | `[3,0.5]` | no invented connection across parts |
| `null` | Point `[1,1]` | `null` | no invented unknown location |
| Line `[]` | Point `[1,1]` | `null` | empty geometry |

The MultiLine fixture intentionally differs from flattening into one line, which incorrectly produces
`[5,0.5]`. The overlapping fixture currently returns `[4,0]` due to source-order candidates; any valid point
in the overlap is geometrically correct, but the explicit expectation makes tie behavior reproducible.

One real browser journey should additionally assert:

1. Initial state contains no rank marker.
2. Open first pair; exactly one marker contains the API's rank, has `aria-hidden="true"`, has no
   nonnegative `tabindex`, and has `pointer-events: none`.
3. Existing selected features still identify exactly the pair's two IDs, with their utility colours;
   existing halo remains present. Compare the marker's map coordinate to a synthetic routed geometry pair
   with an off-centre crossing to detect accidentally using the union bounding-box center.
4. Select a second pair; still exactly one marker and its rank changes.
5. Change theme; still exactly one marker with readable audited text and ring.
6. Navigate to an invalid pair hash; marker disappears with the selection. Refresh filters so neither
   project is rendered; marker disappears without inventing fallback coordinates.

No test, server, browser or product edit was run for this proposal.
