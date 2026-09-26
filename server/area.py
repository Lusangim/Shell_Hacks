"""Local projected-circle queries over already validated project geometry."""

from __future__ import annotations

from collections import Counter

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform

from server.schemas import Area, Center, Overlap, ProjectCollection


TO_METRES = Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True).transform


def build_area(
    projects: ProjectCollection,
    overlaps: tuple[Overlap, ...],
    *,
    lat: float,
    lon: float,
    radius_km: float,
) -> Area:
    """Return every mapped project intersecting a projected metric circle."""
    x, y = TO_METRES(lon, lat)
    circle = Point(x, y).buffer(radius_km * 1000)
    selected = []
    for project in projects.features:
        if project.geometry is None:
            continue
        geometry = shape(project.geometry.model_dump(mode="json"))
        if geometry.is_empty:
            continue
        if transform(TO_METRES, geometry).intersects(circle):
            selected.append(project)
    selected_ids = {project.properties.id for project in selected}
    pairs = sorted(
        (pair for pair in overlaps if pair.a in selected_ids or pair.b in selected_ids),
        key=lambda pair: (pair.rank, pair.distance_km, pair.id),
    )
    return Area(
        center=Center(lat=lat, lon=lon), radius_km=radius_km,
        projects=selected, overlaps=pairs,
        counts_by_utility=dict(Counter(project.properties.utility for project in selected)),
        counts_by_band=dict(Counter(pair.band for pair in pairs)),
    )
