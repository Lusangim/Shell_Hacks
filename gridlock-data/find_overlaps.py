"""Find and rank coordination opportunities between utilities.

Input:  projects.geojson (from place_projects.py)
Output: overlaps.json - every pair of projects from DIFFERENT utilities within 40 km, ranked.

Distance = closest points between the two geometries (not centres), measured in metres
in an equal-area projection (EPSG:5070).
"""
import json
from shapely.geometry import shape
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer

BANDS = [  # (max metres, band id, label, what can be shared, weight)
    (0,      "touching", "Touching / crossing", "Must coordinate: outage timing, crossing structures", 4),
    (1600,   "lt_1_6km", "Under 1.6 km", "Share land: right-of-way, access roads, permits", 3),
    (8000,   "lt_8km",   "Under 8 km", "Share site logistics: laydown yards, deliveries", 2),
    (40000,  "lt_40km",  "Under 40 km", "Share crews and equipment", 1),
]
ACCURACY_FACTOR = {"exact": 1.0, "approximate": 0.8}

to_m = Transformer.from_crs(4326, 5070, always_xy=True).transform
feats = [f for f in json.load(open("projects.geojson", encoding="utf-8"))["features"] if f["geometry"]]
geoms = [transform(to_m, shape(f["geometry"])) for f in feats]
tree = STRtree(geoms)


def band_for(d):
    for max_m, bid, label, share, w in BANDS:
        if d <= max_m + 1:          # +1 m tolerance for "touching"
            return bid, label, share, w
    return None


def timeline(a, b):
    ya, yb = a.get("year"), b.get("year")
    if not ya or not yb:
        return "unknown", 0.3
    gap = abs(ya - yb)
    return ("same year" if gap == 0 else f"{gap} year{'s' if gap > 1 else ''} apart"), {0: 1.0, 1: 0.7, 2: 0.4}.get(gap, 0.1)


pairs = []
for i, g in enumerate(geoms):
    for j in tree.query(g.buffer(40000)):
        j = int(j)
        if j <= i:
            continue
        a, b = feats[i]["properties"], feats[j]["properties"]
        if a["utility"] == b["utility"]:
            continue
        d = g.distance(geoms[j])
        bd = band_for(d)
        if not bd:
            continue
        bid, label, share, w = bd
        tl, tf = timeline(a, b)
        cross_state = "Dominion Energy SC" in (a["utility"], b["utility"])
        acc = ACCURACY_FACTOR[a["accuracy"]] * ACCURACY_FACTOR[b["accuracy"]]
        score = round(w * tf * acc * (1.5 if cross_state else 1.0), 3)
        pairs.append(dict(
            a=a["id"], b=b["id"], a_name=a["name"], b_name=b["name"], a_utility=a["utility"], b_utility=b["utility"],
            distance_km=round(d / 1000, 2), band=bid, band_label=label, can_share=share,
            a_year=a.get("year"), b_year=b.get("year"), timeline=tl,
            cross_state=cross_state, accuracy=f'{a["accuracy"]} / {b["accuracy"]}', score=score))

pairs.sort(key=lambda p: (-p["score"], p["distance_km"]))
for rank, p in enumerate(pairs, 1):
    p["rank"] = rank
json.dump(pairs, open("overlaps.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
print("pairs within 40 km (different utilities):", len(pairs))
print("cross-state (Dominion vs Georgia):", sum(p["cross_state"] for p in pairs))
print("by band:", Counter(p["band"] for p in pairs))
print("\nTop 15:")
for p in pairs[:15]:
    print(f'{p["rank"]:>2}. {p["score"]:<5} {p["distance_km"]:>6} km  {p["timeline"]:<14} {p["a_name"][:42]:<42} <> {p["b_name"][:48]}')
