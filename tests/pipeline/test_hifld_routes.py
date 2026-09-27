"""Routing a line project along existing HIFLD lines is used only when it is plausibly the same line."""

import pytest
from shapely.geometry import MultiLineString

from pipeline.hifld_routes import HifldNetwork, volt_class

# About 9.3 km per 0.1 degree of longitude at 33 N; every point sits in Georgia.
A, B, C = (-83.00, 33.00), (-82.90, 33.00), (-82.95, 33.00)


def line(start, end, sub_1, sub_2, kv=115):
    return {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [list(start), list(end)]},
            "properties": {"SUB_1": sub_1, "SUB_2": sub_2, "VOLTAGE": kv, "VOLT_CLASS": volt_class(kv)}}


def test_direct_line_between_the_two_substations_is_routed() -> None:
    route = HifldNetwork([line(A, B, "ALPHA", "BRAVO")]).route([A, B], [115])
    assert isinstance(route, MultiLineString)
    assert list(route.geoms[0].coords) == [A, B]


def test_route_through_an_unnamed_tap_is_accepted() -> None:
    network = HifldNetwork([line(A, C, "ALPHA", "TAP123"), line(C, B, "TAP123", "BRAVO")])
    assert network.route([A, B], [115]) is not None


def test_route_through_another_named_substation_is_rejected() -> None:
    network = HifldNetwork([line(A, C, "ALPHA", "CHARLIE"), line(C, B, "CHARLIE", "BRAVO")])
    assert network.route([A, B], [115]) is None


def test_long_detour_is_rejected() -> None:
    far = (-82.95, 33.08)   # the path A-far-B is about 2.2 times the straight distance
    network = HifldNetwork([line(A, far, "ALPHA", "TAP1"), line(far, B, "TAP1", "BRAVO")])
    assert network.route([A, B], [115]) is None


@pytest.mark.parametrize(("voltages", "expected"), [([115], False), ([230], True), ([], True)])
def test_route_must_run_on_the_project_voltage_class(voltages, expected) -> None:
    network = HifldNetwork([line(A, B, "ALPHA", "BRAVO", kv=230)])
    assert (network.route([A, B], voltages) is not None) is expected


def test_substation_far_from_any_line_end_is_not_routed() -> None:
    network = HifldNetwork([line(A, B, "ALPHA", "BRAVO")])
    off_network = (-82.90, 33.02)   # about 2.2 km north of the BRAVO line end
    assert network.route([A, off_network], [115]) is None


def test_route_keeps_short_connectors_to_the_matched_substations() -> None:
    near_a = (-83.005, 33.0)        # about 470 m west of the ALPHA line end
    route = HifldNetwork([line(A, B, "ALPHA", "BRAVO")]).route([near_a, B], [115])
    assert route is not None
    assert any(coords[0] == near_a for coords in (list(part.coords) for part in route.geoms))
