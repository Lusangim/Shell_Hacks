"""Founder-approved location rules (2026-09-26, option C), checked on the committed build.

- A line whose route no single HIFLD line gives may follow existing HIFLD lines, only when confident.
- A town centre never stands in for a line end when a real substation end is known.
- A project located only at town centres stays on the map, flagged; on its own it cannot put a pair
  closer than "under 40 km", unless both plans name the same substation.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from pipeline.overlap_geometry import NAME_MATCH_REASONS, TOWN_CAP_NOTE, band_for, town_capped_band
from server.schemas import Overlap

ROOT = Path(__file__).resolve().parents[2]
BUILT = ROOT / "data" / "build"


@pytest.fixture(scope="module")
def built():
    projects = json.loads((BUILT / "projects.geojson").read_text(encoding="utf-8"))["features"]
    overlaps = json.loads((BUILT / "overlaps.json").read_text(encoding="utf-8"))
    places = json.loads((BUILT / "places.json").read_text(encoding="utf-8"))
    towns = {(round(p["lon"], 5), round(p["lat"], 5)) for p in places}
    return {f["properties"]["id"]: f for f in projects}, overlaps, towns


def _coords(geometry):
    if geometry["type"] == "Point":
        return [geometry["coordinates"]]
    if geometry["type"] == "LineString":
        return geometry["coordinates"]
    return [c for part in geometry["coordinates"] for c in part]


@pytest.mark.parametrize(("band", "reason", "town_only", "expected"), [
    ("touching", "proximity", True, ("lt_40km", True)),
    ("lt_8km", "same_area_approximate", True, ("lt_40km", True)),
    ("lt_1_6km", "proximity", True, ("lt_40km", True)),
    ("touching", "shared_endpoint", True, ("touching", False)),
    ("touching", "same_substation", True, ("touching", False)),
    ("lt_40km", "proximity", True, ("lt_40km", False)),
    ("touching", "proximity", False, ("touching", False)),
])
def test_town_capped_band(band, reason, town_only, expected) -> None:
    assert town_capped_band(band, reason, town_only) == expected


def test_town_only_projects_are_placed_approximate_and_say_so(built) -> None:
    projects, _, towns = built
    town_only = [f for f in projects.values() if f["properties"]["town_only"]]
    assert len(town_only) == 43
    for feature in town_only:
        props = feature["properties"]
        assert feature["geometry"] is not None and props["accuracy"] == "approximate", props["id"]
        assert props["location_source"].startswith("Only the town"), props["id"]
        assert "Census town centre" in props["location_source"], props["id"]
        assert all((round(c[0], 5), round(c[1], 5)) in towns for c in _coords(feature["geometry"])), props["id"]


def test_no_line_is_drawn_to_a_town_centre_when_a_substation_end_is_known(built) -> None:
    projects, _, towns = built
    for feature in projects.values():
        props = feature["properties"]
        if feature["geometry"] is None or props["town_only"]:
            continue
        if feature["geometry"]["type"] in ("LineString", "MultiLineString"):
            points = _coords(feature["geometry"])
            assert not any((round(c[0], 5), round(c[1], 5)) in towns for c in points), props["id"]


def test_routed_lines_follow_hifld_and_stay_approximate(built) -> None:
    projects, _, _ = built
    routed = [f for f in projects.values()
              if (f["properties"]["location_source"] or "").startswith("Follows existing HIFLD transmission lines")]
    assert len(routed) == 10
    for feature in routed:
        props = feature["properties"]
        assert feature["geometry"]["type"] == "MultiLineString", props["id"]
        assert props["accuracy"] == "approximate" and not props["town_only"], props["id"]
        assert "the plan gives no route" in props["location_source"], props["id"]


def test_hand_placed_okatie_line_is_not_routed_and_keeps_its_inferred_note(built) -> None:
    projects, _, _ = built
    source = projects["desc-p12"]["properties"]["location_source"]
    assert source.startswith("Straight line between") and "Hand-placed" in source and "INFERRED" in source


def test_town_only_locations_cannot_make_a_close_pair_on_their_own(built) -> None:
    projects, overlaps, _ = built
    capped = [pair for pair in overlaps if pair["town_capped"]]
    assert len(capped) == 15
    for pair in overlaps:
        town = projects[pair["a"]]["properties"]["town_only"] or projects[pair["b"]]["properties"]["town_only"]
        if pair["town_capped"]:
            assert town and pair["band"] == "lt_40km", pair["id"]
            assert band_for(pair["distance_km"] * 1000) != "lt_40km", pair["id"]
            assert pair["touch_reason"] not in NAME_MATCH_REASONS, pair["id"]
            assert TOWN_CAP_NOTE in pair["touch_detail"], pair["id"]
        elif town and pair["band"] != "lt_40km":
            assert pair["touch_reason"] in NAME_MATCH_REASONS, pair["id"]


def _overlap(**changes) -> dict:
    base = dict(id="a__b", a="a", b="b", a_utility="X", b_utility="Y", a_name="A", b_name="B",
                distance_km=0.0, band="touching", band_label="Touching / crossing", touch_reason="proximity",
                touch_detail="d", can_share="c", a_year=None, b_year=None, year_gap=None, timeline="unknown",
                cross_state=False, pair_note=None, accuracy_pair="approximate", rank=1,
                savings={"status": "unknown_year", "low_usd": None, "high_usd": None, "basis": "b",
                         "assumption_ids": []},
                brief_status="none")
    base.update(changes)
    weight = {"touching": 4, "lt_1_6km": 3, "lt_8km": 2, "lt_40km": 1}[base["band"]]
    base["score_parts"] = dict(band=weight, timing=0.3, location=0.8, state_line=1.0, savings=1.0)
    base["score"] = round(weight * 0.3 * 0.8, 3)
    return base


def test_contract_accepts_only_a_real_town_cap() -> None:
    Overlap.model_validate(_overlap(band="lt_40km", town_capped=True))
    with pytest.raises(ValidationError):
        Overlap.model_validate(_overlap(band="touching", town_capped=True))
    with pytest.raises(ValidationError):
        Overlap.model_validate(_overlap(distance_km=12.0, band="lt_40km", town_capped=True))
    with pytest.raises(ValidationError):
        Overlap.model_validate(_overlap(band="lt_40km"))
