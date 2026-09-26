"""The API fixtures and boundary rules stay in lockstep with the public contract."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from server.schemas import (
    Area,
    Brief,
    BriefSavings,
    ErrorResponse,
    Meta,
    MultiLineGeometry,
    Overlap,
    ProjectCollection,
    ProjectFeature,
    SearchResult,
)
from server.export_contracts import exported_schemas


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "api"
CONTRACTS = ROOT / "contracts"


@pytest.mark.parametrize(
    ("name", "model"),
    [
        ("projects", ProjectCollection),
        ("overlaps", list[Overlap]),
        ("meta", Meta),
        ("area", Area),
        ("brief", Brief),
        ("search", list[SearchResult]),
        ("error", ErrorResponse),
        ("basemap", dict),
    ],
)
def test_normal_fixtures_validate(name, model):
    from pydantic import TypeAdapter

    value = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    TypeAdapter(model).validate_python(value)


@pytest.mark.parametrize("name", ["empty", "unknown-location", "no-cost", "stale-brief", "malicious-string"])
def test_edge_project_fixtures_validate(name):
    value = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    ProjectCollection.model_validate(value)


def test_schemas_exported_for_every_model():
    expected = {"project", "projects", "overlap", "brief", "area", "meta", "search-result", "error"}
    for name in expected:
        schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema == exported_schemas()[name]


def test_unknown_location_has_no_geometry_and_no_fake_coordinates():
    value = json.loads((FIXTURES / "unknown-location.json").read_text(encoding="utf-8"))
    feature = ProjectFeature.model_validate(value["features"][0])
    assert feature.geometry is None
    assert feature.properties.accuracy == "unknown"


def test_invalid_pair_order_and_savings_range_rejected():
    value = json.loads((FIXTURES / "overlaps.json").read_text(encoding="utf-8"))[0]
    value["a"], value["b"] = value["b"], value["a"]
    with pytest.raises(ValidationError):
        Overlap.model_validate(value)
    value = json.loads((FIXTURES / "overlaps.json").read_text(encoding="utf-8"))[0]
    value["savings"]["low_usd"] = value["savings"]["high_usd"] + 1
    with pytest.raises(ValidationError):
        Overlap.model_validate(value)


def test_out_of_band_distance_rejected():
    value = json.loads((FIXTURES / "overlaps.json").read_text(encoding="utf-8"))[0]
    value["distance_km"] = 40
    with pytest.raises(ValidationError):
        Overlap.model_validate(value)


def test_impossible_coordinates_rejected():
    value = json.loads((FIXTURES / "projects.json").read_text(encoding="utf-8"))
    value["features"][0]["geometry"]["coordinates"] = [181, 91]
    with pytest.raises(ValidationError):
        ProjectCollection.model_validate(value)


@pytest.mark.parametrize("low,high", [(300, 100), (None, None)])
def test_brief_range_needs_ordered_bounds(low, high):
    value = json.loads((FIXTURES / "brief.json").read_text(encoding="utf-8"))["savings_range"]
    value.update(status="range", low_usd=low, high_usd=high)
    with pytest.raises(ValidationError):
        BriefSavings.model_validate(value)


def test_brief_non_range_has_no_numeric_bounds():
    value = json.loads((FIXTURES / "brief.json").read_text(encoding="utf-8"))["savings_range"]
    value.update(status="no_cost", low_usd=100, high_usd=200)
    with pytest.raises(ValidationError):
        BriefSavings.model_validate(value)


def test_same_utility_overlap_rejected():
    value = json.loads((FIXTURES / "overlaps.json").read_text(encoding="utf-8"))[0]
    value["b_utility"] = value["a_utility"]
    with pytest.raises(ValidationError):
        Overlap.model_validate(value)


@pytest.mark.parametrize("line", [[], [[-81, 32]]])
def test_multiline_members_need_two_positions(line):
    with pytest.raises(ValidationError):
        MultiLineGeometry.model_validate({"type": "MultiLineString", "coordinates": [line]})


def test_negative_area_and_meta_counts_rejected():
    area = json.loads((FIXTURES / "area.json").read_text(encoding="utf-8"))
    area["counts_by_band"]["touching"] = -1
    with pytest.raises(ValidationError):
        Area.model_validate(area)
    meta = json.loads((FIXTURES / "meta.json").read_text(encoding="utf-8"))
    meta["stage_counts"]["kept"] = -1
    with pytest.raises(ValidationError):
        Meta.model_validate(meta)


def test_area_counts_match_returned_members():
    area = json.loads((FIXTURES / "area.json").read_text(encoding="utf-8"))
    area["counts_by_utility"]["Georgia Power"] = 2
    with pytest.raises(ValidationError):
        Area.model_validate(area)
    area = json.loads((FIXTURES / "area.json").read_text(encoding="utf-8"))
    area["counts_by_band"]["touching"] = 2
    with pytest.raises(ValidationError):
        Area.model_validate(area)
