"""Local search results keep their coordinates tied to built artifacts."""

from __future__ import annotations

import json
import shutil
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from server.app import create_app
from server.schemas import ErrorResponse, SearchResult
from server.settings import ROOT


BUILD = ROOT / "data" / "build"
FIXTURES = ROOT / "tests" / "fixtures" / "api"
RESULTS = TypeAdapter(list[SearchResult])


@pytest.fixture
def real_client() -> TestClient:
    with TestClient(create_app(artifact_dir=BUILD), base_url="http://localhost") as client:
        yield client


@pytest.fixture
def synthetic_artifacts(tmp_path: Path) -> Path:
    for source, target in (
        ("projects.json", "projects.json"),
        ("overlaps.json", "overlaps.json"),
        ("meta.json", "meta.json"),
        ("basemap.json", "basemap.json"),
    ):
        shutil.copyfile(FIXTURES / source, tmp_path / target)
    return tmp_path


def search(client: TestClient, query: str) -> list[SearchResult]:
    response = client.get("/api/search", params={"q": query})
    assert response.status_code == 200
    return RESULTS.validate_python(response.json())


def test_savannah_place_is_first_with_census_coordinates(real_client: TestClient) -> None:
    result = search(real_client, "sav")
    assert result
    assert result[0].type == "place"
    assert result[0].label == "Savannah city"
    assert (result[0].lat, result[0].lon) == (32.018043, -81.196492)
    assert result[0].ref is None


def test_okatie_returns_placed_project_and_source_backed_endpoint(real_client: TestClient) -> None:
    result = search(real_client, "okat")
    project = next(item for item in result if item.type == "project" and item.ref == "desc-p11")
    assert project.label == "Okatie 230-115kV Substation, Jasper – Yemassee 230kV #1 Fold-in"
    assert (project.lat, project.lon) == (32.335008, -81.030859)
    endpoint = next(item for item in result if item.type == "substation" and item.label == "Okatie")
    assert endpoint.ref == "desc-p11"
    assert (endpoint.lat, endpoint.lon) == (32.335008, -81.030859)


def test_named_substation_uses_placed_point_and_unknown_is_omitted(real_client: TestClient) -> None:
    result = search(real_client, "mcintosh")
    station = next(item for item in result if item.type == "substation" and item.label == "MCINTOSH")
    assert station.ref == "sertp-p107-9bc088"
    assert (station.lat, station.lon) == (32.3521162, -81.1751124)
    assert all(item.label != "Long Savannah" or item.type != "substation" for item in search(real_client, "long savannah"))


def test_word_start_match_and_ten_result_deterministic_cap(real_client: TestClient) -> None:
    assert any(item.type == "project" and "Gills Creek" in item.label for item in search(real_client, "gills"))
    first = search(real_client, "re")
    second = search(real_client, "re")
    assert len(first) == 10
    assert first == second


@pytest.mark.parametrize("query", ["", "s", "  "])
def test_short_query_is_typed_422(real_client: TestClient, query: str) -> None:
    response = real_client.get("/api/search", params={"q": query})
    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "invalid_request"


def test_no_result_and_special_characters_are_safe(real_client: TestClient) -> None:
    assert search(real_client, "zzzz-no-such-place") == []
    assert search(real_client, ".*") == []
    assert search(real_client, "<script>") == []


def test_synthetic_fixture_without_places_still_starts(synthetic_artifacts: Path) -> None:
    with TestClient(create_app(artifact_dir=synthetic_artifacts), base_url="http://localhost") as client:
        result = search(client, "synthetic")
    assert any(item.type == "project" and item.ref == "desc-p1" for item in result)
    assert not any(item.type == "place" for item in result)


def test_production_requires_places_artifact(synthetic_artifacts: Path) -> None:
    (synthetic_artifacts / "projects.json").rename(synthetic_artifacts / "projects.geojson")
    with pytest.raises(RuntimeError, match="places.json"):
        with TestClient(create_app(artifact_dir=synthetic_artifacts)):
            pass


def test_present_places_are_validated_and_loaded_once(synthetic_artifacts: Path) -> None:
    places = synthetic_artifacts / "places.json"
    places.write_text(json.dumps([{"name": "Synthetic place", "state": "GA", "lat": 32, "lon": -81}]), encoding="utf-8")
    with TestClient(create_app(artifact_dir=synthetic_artifacts), base_url="http://localhost") as client:
        original = search(client, "synthetic")
        places.write_text("{}", encoding="utf-8")
        assert search(client, "synthetic") == original
    with pytest.raises(RuntimeError, match="places.json"):
        with TestClient(create_app(artifact_dir=synthetic_artifacts)):
            pass


def test_search_does_not_open_an_outbound_socket(real_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def deny_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket.socket, "connect", deny_socket)
    assert search(real_client, "sav")
