"""Read-only public asset index loaded once in the FastAPI lifespan."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

from pipeline.savings import UnitCosts, load_unit_costs
from server.settings import ROOT


TO_METRES = Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True).transform
TO_DEGREES = Transformer.from_crs("EPSG:5070", "EPSG:4326", always_xy=True).transform


@dataclass(frozen=True)
class RawAsset:
    id: str
    asset_class: str
    name: str
    source: str
    geometry: LineString | Point


@dataclass(frozen=True)
class StormData:
    scenario: dict
    assets: tuple[RawAsset, ...]
    tree: STRtree
    costs: UnitCosts


def load_storm_data(root: Path = ROOT) -> StormData:
    """Load the two public raw files and the existing unit-cost loader once."""
    scenario = json.loads((root / "data" / "scenarios" / "gl1_hypothetical.json").read_text(encoding="utf-8"))
    lines = json.loads((root / "data" / "raw" / "hifld_lines_ga_sc.geojson").read_text(encoding="utf-8"))["features"]
    stations = json.loads((root / "data" / "raw" / "osm_substations_sc_ga.json").read_text(encoding="utf-8"))["elements"]
    assets: list[RawAsset] = []
    for index, feature in enumerate(lines):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "LineString":
            continue
        points = [TO_METRES(float(lon), float(lat)) for lon, lat in geometry.get("coordinates", [])]
        if len(points) < 2:
            continue
        line = LineString(points)
        if line.is_empty or line.length == 0:
            continue
        props = feature.get("properties") or {}
        voltage_class = str(props.get("VOLT_CLASS") or "NOT AVAILABLE")
        asset_class = "line_wood" if voltage_class in ("UNDER 100", "NOT AVAILABLE") else "line_steel"
        first, second = str(props.get("SUB_1") or "Unknown"), str(props.get("SUB_2") or "Unknown")
        assets.append(RawAsset(f"hifld-{index}", asset_class, f"{first} - {second}", "HIFLD transmission lines (archived)", line))
    for element in stations:
        if element.get("tags", {}).get("power") != "substation":
            continue
        center = element.get("center") or element
        if "lon" not in center or "lat" not in center:
            continue
        point = Point(*TO_METRES(float(center["lon"]), float(center["lat"])))
        name = element.get("tags", {}).get("name") or f"Unnamed OSM substation {element['id']}"
        assets.append(RawAsset(f"osm-{element['type']}-{element['id']}", "substation", name, "OpenStreetMap substations", point))
    frozen = tuple(assets)
    return StormData(scenario, frozen, STRtree([asset.geometry for asset in frozen]), load_unit_costs(root / "data" / "manual" / "unit_costs_2026.csv"))
