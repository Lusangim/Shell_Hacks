"""Read-only measurement: can GridLock's straight-line projects follow real HIFLD lines?

For every project whose map line is a straight line between its two named substations, route
between the same two end points along the public HIFLD transmission-line network (shortest path
over real lines, not across open land). Report how many find a plausible real route, how far the
straight line was from it, and how pair distances, bands and the ranking would change.
Nothing in the repository is modified.
"""
from __future__ import annotations

import csv
import heapq
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from shapely.geometry import LineString, MultiLineString, Point, shape
from shapely.ops import transform
from shapely.strtree import STRtree

SNAP = Path(sys.argv[1])
OUT = Path(sys.argv[2])
NODE_TOL = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0   # m: HIFLD line ends this close are one node
END_TOL = 1500.0      # m: a project end must be this close to a network node
MAX_RATIO = 1.5       # a real route at most 1.5x the straight distance counts as plausible
sys.path.insert(0, str(SNAP / "pipeline"))
from overlap_geometry import TO_GEO, TO_METRES, band_for, nearest_point_distance_m  # noqa: E402

OUT.mkdir(parents=True, exist_ok=True)
BAND_W = {"touching": 4, "lt_1_6km": 3, "lt_8km": 2, "lt_40km": 1}


def volt_class(kv: float) -> str:
    if kv < 100:
        return "UNDER 100"
    if kv <= 161:
        return "100-161"
    if kv <= 287:
        return "220-287"
    if kv <= 345:
        return "345"
    return "500"


def unnamed(name: str) -> bool:
    n = (name or "").upper()
    return not n or n.startswith(("TAP", "UNKNOWN", "NOT AVAILABLE"))


# ---------- network from HIFLD ----------
hifld = json.load(open(SNAP / "data/raw/hifld_lines_ga_sc.geojson", encoding="utf-8"))["features"]
nodes_xy: list[tuple[float, float]] = []
node_names: list[set[str]] = []
grid: dict[tuple[int, int], list[int]] = defaultdict(list)


def node_for(x: float, y: float, name: str) -> int:
    cx, cy = int(x // NODE_TOL), int(y // NODE_TOL)
    best, best_d = None, NODE_TOL
    for gx in (cx - 1, cx, cx + 1):
        for gy in (cy - 1, cy, cy + 1):
            for i in grid[(gx, gy)]:
                d = ((nodes_xy[i][0] - x) ** 2 + (nodes_xy[i][1] - y) ** 2) ** 0.5
                if d <= best_d:
                    best, best_d = i, d
    if best is None:
        best = len(nodes_xy)
        nodes_xy.append((x, y))
        node_names.append(set())
        grid[(cx, cy)].append(best)
    if not unnamed(name):
        node_names[best].add(name.upper())
    return best


edges = []   # (u, v, length_m, feature index, volt class)
adj: dict[int, list[tuple[int, float, int]]] = defaultdict(list)
vc_counter = Counter()
for i, f in enumerate(hifld):
    g = shape(f["geometry"])
    gm = transform(TO_METRES, g)
    (x1, y1), (x2, y2) = gm.coords[0], gm.coords[-1]
    p = f["properties"]
    u = node_for(x1, y1, p.get("SUB_1") or "")
    v = node_for(x2, y2, p.get("SUB_2") or "")
    if u == v:
        continue
    kv = p.get("VOLTAGE")
    vc = volt_class(kv) if isinstance(kv, (int, float)) and kv > 0 else (p.get("VOLT_CLASS") or "?")
    vc_counter[vc] += 1
    e = len(edges)
    edges.append((u, v, gm.length, i, vc))
    adj[u].append((v, gm.length, e))
    adj[v].append((u, gm.length, e))

node_tree = STRtree([Point(xy) for xy in nodes_xy])


def nearest_node(x: float, y: float) -> tuple[int, float]:
    i = int(node_tree.nearest(Point(x, y)))
    return i, ((nodes_xy[i][0] - x) ** 2 + (nodes_xy[i][1] - y) ** 2) ** 0.5


def dijkstra(src: int, dst: int, allowed: set[str] | None):
    dist = {src: 0.0}
    prev: dict[int, tuple[int, int]] = {}
    heap = [(0.0, src)]
    while heap:
        d, n = heapq.heappop(heap)
        if n == dst:
            break
        if d > dist.get(n, float("inf")):
            continue
        for m, w, e in adj[n]:
            if allowed is not None and edges[e][4] not in allowed:
                continue
            nd = d + w
            if nd < dist.get(m, float("inf")):
                dist[m] = nd
                prev[m] = (n, e)
                heapq.heappush(heap, (nd, m))
    if dst not in dist:
        return None
    path_edges, n = [], dst
    while n != src:
        n, e = prev[n]
        path_edges.append(e)
    path_edges.reverse()
    return dist[dst], path_edges


# ---------- the straight-line projects ----------
features = json.load(open(SNAP / "data/build/projects.geojson", encoding="utf-8"))["features"]
by_id = {f["properties"]["id"]: f for f in features}
straight = [f for f in features if (f["properties"].get("location_source") or "").startswith("Straight line")]

rows, routed_geom = [], {}
for f in straight:
    p = f["properties"]
    pts = [transform(TO_METRES, Point(c)).coords[0] for c in f["geometry"]["coordinates"]]
    kvs = [k for k in (p.get("voltage_kv") or []) if isinstance(k, (int, float)) and k > 0]
    allowed = {volt_class(k) for k in kvs} or None
    town_end = "Census town" in (p.get("location_source") or "")
    seg_results, ok, reason = [], True, ""
    for a, b in zip(pts, pts[1:]):
        na, da = nearest_node(*a)
        nb, db = nearest_node(*b)
        straight_m = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        if max(da, db) > END_TOL or na == nb:
            ok, reason = False, "end not on the line network"
            break
        res_v = dijkstra(na, nb, allowed) if allowed else None
        res_any = dijkstra(na, nb, None)
        if res_any is None:
            ok, reason = False, "no connected path"
            break
        res = res_v or res_any
        length, path = res
        mids = set()
        for e in path[:-1]:
            pass
        # named substations passed through (not the two ends)
        visited = [na]
        for e in path:
            u, v = edges[e][0], edges[e][1]
            visited.append(v if visited[-1] == u else u)
        mids = set().union(*(node_names[n] for n in visited[1:-1])) if len(visited) > 2 else set()
        # short connectors keep the project's own end points (the matched substations) on the route
        connectors = [LineString([TO_GEO(*a), TO_GEO(*nodes_xy[na])]), LineString([TO_GEO(*nodes_xy[nb]), TO_GEO(*b)])]
        seg_results.append(dict(straight_m=straight_m, length=length, hops=len(path), path=path,
                                voltage_matched=res_v is not None, snap_m=max(da, db),
                                named_mids=sorted(mids), connectors=[c for c in connectors if c.length > 0]))
    if not ok:
        rows.append(dict(id=p["id"], utility=p["utility"], type=p.get("project_type"), name=p["name"],
                         category=reason, ratio="", hops="", named_mids="", max_offset_km="",
                         voltage_matched="", town_end=town_end))
        continue
    total_straight = sum(s["straight_m"] for s in seg_results)
    total_len = sum(s["length"] for s in seg_results)
    ratio = total_len / total_straight if total_straight else float("inf")
    hops = sum(s["hops"] for s in seg_results)
    mids = sorted(set().union(*(set(s["named_mids"]) for s in seg_results)))
    vmatch = all(s["voltage_matched"] for s in seg_results) if allowed else None
    lines = [LineString(hifld[edges[e][3]]["geometry"]["coordinates"]) for s in seg_results for e in s["path"]]
    lines += [c for s in seg_results for c in s["connectors"]]
    route = MultiLineString(lines)
    off = transform(TO_METRES, route).hausdorff_distance(transform(TO_METRES, shape(f["geometry"])))
    if ratio <= MAX_RATIO and not mids and not town_end and vmatch is not False:
        category = "direct real line" if hops == len(seg_results) else "real route via taps"
        routed_geom[p["id"]] = route
    elif ratio <= MAX_RATIO and not town_end:
        category = "plausible, but passes other substations or other voltage"
    else:
        category = "only a long detour" if not town_end else "an end is a town centre"
    rows.append(dict(id=p["id"], utility=p["utility"], type=p.get("project_type"), name=p["name"],
                     category=category, ratio=round(ratio, 2), hops=hops, named_mids="; ".join(mids[:4]),
                     max_offset_km=round(off / 1000, 2), voltage_matched=vmatch, town_end=town_end))

with open(OUT / f"routes-tol{int(NODE_TOL)}.csv", "w", newline="", encoding="utf-8") as h:
    w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# ---------- effect on pairs ----------
overlaps = json.load(open(SNAP / "data/build/overlaps.json", encoding="utf-8"))
old = {o["id"]: o for o in overlaps}
placed = [f for f in features if f["geometry"]]
geom = {f["properties"]["id"]: (routed_geom.get(f["properties"]["id"]) or shape(f["geometry"])) for f in placed}
props = {f["properties"]["id"]: f["properties"] for f in placed}


def tfactor(a, b):
    ya, yb = a.get("year"), b.get("year")
    if not ya or not yb:
        return 0.3
    return {0: 1.0, 1: 0.7, 2: 0.4}.get(abs(ya - yb), 0.1)


acc_f = {"exact": 1.0, "approximate": 0.8}
new_pairs = {}
for rid in routed_geom:
    for oid, og in geom.items():
        if oid == rid or props[oid]["utility"] == props[rid]["utility"]:
            continue
        pid = "__".join(sorted((rid, oid)))
        if pid in new_pairs:
            continue
        d = nearest_point_distance_m(geom[rid], og)
        band = band_for(d)
        a, b = props[rid], props[oid]
        cs = bool(a.get("state") and b.get("state") and a["state"] != b["state"])
        score = None
        if band:
            score = round(BAND_W[band] * tfactor(a, b) * acc_f[a["accuracy"]] * acc_f[b["accuracy"]] * (1.5 if cs else 1.0), 3)
        new_pairs[pid] = dict(distance_km=d / 1000, band=band, score=score)

changed = Counter()
examples = []
merged = {k: dict(score=v["score"], distance_km=v["distance_km"], band=v["band"]) for k, v in old.items()}
for pid, n in new_pairs.items():
    o = old.get(pid)
    if o is None and n["band"]:
        changed["new pair within 40 km"] += 1
        merged[pid] = n
    elif o is not None and not n["band"]:
        changed["pair drops out (40 km or more)"] += 1
        merged.pop(pid, None)
    elif o is not None:
        if n["band"] != o["band"]:
            changed[f"band {o['band']} -> {n['band']}"] += 1
            if o["rank"] <= 50:
                examples.append((o["rank"], pid, o["band"], n["band"], round(o["distance_km"], 2), round(n["distance_km"], 2)))
        else:
            changed["same band"] += 1
        merged[pid] = n
old_top = [o["id"] for o in sorted(overlaps, key=lambda o: o["rank"])][:20]
new_rank = sorted(merged, key=lambda k: (-merged[k]["score"], merged[k]["distance_km"], k))
new_top = new_rank[:20]
summary = dict(
    node_tolerance_m=NODE_TOL, hifld_lines=len(hifld), network_nodes=len(nodes_xy), network_edges=len(edges),
    straight_line_projects=len(straight),
    by_category=Counter(r["category"] for r in rows),
    by_category_rebuild_or_reconductor=Counter(r["category"] for r in rows if r["type"] in ("rebuild_line", "reconductor")),
    routed=len(routed_geom),
    median_ratio_routed=sorted(r["ratio"] for r in rows if r["id"] in routed_geom)[len(routed_geom) // 2] if routed_geom else None,
    max_offset_km_routed=sorted((r["max_offset_km"] for r in rows if r["id"] in routed_geom), reverse=True)[:5],
    pair_changes=changed, pairs_total_before=len(overlaps), pairs_total_after=len(merged),
    top20_kept=len(set(old_top) & set(new_top)), rank1_before=old_top[0], rank1_after=new_top[0],
    band_change_examples_top50=sorted(examples)[:12],
)
json.dump(summary, open(OUT / f"summary-tol{int(NODE_TOL)}.json", "w", encoding="utf-8"), indent=1, default=str)
print(json.dumps(summary, indent=1, default=str))
