"""Census places, local basemap, and complete stage accounting."""

import csv
import hashlib
import json
from pathlib import Path

from server.app import load_artifacts
from server.schemas import Meta
from pipeline import build_all


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
BUILT = ROOT / "data" / "build"
EXTRA_FILES = ("places.json", "basemap.json", "meta.json")


def _json(name: str) -> object:
    return json.loads((BUILT / name).read_text(encoding="utf-8"))


def test_rebuild_has_local_places_and_basemap_from_committed_sources() -> None:
    build_all.build(ROOT)
    places = _json("places.json")
    basemap = _json("basemap.json")
    with (RAW / "places_se.csv").open("r", encoding="utf-8", newline="") as handle:
        expected = [row for row in csv.DictReader(handle) if row["state"] in {"GA", "SC"}]
    assert len(places) == len(expected) == 1150
    assert [item["name"] for item in places] == [row["name"] for row in expected]
    assert all(
        item["state"] == row["state"]
        and item["lat"] == float(row["lat"])
        and item["lon"] == float(row["lon"])
        for item, row in zip(places, expected)
    )

    assert basemap["type"] == "FeatureCollection"
    state_features = [feature for feature in basemap["features"] if feature["properties"]["kind"] == "state_outline"]
    city_features = [feature for feature in basemap["features"] if feature["properties"]["kind"] == "city_label"]
    assert {feature["properties"]["name"] for feature in state_features} == {"Georgia", "South Carolina"}
    assert len(city_features) == 801
    assert all(feature["geometry"]["type"] == "Point" for feature in city_features)
    city_places = [place for place in places if place["name"].endswith((" city", " town"))]
    assert [feature["properties"]["name"] for feature in city_features] == [place["name"] for place in city_places]
    assert all(
        feature["geometry"]["coordinates"] == [place["lon"], place["lat"]]
        for feature, place in zip(city_features, city_places)
    )


def test_meta_counts_all_unmapped_rows_and_production_loader_succeeds() -> None:
    build_all.build(ROOT)
    meta = Meta.model_validate(_json("meta.json"))
    assert meta.stage_counts["source_rows"] == 481
    assert meta.stage_counts["kept"] == 230
    assert meta.stage_counts["placed"] == 181
    assert meta.stage_counts["overlaps"] == 477
    assert meta.stage_counts["cross_state"] == 44
    assert meta.unmapped_count == 128
    assert meta.unmapped_reasons == {
        "kept_not_located": 49,
        "unprefixed_southern_not_located": 77,
        "powersouth_not_located_excluded": 2,
    }
    assert sum(meta.unmapped_reasons.values()) == meta.unmapped_count
    pairs = _json("overlaps.json")
    projects = _json("projects.geojson")
    project_ids = {feature["properties"]["id"] for feature in projects["features"]}
    paired_ids = {project_id for pair in pairs for project_id in (pair["a"], pair["b"])}
    assert meta.no_overlap_count == len(project_ids - paired_ids)
    with (BUILT / "placement_report.csv").open("r", encoding="utf-8", newline="") as handle:
        report_rows = list(csv.DictReader(handle))
    inferred_ids = {
        row["id"] for row in report_rows
        if row["utility"] == "Southern Company" and row["kept"] == "True"
    }
    assert len(inferred_ids) == 78
    assert all(
        feature["properties"]["utility_basis"] == "inferred_from_location"
        for feature in projects["features"] if feature["properties"]["id"] in inferred_ids
    )
    loaded = load_artifacts(BUILT)
    assert len(loaded.projects.features) == 230
    assert len(loaded.overlaps) == 477
    assert len(loaded.basemap.features) == 803


def test_extra_files_are_byte_identical_across_two_rebuilds() -> None:
    build_all.build(ROOT)
    first = {name: hashlib.sha256((BUILT / name).read_bytes()).hexdigest() for name in EXTRA_FILES}
    build_all.build(ROOT)
    assert first == {name: hashlib.sha256((BUILT / name).read_bytes()).hexdigest() for name in EXTRA_FILES}
