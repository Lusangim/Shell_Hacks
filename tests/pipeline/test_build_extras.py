"""Census places, local basemap, and complete stage accounting."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import nearest_points, transform

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
    assert meta.stage_counts["overlaps"] == 465
    assert meta.stage_counts["cross_state"] == 43
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
    assert len(loaded.overlaps) == 465
    assert len(loaded.basemap.features) == 803


def test_extra_files_are_byte_identical_across_two_rebuilds() -> None:
    build_all.build(ROOT)
    first = {name: hashlib.sha256((BUILT / name).read_bytes()).hexdigest() for name in EXTRA_FILES}
    build_all.build(ROOT)
    assert first == {name: hashlib.sha256((BUILT / name).read_bytes()).hexdigest() for name in EXTRA_FILES}


def test_hotspots_count_nearest_place_for_each_close_pair() -> None:
    build_all.build(ROOT)
    hotspots = _json("meta.json")["hotspots"]
    places = _json("places.json")
    projects = {f["properties"]["id"]: f["geometry"] for f in _json("projects.geojson")["features"]}
    to_metres = Transformer.from_crs(4326, 5070, always_xy=True).transform
    place_points = [(place, to_metres(place["lon"], place["lat"])) for place in places]
    counts = Counter()
    best = {}
    for pair in _json("overlaps.json"):
        if pair["band"] not in {"touching", "lt_1_6km", "lt_8km"}:
            continue
        a, b = (transform(to_metres, shape(projects[pair[key]])) for key in ("a", "b"))
        near_a, near_b = nearest_points(a, b)
        x, y = (near_a.x + near_b.x) / 2, (near_a.y + near_b.y) / 2
        place = min(place_points, key=lambda item: ((item[1][0] - x) ** 2 + (item[1][1] - y) ** 2, item[0]["name"]))[0]
        label = place["name"]
        counts[label] += 1
        best[label] = min(best.get(label, pair["rank"]), pair["rank"])
    expected = sorted(
        ({"label": place["name"], "lat": place["lat"], "lon": place["lon"],
          "pairs": counts[place["name"]], "best_rank": best[place["name"]]}
         for place in places if counts[place["name"]] >= 2),
        key=lambda item: (-item["pairs"], item["best_rank"], item["label"]),
    )[:5]
    assert hotspots == expected
    assert len(hotspots) <= 5
    assert any(abs(item["lat"] - 32.018043) < 0.4 and abs(item["lon"] + 81.196492) < 0.4
               and item["best_rank"] == 1 for item in hotspots)
