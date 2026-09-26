"""Exact overlap boundaries, geodesic measurement, and sourced explanations."""

import json
from pathlib import Path

import pytest
from pyproj import Geod
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform

from pipeline.overlap_geometry import (
    TO_METRES,
    band_for,
    can_share,
    classify_touch,
    nearest_point_distance_m,
    rank_key,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("distance_m", "expected"),
    [
        (0, "touching"), (1, "touching"), (1.01, "lt_1_6km"),
        (1599.99, "lt_1_6km"), (1600, "lt_8km"),
        (7999.99, "lt_8km"), (8000, "lt_40km"),
        (39999.99, "lt_40km"), (40000, None),
    ],
)
def test_exact_band_boundaries(distance_m: float, expected: str | None) -> None:
    assert band_for(distance_m) == expected


def test_nearest_points_are_measured_geodesically() -> None:
    line = LineString([(-81.0, 32.0), (-80.0, 32.0)])
    endpoint = Point(-81.0, 32.0)
    assert nearest_point_distance_m(line, endpoint) == pytest.approx(0, abs=1e-6)
    north = Point(-81.0, 32.01)
    expected = Geod(ellps="WGS84").inv(-81.0, 32.0, -81.0, 32.01)[2]
    assert nearest_point_distance_m(endpoint, north) == pytest.approx(expected, abs=1e-6)


def test_real_pair_enters_under_40km_only_after_geodesic_measurement() -> None:
    features = {
        feature["properties"]["id"]: feature
        for feature in json.loads((ROOT / "data/build/projects.geojson").read_text(encoding="utf-8"))["features"]
    }
    ashley = shape(features["sertp-p114-46d04f"]["geometry"])
    douglasville = shape(features["sertp-p83-7714c0"]["geometry"])
    projected_m = transform(TO_METRES, ashley).distance(transform(TO_METRES, douglasville))
    geodesic_m = nearest_point_distance_m(ashley, douglasville)
    assert projected_m == pytest.approx(40154.2406, abs=0.01)
    assert geodesic_m == pytest.approx(39967.4107, abs=0.01)
    assert band_for(projected_m) is None
    assert band_for(geodesic_m) == "lt_40km"


def test_mcintosh_pairs_are_shared_endpoints_with_source_limits() -> None:
    features = {
        feature["properties"]["id"]: feature
        for feature in json.loads((ROOT / "data/build/projects.geojson").read_text(encoding="utf-8"))["features"]
    }
    tie = features["desc-p41"]
    relays = features["sertp-p107-9bc088"]
    goshen = features["sertp-p111-fe1e3b"]
    for other in (relays, goshen):
        reason, detail = classify_touch(
            tie["properties"], other["properties"],
            shape(tie["geometry"]), shape(other["geometry"]), 0,
        )
        assert reason == "shared_endpoint"
        assert "McIntosh" in detail
        assert "Deerfield" in detail
        assert "location not stated" in detail
    assert "230 kV" in classify_touch(
        tie["properties"], relays["properties"], shape(tie["geometry"]), shape(relays["geometry"]), 0,
    )[1]
    assert "115 kV" in classify_touch(
        tie["properties"], goshen["properties"], shape(tie["geometry"]), shape(goshen["geometry"]), 0,
    )[1]


def test_unsupported_same_substation_claim_falls_back() -> None:
    a = {"id": "a", "endpoints": ["McIntosh"], "voltage_kv": [115], "accuracy": "approximate",
         "source": {"doc": "A", "page": 1}}
    b = {"id": "b", "endpoints": ["McIntosh"], "voltage_kv": [], "accuracy": "exact",
         "source": {"doc": "B", "page": 2}}
    reason, detail = classify_touch(a, b, Point(0, 0), Point(0, 0), 0)
    assert reason == "same_area_approximate"
    assert "same substation" not in detail.lower()
    b["voltage_kv"] = [230]
    reason, detail = classify_touch(a, b, Point(0, 0), Point(0, 0), 0)
    assert reason == "same_substation"
    assert "McIntosh" in detail
    b["endpoints"] = ["Other"]
    assert classify_touch(a, b, Point(0, 0), Point(0, 0), 0)[0] == "same_area_approximate"


def test_crossing_claim_requires_exact_lines() -> None:
    a = {"id": "a", "endpoints": ["A", "B"], "voltage_kv": [115], "accuracy": "exact",
         "source": {"doc": "A", "page": 1}}
    b = {"id": "b", "endpoints": ["C", "D"], "voltage_kv": [230], "accuracy": "exact",
         "source": {"doc": "B", "page": 2}}
    east = LineString([(-1, 0), (1, 0)])
    north = LineString([(0, -1), (0, 1)])
    assert classify_touch(a, b, east, north, 0)[0] == "lines_cross"
    b["accuracy"] = "approximate"
    assert classify_touch(a, b, east, north, 0)[0] == "same_area_approximate"
    assert classify_touch(a, b, east, north, 100)[0] == "proximity"


def test_share_wording_depends_on_band_and_reason() -> None:
    assert can_share("touching", "shared_endpoint") != can_share("touching", "proximity")
    assert can_share("touching", "shared_endpoint") != can_share("lt_8km", "shared_endpoint")
    assert "unverified" in can_share("touching", "same_area_approximate").lower()


def test_rank_ties_use_full_distance_then_pair_id() -> None:
    pairs = [
        {"id": "z", "score": 3, "distance_km": 1.0000002},
        {"id": "b", "score": 3, "distance_km": 1.0000001},
        {"id": "a", "score": 3, "distance_km": 1.0000001},
        {"id": "x", "score": 4, "distance_km": 2},
    ]
    assert [pair["id"] for pair in sorted(pairs, key=rank_key)] == ["x", "a", "b", "z"]


def test_built_pairs_publish_reasons_note_and_deterministic_rank() -> None:
    pairs = json.loads((ROOT / "data/build/overlaps.json").read_text(encoding="utf-8"))
    by_id = {pair["id"]: pair for pair in pairs}
    relays = by_id["desc-p41__sertp-p107-9bc088"]
    goshen = by_id["desc-p41__sertp-p111-fe1e3b"]
    for pair in (relays, goshen):
        assert pair["touch_reason"] == "shared_endpoint"
        assert "Deerfield" in pair["touch_detail"]
        assert pair["cross_state"] is True
        assert pair["pair_note"] is None
    georgia = by_id["sertp-p114-46d04f__sertp-p124-e36f41"]
    assert georgia["pair_note"] == "May already plan jointly through Georgia's Integrated Transmission System"
    assert [(pair["rank"], pair["id"]) for pair in pairs] == [
        (rank, pair["id"]) for rank, pair in enumerate(sorted(pairs, key=rank_key), 1)
    ]
