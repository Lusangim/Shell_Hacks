"""The area explorer uses mapped geometry and preserves pair data."""

from __future__ import annotations

import copy
import json
import shutil
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.schemas import Area, ErrorResponse
from server.settings import ROOT


FIXTURES = ROOT / "tests" / "fixtures" / "api"
MCINTOSH = {"lat": "32.3521162", "lon": "-81.1751124"}


@pytest.fixture
def real_client() -> TestClient:
    with TestClient(create_app(artifact_dir=ROOT / "data" / "build"), base_url="http://localhost") as client:
        yield client


@pytest.fixture
def crossing_artifacts(tmp_path: Path) -> Path:
    for source, target in (
        ("projects.json", "projects.json"),
        ("overlaps.json", "overlaps.json"),
        ("meta.json", "meta.json"),
        ("basemap.json", "basemap.json"),
    ):
        shutil.copyfile(FIXTURES / source, tmp_path / target)
    collection = json.loads((tmp_path / "projects.json").read_text(encoding="utf-8"))
    crossing = collection["features"][0]
    crossing["geometry"] = {"type": "LineString", "coordinates": [[-81.02, 32.0], [-80.98, 32.0]]}
    far = collection["features"][1]
    far["geometry"] = {"type": "Point", "coordinates": [-80.7, 32.0]}
    unknown = copy.deepcopy(far)
    unknown["properties"]["id"] = "sertp-p2-abcdef"
    unknown["properties"]["accuracy"] = "unknown"
    unknown["properties"]["location_source"] = None
    unknown["geometry"] = None
    collection["features"].append(unknown)
    (tmp_path / "projects.json").write_text(json.dumps(collection), encoding="utf-8")
    return tmp_path


def area(client: TestClient, params: dict[str, str]) -> Area:
    response = client.get("/api/area", params=params)
    assert response.status_code == 200
    return Area.model_validate(response.json())


def test_real_mcintosh_one_km_case_has_exact_ids_counts_and_order(real_client: TestClient) -> None:
    params = {**MCINTOSH, "radius_km": "1"}
    first = area(real_client, params)
    second = area(real_client, params)
    assert first == second
    assert (first.center.lat, first.center.lon, first.radius_km) == (32.3521162, -81.1751124, 1)
    assert [project.properties.id for project in first.projects] == [
        "desc-p41", "sertp-p107-9bc088", "sertp-p111-fe1e3b", "sertp-p113-5484a4",
    ]
    assert first.counts_by_utility == {"Dominion Energy SC": 1, "Georgia Power": 3}
    assert len(first.overlaps) == 20
    assert first.counts_by_band == {"touching": 2, "lt_1_6km": 1, "lt_8km": 3, "lt_40km": 14}
    assert [pair.rank for pair in first.overlaps] == sorted(pair.rank for pair in first.overlaps)
    assert first.overlaps[0].id == "desc-p41__sertp-p107-9bc088"
    assert all(pair.a in {p.properties.id for p in first.projects} or pair.b in {p.properties.id for p in first.projects} for pair in first.overlaps)


def test_line_crossing_with_endpoints_outside_and_one_sided_pair(crossing_artifacts: Path) -> None:
    with TestClient(create_app(artifact_dir=crossing_artifacts), base_url="http://localhost") as client:
        result = area(client, {"lat": "32", "lon": "-81", "radius_km": "1"})
    assert [project.properties.id for project in result.projects] == ["desc-p1"]
    assert [pair.id for pair in result.overlaps] == ["desc-p1__sertp-p1-abcdef"]
    assert result.counts_by_utility == {"Dominion Energy SC": 1}
    assert result.counts_by_band == {"touching": 1}


def test_axis_reversal_does_not_relocate_projects(crossing_artifacts: Path) -> None:
    with TestClient(create_app(artifact_dir=crossing_artifacts), base_url="http://localhost") as client:
        right = area(client, {"lat": "32", "lon": "-81", "radius_km": "1"})
        reversed_axes = area(client, {"lat": "-81", "lon": "32", "radius_km": "1"})
    assert len(right.projects) == 1
    assert reversed_axes.projects == []
    assert reversed_axes.overlaps == []
    assert reversed_axes.counts_by_utility == {}
    assert reversed_axes.counts_by_band == {}


def test_default_radius_and_both_valid_edges(real_client: TestClient) -> None:
    default = area(real_client, MCINTOSH)
    assert default.radius_km == 40
    assert any(project.properties.id == "sertp-p107-9bc088" for project in default.projects)
    assert area(real_client, {**MCINTOSH, "radius_km": "1"}).radius_km == 1
    assert area(real_client, {**MCINTOSH, "radius_km": "80"}).radius_km == 80


@pytest.mark.parametrize("params", [
    {"lat": "91", "lon": "-81"},
    {"lat": "-91", "lon": "-81"},
    {"lat": "32", "lon": "181"},
    {"lat": "32", "lon": "-181"},
    {"lat": "nan", "lon": "-81"},
    {"lat": "inf", "lon": "-81"},
    {"lat": "32", "lon": "nan"},
    {"lat": "32", "lon": "-inf"},
    {"lat": "32", "lon": "-81", "radius_km": "0.9999"},
    {"lat": "32", "lon": "-81", "radius_km": "80.0001"},
    {"lat": "32", "lon": "-81", "radius_km": "nan"},
    {"lat": "32", "lon": "-81", "radius_km": "inf"},
    {"lat": "32", "lon": "-81", "radius_km": "-1"},
    {"lat": "32"},
])
def test_invalid_area_input_is_typed_422(real_client: TestClient, params: dict[str, str]) -> None:
    response = real_client.get("/api/area", params=params)
    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "invalid_request"


def test_area_stays_local(real_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def deny_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket.socket, "connect", deny_socket)
    assert area(real_client, {**MCINTOSH, "radius_km": "1"}).projects
