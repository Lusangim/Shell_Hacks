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
