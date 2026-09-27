"""Route a line project along public HIFLD transmission lines between its two matched substations.

Plans name a line's end substations but never its route. When no single HIFLD line joins the two
names, GridLock may follow the existing HIFLD network between the two matched substations, like
directions along roads instead of a straight line across country. A route is used only when it is
plausibly the same line:
  - both substations are within 1.5 km of a network node,
  - every segment runs on lines of the project's voltage class (any class if the plan gives none),
  - the route passes no other named substation (unnamed taps and junctions are fine), and
  - the whole route is at most 1.5 times the straight distance.
Anything else stays a straight line and says so. The route is still an inference, never "exact".
"""

from __future__ import annotations

import heapq
import math
from collections import defaultdict

from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import transform
from shapely.strtree import STRtree

try:  # imported as pipeline.hifld_routes by tests, as hifld_routes when the build runs the scripts
    from pipeline.overlap_geometry import TO_GEO, TO_METRES
except ImportError:  # pragma: no cover - script mode
    from overlap_geometry import TO_GEO, TO_METRES

NODE_TOL_M = 100.0
END_TOL_M = 1500.0
MAX_DETOUR = 1.5


def volt_class(kv: float) -> str:
    """HIFLD's VOLT_CLASS bucket for a nominal voltage in kV."""
    if kv < 100:
        return "UNDER 100"
    if kv <= 161:
        return "100-161"
    if kv <= 287:
        return "220-287"
    if kv <= 345:
        return "345"
    return "500"


def _named(name: str | None) -> str | None:
    text = " ".join((name or "").upper().split())
    if not text or text.startswith(("TAP", "UNKNOWN", "NOT AVAILABLE")):
        return None
    return text


class HifldNetwork:
    """HIFLD lines as a graph: nodes are line ends (within NODE_TOL_M), edges are lines."""

    def __init__(self, features: list[dict]) -> None:
        self.xy: list[tuple[float, float]] = []
        self.names: list[set[str]] = []
        self._cells: dict[tuple[int, int], list[int]] = defaultdict(list)
        self.edges: list[tuple[int, int, float, str, list]] = []
        self.adj: dict[int, list[tuple[int, float, int]]] = defaultdict(list)
        for feature in features:
            geometry = feature.get("geometry")
            if not geometry or geometry["type"] != "LineString":
                continue
            props = feature.get("properties") or {}
            metres = transform(TO_METRES, LineString(geometry["coordinates"]))
            u = self._node(*metres.coords[0], props.get("SUB_1"))
            v = self._node(*metres.coords[-1], props.get("SUB_2"))
            if u == v:
                continue
            kv = props.get("VOLTAGE")
            vclass = volt_class(kv) if isinstance(kv, (int, float)) and kv > 0 else (props.get("VOLT_CLASS") or "?")
            edge = len(self.edges)
            self.edges.append((u, v, metres.length, vclass, [list(c) for c in geometry["coordinates"]]))
            self.adj[u].append((v, metres.length, edge))
            self.adj[v].append((u, metres.length, edge))
        self._tree = STRtree([Point(p) for p in self.xy]) if self.xy else None

    def _node(self, x: float, y: float, name: str | None) -> int:
        cx, cy = int(x // NODE_TOL_M), int(y // NODE_TOL_M)
        best, best_d = None, NODE_TOL_M
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for i in self._cells[(gx, gy)]:
                    d = math.hypot(self.xy[i][0] - x, self.xy[i][1] - y)
                    if d <= best_d:
                        best, best_d = i, d
        if best is None:
            best = len(self.xy)
            self.xy.append((x, y))
            self.names.append(set())
            self._cells[(cx, cy)].append(best)
        named = _named(name)
        if named:
            self.names[best].add(named)
        return best

    def _nearest(self, x: float, y: float) -> tuple[int, float]:
        i = int(self._tree.nearest(Point(x, y)))
        return i, math.hypot(self.xy[i][0] - x, self.xy[i][1] - y)

    def _shortest(self, src: int, dst: int, allowed: set[str] | None):
        dist, prev, heap = {src: 0.0}, {}, [(0.0, src)]
        while heap:
            d, node = heapq.heappop(heap)
            if node == dst:
                break
            if d > dist.get(node, math.inf):
                continue
            for nxt, weight, edge in self.adj[node]:
                if allowed is not None and self.edges[edge][3] not in allowed:
                    continue
                nd = d + weight
                if nd < dist.get(nxt, math.inf):
                    dist[nxt], prev[nxt] = nd, (node, edge)
                    heapq.heappush(heap, (nd, nxt))
        if dst not in dist:
            return None
        path, visited, node = [], [dst], dst
        while node != src:
            node, edge = prev[node]
            path.append(edge)
            visited.append(node)
        return dist[dst], path[::-1], visited[::-1]

    def route(self, points: list[tuple[float, float]], voltages: list[float]) -> MultiLineString | None:
        """Route through (lon, lat) substation points in order, or None when not confident."""
        if self._tree is None or len(points) < 2:
            return None
        allowed = {volt_class(kv) for kv in voltages if kv and kv > 0} or None
        parts, route_m, straight_m = [], 0.0, 0.0
        for start, end in zip(points, points[1:]):
            a, b = TO_METRES(*start), TO_METRES(*end)
            node_a, gap_a = self._nearest(*a)
            node_b, gap_b = self._nearest(*b)
            if max(gap_a, gap_b) > END_TOL_M or node_a == node_b:
                return None
            found = self._shortest(node_a, node_b, allowed)
            if found is None:
                return None
            length, path, visited = found
            if any(self.names[node] for node in visited[1:-1]):
                return None
            route_m += length
            straight_m += math.hypot(a[0] - b[0], a[1] - b[1])
            parts.extend(self.edges[edge][4] for edge in path)
            for point, node in ((start, node_a), (end, node_b)):
                corner = list(TO_GEO(*self.xy[node]))
                if (gap_a if node == node_a else gap_b) > 0:
                    parts.append([list(point), corner])
        if straight_m <= 0 or route_m / straight_m > MAX_DETOUR:
            return None
        return MultiLineString(parts)
