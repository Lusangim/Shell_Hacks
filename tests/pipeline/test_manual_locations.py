"""Border placements must retain public provenance and honest unknowns."""

import csv
import json
from pathlib import Path

import pytest

from pipeline.manual_locations import load_manual_locations


ROOT = Path(__file__).resolve().parents[2]
BORDER = (-82.8, 31.5, -80.5, 34.0)
NEIGHBOR_CANDIDATES = {
    "desc-p8": "Canadys",
    "desc-p13": "Okatie",
    "desc-p14": "Graniteville",
    "desc-p38": "Lyles",
    "sertp-p75-214b7c": "Little Ogeechee",
    "sertp-p111-80c2f1": "McIntosh",
}


def _features() -> list[dict]:
    return json.loads((ROOT / "data/build/projects.geojson").read_text(encoding="utf-8"))["features"]


def _geometry_points(geometry: dict | None) -> list[list[float]]:
    if geometry is None:
        return []
    if geometry["type"] == "Point":
        return [geometry["coordinates"]]
    if geometry["type"] == "LineString":
        return geometry["coordinates"]
    return [point for line in geometry["coordinates"] for point in line]


def _in_border(point: list[float]) -> bool:
    lon, lat = point
    west, south, east, north = BORDER
    return west <= lon <= east and south <= lat <= north


def test_every_manual_fix_has_named_source_note_and_inferred_okatie() -> None:
    rows = load_manual_locations(ROOT / "data/manual/manual_locations.csv")
    assert len(rows) == 1
    okatie = rows[0]
    assert okatie["name"] == "Okatie"
    assert "HIFLD" in okatie["source"] and "TAP170160" in okatie["source"]
    assert "SCRTP" in okatie["source"]
    assert okatie["note"].startswith("INFERRED")

    hifld = json.loads((ROOT / "data/raw/hifld_lines_ga_sc.geojson").read_text(encoding="utf-8"))["features"]
    tap_endpoints = [
        endpoint
        for feature in hifld
        if "TAP170160" in (feature["properties"].get("SUB_1"), feature["properties"].get("SUB_2"))
        for endpoint in (feature["geometry"]["coordinates"][0], feature["geometry"]["coordinates"][-1])
    ]
    assert any(abs(float(okatie["lon"]) - lon) < 0.000001
               and abs(float(okatie["lat"]) - lat) < 0.000001
               for lon, lat in tap_endpoints)

    by_id = {feature["properties"]["id"]: feature for feature in _features()}
    for project_id in ("desc-p11", "desc-p12", "desc-p41"):
        project = by_id[project_id]["properties"]
        assert project["accuracy"] == "approximate"
        assert "INFERRED" in project["location_source"]
        assert "HIFLD" in project["location_source"]


@pytest.mark.parametrize("missing", ["source", "note"])
def test_manual_fix_missing_provenance_is_rejected(tmp_path: Path, missing: str) -> None:
    manual = tmp_path / "manual_locations.csv"
    values = {"name": "Test", "lat": "32", "lon": "-81", "source": "HIFLD feature X", "note": "INFERRED"}
    values[missing] = ""
    with manual.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=values)
        writer.writeheader()
        writer.writerow(values)
    with pytest.raises(ValueError, match=missing):
        load_manual_locations(manual)


def test_full_border_geometry_set_has_named_source_and_cautious_accuracy() -> None:
    region = [feature for feature in _features()
              if any(_in_border(point) for point in _geometry_points(feature["geometry"]))]
    assert len(region) == 52
    assert sum(feature["properties"]["accuracy"] == "exact" for feature in region) == 9
    assert sum(feature["properties"]["accuracy"] == "approximate" for feature in region) == 43
    for feature in region:
        props = feature["properties"]
        source = props["location_source"]
        assert source and any(label in source for label in
                              ("OpenStreetMap", "HIFLD", "Census town centre", "Hand-placed")), props["id"]
        if "Hand-placed" in source or "Census town centre" in source:
            assert props["accuracy"] == "approximate", props["id"]


def test_all_kept_unknowns_have_explicit_reason_in_artifact_and_report() -> None:
    features = _features()
    unknowns = {feature["properties"]["id"]: feature["properties"]
                for feature in features if feature["geometry"] is None}
    assert len(unknowns) == 49
    with (ROOT / "data/build/placement_report.csv").open(encoding="utf-8", newline="") as handle:
        report = {row["id"]: row for row in csv.DictReader(handle)}
    for project_id, props in unknowns.items():
        assert props["accuracy"] == "unknown"
        assert props["location_source"].startswith("Unknown: no named endpoint match"), project_id
        assert report[project_id]["location_source"] == props["location_source"]
        assert "NO" in report[project_id]["matched"]
    for project_id, neighbor in NEIGHBOR_CANDIDATES.items():
        assert project_id in unknowns
        assert neighbor.casefold() in unknowns[project_id]["description"].casefold()
