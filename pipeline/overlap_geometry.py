"""Pure, source-conservative geometry and wording for overlap pairs."""

import re

from pyproj import Geod, Transformer
from shapely.geometry import Point
from shapely.ops import nearest_points, transform


TO_METRES = Transformer.from_crs(4326, 5070, always_xy=True).transform
TO_GEO = Transformer.from_crs(5070, 4326, always_xy=True).transform
GEOD = Geod(ellps="WGS84")
LINE_TYPES = {"LineString", "MultiLineString"}


def band_for(distance_m: float) -> str | None:
    """The published, strict distance bands; no tolerance beyond touching."""
    if distance_m <= 1:
        return "touching"
    if distance_m < 1600:
        return "lt_1_6km"
    if distance_m < 8000:
        return "lt_8km"
    if distance_m < 40000:
        return "lt_40km"
    return None


def nearest_point_distance_m(a, b) -> float:
    """Find nearest points in EPSG:5070, then measure that span on WGS84."""
    near_a, near_b = nearest_points(transform(TO_METRES, a), transform(TO_METRES, b))
    lon_a, lat_a = TO_GEO(near_a.x, near_a.y)
    lon_b, lat_b = TO_GEO(near_b.x, near_b.y)
    return GEOD.inv(lon_a, lat_a, lon_b, lat_b)[2]


def _endpoint_key(name: str) -> str:
    """Normalize case and the source's (SAV) tag without merging station names."""
    name = re.sub(r"\s*\(SAV\)", "", name.upper())
    return " ".join(name.split())


def _shared_endpoint(a: dict, b: dict) -> str | None:
    b_keys = {_endpoint_key(name) for name in b.get("endpoints", [])}
    return next((name for name in a.get("endpoints", []) if _endpoint_key(name) in b_keys), None)


def _line_endpoint_touches(line, other) -> bool:
    if line.geom_type == "LineString":
        endpoints = (line.coords[0], line.coords[-1])
    elif line.geom_type == "MultiLineString":
        endpoints = tuple(point for part in line.geoms for point in (part.coords[0], part.coords[-1]))
    else:
        return False
    return any(nearest_point_distance_m(Point(point), other) <= 1 for point in endpoints)


def _source(project: dict) -> str:
    source = project["source"]
    return f'{source["doc"]}, p. {source["page"]}'


def classify_touch(a: dict, b: dict, geometry_a, geometry_b, distance_m: float) -> tuple[str, str]:
    """Describe only named, mapped contact that the source rows support."""
    if distance_m > 1:
        return "proximity", "Mapped geometries are nearby; a shared asset is not established."

    common = _shared_endpoint(a, b)
    if common and geometry_a.geom_type == geometry_b.geom_type == "Point":
        if a.get("voltage_kv") and b.get("voltage_kv"):
            return (
                "same_substation",
                f'Both plans name {common} work with stated voltages ({_source(a)}; {_source(b)}). '
                "Shared equipment is not established.",
            )

    lines = [
        (geometry_a, geometry_b) if geometry_a.geom_type in LINE_TYPES else None,
        (geometry_b, geometry_a) if geometry_b.geom_type in LINE_TYPES else None,
    ]
    if common and any(pair is not None and _line_endpoint_touches(*pair) for pair in lines):
        ids = {a["id"], b["id"]}
        if ids == {"desc-p41", "sertp-p107-9bc088"}:
            return (
                "shared_endpoint",
                "The Okatie–McIntosh 115 kV tie line names McIntosh as an endpoint. "
                "The DESC series reactor work is at new Deerfield Switching Station, location not stated; "
                "the SERTP relay work is at the McIntosh 230 kV bus "
                f"({_source(a)}; {_source(b)}).",
            )
        if ids == {"desc-p41", "sertp-p111-fe1e3b"}:
            return (
                "shared_endpoint",
                "Both plans name McIntosh as an endpoint of a 115 kV line. "
                "The SERTP rebuild covers the 6.7-mile Goshen (Savannah)–Georgia Pacific (Rincon) section; "
                "the mapped full Goshen–McIntosh line endpoint does not establish work at McIntosh. "
                "The DESC series reactor work is at new Deerfield Switching Station, location not stated "
                f"({_source(a)}; {_source(b)}).",
            )
        return (
            "shared_endpoint",
            f'Both plans name {common} as an endpoint, and mapped line endpoints meet '
            f'({_source(a)}; {_source(b)}). The physical work location is unverified.',
        )

    if (geometry_a.geom_type in LINE_TYPES and geometry_b.geom_type in LINE_TYPES
            and a.get("accuracy") == b.get("accuracy") == "exact"
            and geometry_a.intersects(geometry_b)):
        return (
            "lines_cross",
            f'Mapped exact line geometries intersect ({_source(a)}; {_source(b)}); '
            "the plans do not establish a shared asset.",
        )
    if "approximate" in (a.get("accuracy"), b.get("accuracy")):
        return (
            "same_area_approximate",
            "Mapped geometries meet, but at least one placement is approximate; "
            "physical contact and shared assets are unverified.",
        )
    return "proximity", "Mapped geometries meet; the plans do not establish a shared asset."


def can_share(band: str, reason: str) -> str:
    """Coordination opportunity, not a claim that an asset can literally be shared."""
    if band == "touching":
        return {
            "same_substation": "Coordinate substation work and outage timing; shared equipment unverified.",
            "shared_endpoint": "Verify work locations before reviewing possible coordination; shared assets unverified.",
            "lines_cross": "Review the mapped crossing and outage timing; shared assets unverified.",
            "same_area_approximate": "Review the mapped area together; physical contact unverified.",
            "proximity": "Review mapped proximity; shared assets unverified.",
        }[reason]
    if band == "lt_1_6km":
        return "Review nearby access and right-of-way opportunities; sharing unverified."
    if band == "lt_8km":
        return "Review nearby site logistics and deliveries; sharing unverified."
    return "Review crew and equipment timing in the area; sharing unverified."


def rank_key(pair: dict) -> tuple[float, float, str]:
    return -pair["score"], pair["distance_km"], pair["id"]


TOWN_CAPPED_BANDS = frozenset({"touching", "lt_1_6km", "lt_8km"})
NAME_MATCH_REASONS = frozenset({"same_substation", "shared_endpoint"})
TOWN_CAP_NOTE = ("One location is only a town centre, not a substation, so GridLock counts this pair "
                 "as under 40 km at most.")


def town_capped_band(band: str, reason: str, town_only: bool) -> tuple[str, bool]:
    """A town-centre location alone cannot put a pair closer than 'under 40 km'.

    Pairs whose plans name the same substation keep their band: that match comes from the plans' own
    words, not from where the town centre happens to be.
    """
    if town_only and band in TOWN_CAPPED_BANDS and reason not in NAME_MATCH_REASONS:
        return "lt_40km", True
    return band, False
