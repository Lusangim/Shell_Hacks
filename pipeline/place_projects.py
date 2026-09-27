"""Place GridLock projects on the map.

Inputs (all in this folder):
  desc_2026_2030_projects.csv   Dominion Energy SC plan (SCRTP)
  sertp_2025_projects.csv       SERTP 2025 plan (Georgia side = SOUTHERN area)
  osm_substations_sc_ga.json    OpenStreetMap substations (Overpass export)
  hifld_lines_ga_sc.geojson     HIFLD transmission lines (with SUB_1 / SUB_2 names)
  us_states.geojson             State boundaries

Output:
  projects.geojson              One feature per GA/SC project, with accuracy + source
  placement_report.csv          What matched, what didn't (for hand-fixing)
  manual_locations.csv          (optional) hand-placed substations: name,lat,lon,source,note
"""
import csv, json, math, re
from collections import defaultdict
from pathlib import Path
from shapely.geometry import shape, Point, LineString, mapping
from ids import desc_id, sertp_ids
from fields import miles, parse_cost, parse_in_service_year, project_type, voltage_kv
from hifld_routes import HifldNetwork
from manual_locations import load_manual_locations


DESC_URL = "https://www.scrtp.com/assets/pdfs/home/2026-2030-2million-and-above-project-descriptions.pdf"
SERTP_URL = "https://www.southeasternrtp.com/docs/general/2025/2025%20Regional%20Transmission%20Plan%20and%20Input%20Assumptions.pdf"

DASH = r"\s+[\-–—�]\s+|[–—�]"   # spaced hyphen or any en/em dash
PREFIX_UTILITY = {"GTC": "Georgia Transmission Corp.", "MEAG": "MEAG Power", "SAV": "Georgia Power",
                  "DU": "Dalton Utilities", "PS": "PowerSouth", "GRID": "Georgia ITS (joint)"}
STRIP_WORDS = r"\b(SUBSTATION|SUB|SWITCHING STATION|SWITCHYARD|SWITCH|STATION|PRIMARY|TS|SS|DS|PLANT|GT|TRANSMISSION|DISTRIBUTION|STEAM|HYDRO|TAP|JCT|JUNCTION)\b"


def norm(name):
    n = name.upper().replace("&", " AND ")
    n = re.sub(r"\(.*?\)", " ", n)                  # (SAV), (WHITE), ...
    n = re.sub(r"\b\d+(/\d+)*\s*-?\s*(KV)?\b", " ", n)  # voltages / numbers
    n = re.sub(r"[#.,'`]", " ", n)
    return " ".join(n.split())


def keys(name):
    """Normalized lookup keys for a substation name, most specific first."""
    a = norm(name)
    b = " ".join(re.sub(STRIP_WORDS, " ", a).split())
    out = [k for k in dict.fromkeys([a, b]) if k and not k.startswith(("UNKNOWN", "NOT AVAILABLE"))]
    return out


def dist_km(p, q):
    (lat1, lon1), (lat2, lon2) = p, q
    r = math.radians
    x = (r(lon2) - r(lon1)) * math.cos((r(lat1) + r(lat2)) / 2)
    return 6371 * math.hypot(x, r(lat2) - r(lat1))


# ---------------- state boundaries ----------------
states = {f["properties"]["name"]: shape(f["geometry"]) for f in json.load(open("us_states.geojson"))["features"]}
GA, SC = states["Georgia"], states["South Carolina"]


def state_of(lat, lon):
    p = Point(lon, lat)
    if GA.buffer(0.02).contains(p):
        return "GA"
    if SC.buffer(0.02).contains(p):
        return "SC"
    return "other"


# ---------------- gazetteer: name -> candidate points ----------------
gaz = defaultdict(list)   # key -> [dict(lat,lon,src,label,operator)]

for e in json.load(open("osm_substations_sc_ga.json", encoding="utf-8"))["elements"]:
    t = e.get("tags", {})
    if not t.get("name"):
        continue
    lat, lon = (e["lat"], e["lon"]) if "lat" in e else (e["center"]["lat"], e["center"]["lon"])
    for k in keys(t["name"]):
        gaz[k].append(dict(lat=lat, lon=lon, src="OpenStreetMap", label=t["name"], operator=t.get("operator", "")))

hifld = json.load(open("hifld_lines_ga_sc.geojson"))["features"]
end_votes = defaultdict(list)   # key -> candidate endpoint coords from HIFLD lines
line_index = defaultdict(list)  # frozenset(keyA,keyB) -> [feature]
for f in hifld:
    p, g = f["properties"], f["geometry"]
    if not g:
        continue
    coords = g["coordinates"] if g["type"] == "LineString" else [c for part in g["coordinates"] for c in part]
    ends = [(coords[0][1], coords[0][0]), (coords[-1][1], coords[-1][0])]
    ka, kb = keys(p.get("SUB_1") or ""), keys(p.get("SUB_2") or "")
    for k in ka + kb:
        end_votes[k].extend(ends)       # we don't know which end is which; vote below
    for x in ka:
        for y in kb:
            line_index[frozenset((x, y))].append(f)

# A HIFLD name's true location is the endpoint that recurs across its lines (>= 2 lines agree within 1.5 km)
for k, pts in end_votes.items():
    best, support = None, 0
    for p in pts:
        s = sum(1 for q in pts if dist_km(p, q) < 1.5)
        if s > support:
            best, support = p, s
    if best and support >= 2 and not any(dist_km((c["lat"], c["lon"]), best) < 2 for c in gaz[k]):
        gaz[k].append(dict(lat=best[0], lon=best[1], src="HIFLD line endpoints", label=k, operator=""))

# Second pass: a name seen on only one HIFLD line gets the end of that line away from its known neighbour
for f in hifld:
    p, g = f["properties"], f["geometry"]
    if not g:
        continue
    coords = g["coordinates"] if g["type"] == "LineString" else [c for part in g["coordinates"] for c in part]
    ends = [(coords[0][1], coords[0][0]), (coords[-1][1], coords[-1][0])]
    for this, other in ((p.get("SUB_1") or "", p.get("SUB_2") or ""), (p.get("SUB_2") or "", p.get("SUB_1") or "")):
        tk, ok = keys(this), [c for k in keys(other) for c in gaz.get(k, [])]
        if not tk or not ok or any(gaz.get(k) for k in tk):
            continue
        near = min(ends, key=lambda e: min(dist_km(e, (c["lat"], c["lon"])) for c in ok))
        far = ends[1] if near == ends[0] else ends[0]
        if min(dist_km(near, (c["lat"], c["lon"])) for c in ok) < 3:
            gaz[tk[0]].append(dict(lat=far[0], lon=far[1], src="HIFLD line end", label=this, operator=""))

# Town fallback (Census places): used only when no substation matches; always "approximate - town"
towns = defaultdict(list)
for r in csv.DictReader(open("places_se.csv", encoding="utf-8")):
    nm = re.sub(r"\s+(city|town|CDP|village|consolidated government.*|unified government.*|metropolitan government.*|\(balance\))$", "", r["name"])
    for k in keys(nm):
        towns[k].append(dict(lat=float(r["lat"]), lon=float(r["lon"]), src="Census town centre", label=r["name"] + ", " + r["state"],
                             operator="", town=True))

# HIFLD lines as a network, to follow existing lines between two matched substations (hifld_routes.py)
network = HifldNetwork(hifld)

try:   # hand-placed fixes win
    for r in load_manual_locations(Path("manual_locations.csv")):
        for k in keys(r["name"]):
            gaz[k].insert(0, dict(lat=float(r["lat"]), lon=float(r["lon"]),
                                  src=f'Hand-placed from {r["source"]}: {r["note"]}',
                                  label=r["name"], operator="", manual=True,
                                  inferred=r["note"].upper().startswith("INFERRED")))
except FileNotFoundError:
    pass


def lookup(name, region):
    """Candidates for a substation name, limited to the project's region."""
    for k in keys(name):
        c = [x for x in gaz.get(k, []) if region(x["lat"], x["lon"])]
        if c:
            return c
    for k in keys(name):
        c = [x for x in towns.get(k, []) if region(x["lat"], x["lon"])]
        if c:
            return c
    return []


# ---------------- parse endpoints from project names ----------------
def endpoints(name):
    n = re.sub(r"^[A-Z]{2,5}:\s*", "", name.strip())
    n = re.split(r":|,|\bFold-in\b", n, maxsplit=1, flags=re.I)[0]
    n = re.split(r"\s\d[\d./\-\s]*kV\b", n, maxsplit=1, flags=re.I)[0]
    n = re.split(r"\b(Sub|Substation|Transmission Line|Tie|Line|Area|Tap)\b", n, maxsplit=1, flags=re.I)[0]
    n = re.sub(r"(?<=[A-Za-z0-9)])\s*-\s*(?=[A-Za-z])", " - ", n)   # "Yemassee- Ritter" -> "Yemassee - Ritter"
    parts = [p.strip(" -#") for p in re.split(DASH, n) if p.strip(" -#")]
    return parts


# ---------------- load projects ----------------
projects = []
for i, r in enumerate(csv.DictReader(open("desc_2026_2030_projects.csv", encoding="utf-8")), 1):
    cost_usd, cost_basis, cost_flags = parse_cost(
        r["total_cost"], [r[column] for column in
                          ("previous_cost", "cost_2026", "cost_2027", "cost_2028", "cost_2029", "cost_2030")]
    )
    projects.append(dict(id=desc_id(i), utility="Dominion Energy SC", utility_basis="stated",
                         name=r["project_name"], description=r["description"] or None,
                         need=r["need"] or None, status=r["status"] or None,
                         in_service=r["planned_in_service"] or None,
                         year=parse_in_service_year(r["planned_in_service"]),
                         cost_usd=cost_usd, cost_basis=cost_basis, cost_flags=cost_flags,
                         voltage_kv=voltage_kv(r["project_name"], r["description"]),
                         project_type=project_type(r["project_name"], r["description"]),
                         miles=miles(r["project_name"], r["description"]),
                         source={"doc": "SCRTP Planned Facilities 2026-2030 $2M & Above", "page": i,
                                 "url": DESC_URL},
                         project_id=r["project_id"] or None, home="SC"))

sertp_rows = list(csv.DictReader(open("sertp_2025_projects.csv", encoding="utf-8")))
for i, (r, stable_id) in enumerate(zip(sertp_rows, sertp_ids(sertp_rows)), 1):
    if r["utility_area"] != "SOUTHERN":
        continue
    m = re.match(r"([A-Z]{2,5}):", r["project_name"])
    util = PREFIX_UTILITY.get(m.group(1), m.group(1)) if m else "Southern Company"
    projects.append(dict(id=stable_id, utility=util, utility_basis="stated",
                         name=r["project_name"], description=r["description"] or None,
                         need=r["need"] or None, status=None, in_service=r["in_service_year"] or None,
                         year=parse_in_service_year(r["in_service_year"]),
                         cost_usd=None, cost_basis="none", cost_flags=[],
                         voltage_kv=voltage_kv(r["project_name"], r["description"]),
                         project_type=project_type(r["project_name"], r["description"]),
                         miles=miles(r["project_name"], r["description"]),
                         source={"doc": "SERTP 2025 Regional Transmission Plan (Nov 26 2025)",
                                 "page": int(r["source_page"]), "url": SERTP_URL},
                         project_id=None,
                         home="SAV" if util == "Georgia Power" and m else "GA"))

REGIONS = {
    "SC":  lambda la, lo: state_of(la, lo) == "SC" or (state_of(la, lo) == "GA" and lo > -82.3),  # DESC + border ties
    "GA":  lambda la, lo: state_of(la, lo) in ("GA", "other"),
    "SAV": lambda la, lo: 31.7 < la < 32.6 and -81.8 < lo < -80.8,
}


def pick(cands, near=None):
    if not cands:
        return None, False
    manual = [c for c in cands if c.get("manual")]
    if manual:
        return manual[0], False
    if near:
        cands = sorted(cands, key=lambda c: dist_km((c["lat"], c["lon"]), near))
    return cands[0], len({(round(c["lat"], 2), round(c["lon"], 2)) for c in cands}) > 1


features, report = [], []
for p in projects:
    names = endpoints(p["name"])
    region = REGIONS[p["home"]]
    cands = [lookup(n, region) for n in names]
    geom, accuracy, loc_src, ambiguous = None, "unknown", "", False
    used, state_geom = [], None   # candidates the location rests on; the shape that decides the state

    if len(names) >= 2 and all(cands):
        # choose the combination of candidates that keeps the chain shortest
        chosen = [None] * len(names)
        best = None
        for c0 in cands[0][:6]:
            chain, total = [c0], 0
            for cs in cands[1:]:
                nxt = min(cs, key=lambda c: dist_km((c["lat"], c["lon"]), (chain[-1]["lat"], chain[-1]["lon"])))
                total += dist_km((nxt["lat"], nxt["lon"]), (chain[-1]["lat"], chain[-1]["lon"]))
                chain.append(nxt)
            if best is None or total < best[0]:
                best = (total, chain)
        total, chosen = best
        ambiguous = any(len(c) > 1 for c in cands)
        if total > 200:                       # implausible - probably a wrong match
            chosen, geom = None, None
        else:
            # real route from HIFLD if a line connects the two end substations
            hit = None
            for x in keys(names[0]):
                for y in keys(names[-1]):
                    hit = hit or line_index.get(frozenset((x, y)))
            if hit and len(names) == 2:
                geom, accuracy, loc_src = hit[0]["geometry"], "exact", "HIFLD line route"
            else:
                # A town centre is not where a line ends: never draw to one when a real substation is known.
                real = [c for c in chosen if not c.get("town")]
                town_names = [n for n, c in zip(names, chosen) if c.get("town")]
                accuracy = "approximate"
                # The state (and so which rows are kept) still comes from the whole matched chain, as
                # before: trimming or routing changes what is drawn, never which projects are in scope.
                state_geom = LineString([(c["lon"], c["lat"]) for c in chosen])
                if len(real) == len(chosen):
                    points = [(c["lon"], c["lat"]) for c in chosen]
                    # Route only between substations matched in public data; a hand-placed end (Okatie,
                    # inferred) keeps its straight line and its visible "INFERRED" note.
                    route = None if any(c.get("manual") for c in chosen) else network.route(points, p["voltage_kv"])
                    used = chosen
                    if route is not None:
                        geom = mapping(route)
                        loc_src = (f"Follows existing HIFLD transmission lines between {' and '.join(names)} "
                                   "(network route; the plan gives no route)")
                    else:
                        geom = mapping(state_geom)
                        loc_src = (f"Straight line between {' and '.join(names)} (matched from "
                                   + " / ".join(sorted({c["src"] for c in chosen})) + ")")
                elif len(real) >= 2:
                    geom, used = mapping(LineString([(c["lon"], c["lat"]) for c in real])), real
                    real_names = [n for n, c in zip(names, chosen) if not c.get("town")]
                    loc_src = (f"Straight line between {' and '.join(real_names)} (matched from "
                               + " / ".join(sorted({c["src"] for c in real}))
                               + f"; Census town centre match for {', '.join(town_names)} not used)")
                elif len(real) == 1:
                    c = real[0]
                    n = next(name for name, cand in zip(names, chosen) if cand is c)
                    geom, used = mapping(Point(c["lon"], c["lat"])), real
                    loc_src = (f'{c["src"]} ({c["label"]}) - only \'{n}\' located; '
                               f"Census town centre match for {', '.join(town_names)} not used")
                else:
                    geom, used = mapping(LineString([(c["lon"], c["lat"]) for c in chosen])), chosen
                    loc_src = ("Only the towns matched; the substation locations are not known "
                               "(straight line between Census town centres)")
    if geom is None:
        found = [(n, c) for n, c in zip(names, cands) if c]
        if found:
            n, c = found[0]
            c, ambiguous = pick(c)
            geom, used = mapping(Point(c["lon"], c["lat"])), [c]
            single_site = len(names) == 1
            accuracy = "exact" if single_site and not ambiguous and not c.get("town") and not c.get("inferred") else "approximate"
            if c.get("town"):
                loc_src = (f"Only the town matched; the substation location is not known "
                           f"({c['label']}, Census town centre)")
            else:
                loc_src = f'{c["src"]} ({c["label"]})'
            loc_src += "" if single_site else f" - only '{n}' located"
        else:
            loc_src = ("Unknown: no named endpoint match in committed OpenStreetMap substations, "
                       "HIFLD transmission lines, or Census places within the project's allowed region.")
    town_only = bool(used) and all(c.get("town") for c in used)

    state = ""
    if geom:
        g = state_geom if state_geom is not None else shape(geom)
        state = state_of(g.centroid.y, g.centroid.x)
    georgia_only_orgs = ("Georgia Transmission Corp.", "MEAG Power", "Dalton Utilities", "Georgia ITS (joint)")
    keep = (p["utility"] == "Dominion Energy SC" or state == "GA"
            or (geom is None and (p["home"] == "SAV" or p["utility"] in georgia_only_orgs)))
    if p["utility"] in ("PowerSouth",):
        keep = False
    report.append(dict(id=p["id"], utility=p["utility"], name=p["name"], endpoints=" | ".join(names),
                       matched=" | ".join("yes" if c else "NO" for c in cands), accuracy=accuracy,
                       location_source=loc_src, state=state or "?", kept=keep))
    if not keep:
        continue
    if p["utility"] == "Southern Company":
        p["utility"] = "Georgia Power"
        p["utility_basis"] = "inferred_from_location"
    props = dict(p, accuracy=accuracy, location_source=loc_src or None,
                 state=state if state in ("GA", "SC") else None, endpoints=names, town_only=town_only)
    props.pop("home")
    features.append(dict(type="Feature", geometry=geom, properties=props))

json.dump(dict(type="FeatureCollection", features=features), open("projects.geojson", "w", encoding="utf-8"),
          ensure_ascii=False)
with open("placement_report.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=report[0].keys())
    w.writeheader()
    w.writerows(report)

from collections import Counter
print("kept projects:", len(features))
print("by utility:", Counter(f["properties"]["utility"] for f in features))
print("accuracy:", Counter((f["properties"]["utility"] == "Dominion Energy SC", f["properties"]["accuracy"]) for f in features))
print("dropped (outside GA/SC or PowerSouth):", sum(1 for r in report if not r["kept"]))
