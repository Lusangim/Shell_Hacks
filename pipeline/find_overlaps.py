"""Find and rank coordination opportunities between utilities.

Input:  projects.geojson (from place_projects.py)
Output: overlaps.json - every pair of projects from DIFFERENT utilities within 40 km, ranked.

Nearest points are found in EPSG:5070, then their distance is measured geodesically.
"""
import json
from pathlib import Path
from shapely.geometry import shape
from shapely.ops import transform
from shapely.strtree import STRtree
from overlap_geometry import TO_METRES, band_for, can_share, classify_touch, nearest_point_distance_m, rank_key
from savings import estimate_savings, load_assumptions

BANDS = {
    "touching": ("Touching / crossing", 4),
    "lt_1_6km": ("Under 1.6 km", 3),
    "lt_8km": ("Under 8 km", 2),
    "lt_40km": ("Under 40 km", 1),
}
ACCURACY_FACTOR = {"exact": 1.0, "approximate": 0.8}

feats = [f for f in json.load(open("projects.geojson", encoding="utf-8"))["features"] if f["geometry"]]
geoms = [shape(f["geometry"]) for f in feats]
projected = [transform(TO_METRES, geometry) for geometry in geoms]
tree = STRtree(projected)
assumptions = load_assumptions(Path("assumptions.json"))


def timeline(a, b):
    ya, yb = a.get("year"), b.get("year")
    if not ya or not yb:
        return "unknown", 0.3
    gap = abs(ya - yb)
    return ("same year" if gap == 0 else f"{gap} year{'s' if gap > 1 else ''} apart"), {0: 1.0, 1: 0.7, 2: 0.4}.get(gap, 0.1)


pairs = []
for i, g in enumerate(projected):
    # The candidate radius allows for small EPSG:5070 scale distortion; the
    # final strict 40 km decision uses the geodesic nearest-point distance.
    for j in tree.query(g.buffer(42000)):
        j = int(j)
        if j <= i:
            continue
        a, b = feats[i]["properties"], feats[j]["properties"]
        if a["utility"] == b["utility"]:
            continue
        d = nearest_point_distance_m(geoms[i], geoms[j])
        bid = band_for(d)
        if bid is None:
            continue
        label, w = BANDS[bid]
        tl, tf = timeline(a, b)
        a_state, b_state = a.get("state"), b.get("state")
        cross_state = bool(a_state and b_state and a_state != b_state)
        pair_note = (
            "May already plan jointly through Georgia's Integrated Transmission System"
            if a_state == b_state == "GA" else None
        )
        acc = ACCURACY_FACTOR[a["accuracy"]] * ACCURACY_FACTOR[b["accuracy"]]
        score = round(w * tf * acc * (1.5 if cross_state else 1.0), 3)
        reason, detail = classify_touch(a, b, geoms[i], geoms[j], d)
        if a["id"] > b["id"]:
            a, b = b, a
        year_gap = abs(a["year"] - b["year"]) if a.get("year") is not None and b.get("year") is not None else None
        accuracy_pair = "approximate" if "approximate" in (a["accuracy"], b["accuracy"]) else "exact"
        pairs.append(dict(
            id=f'{a["id"]}__{b["id"]}',
            a=a["id"], b=b["id"], a_name=a["name"], b_name=b["name"], a_utility=a["utility"], b_utility=b["utility"],
            distance_km=d / 1000, band=bid, band_label=label, can_share=can_share(bid, reason),
            touch_reason=reason, touch_detail=detail,
            a_year=a.get("year"), b_year=b.get("year"), year_gap=year_gap, timeline=tl,
            cross_state=cross_state, pair_note=pair_note, accuracy_pair=accuracy_pair, score=score,
            savings=estimate_savings(a, b, assumptions), brief_status="none"))

pairs.sort(key=rank_key)
for rank, p in enumerate(pairs, 1):
    p["rank"] = rank
json.dump(pairs, open("overlaps.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
print("pairs within 40 km (different utilities):", len(pairs))
print("cross-state (different known states):", sum(p["cross_state"] for p in pairs))
print("by band:", Counter(p["band"] for p in pairs))
print("\nTop 15:")
for p in pairs[:15]:
    print(f'{p["rank"]:>2}. {p["score"]:<5} {p["distance_km"]:>6} km  {p["timeline"]:<14} {p["a_name"][:42]:<42} <> {p["b_name"][:48]}')
