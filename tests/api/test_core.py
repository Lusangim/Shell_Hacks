"""Contract and local-only behavior of the walking-skeleton API."""

from __future__ import annotations

import json
import shutil
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from server.app import Basemap, Health, create_app
from server.schemas import ErrorResponse, Meta, Overlap, ProjectCollection, ProjectFeature
from server.settings import Settings


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "api"


@pytest.fixture
def artifacts(tmp_path: Path) -> Path:
    for source, target in (
        ("projects.json", "projects.json"),
        ("overlaps.json", "overlaps.json"),
        ("meta.json", "meta.json"),
        ("basemap.json", "basemap.json"),
    ):
        shutil.copyfile(FIXTURES / source, tmp_path / target)
    return tmp_path


@pytest.fixture
def client(artifacts: Path) -> TestClient:
    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as test_client:
        yield test_client


def test_happy_paths_and_contracts(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert Health.model_validate(health.json()).status == "ok"

    meta = client.get("/api/meta")
    assert meta.status_code == 200
    assert Meta.model_validate(meta.json()).stage_counts["kept"] == 2
    assert meta.json()["hotspots"] == json.loads((FIXTURES / "meta.json").read_text(encoding="utf-8"))["hotspots"]

    basemap = client.get("/api/basemap")
    assert basemap.status_code == 200
    assert Basemap.model_validate(basemap.json()).features == []

    projects = client.get("/api/projects")
    assert projects.status_code == 200
    collection = ProjectCollection.model_validate(projects.json())
    assert [p.properties.id for p in collection.features] == ["desc-p1", "sertp-p1-abcdef"]

    detail = client.get("/api/projects/desc-p1")
    assert detail.status_code == 200
    assert ProjectFeature.model_validate(detail.json()).properties.name == "Synthetic test project"

    overlaps = client.get("/api/overlaps")
    assert overlaps.status_code == 200
    assert [o.rank for o in TypeAdapter(list[Overlap]).validate_python(overlaps.json())] == [1]


def test_project_filters_and_both_project_overlap_semantics(client: TestClient) -> None:
    assert len(ProjectCollection.model_validate(client.get("/api/projects?utility=Georgia%20Power").json()).features) == 1
    assert len(ProjectCollection.model_validate(client.get("/api/projects?voltage_kv=115&year=2028&project_type=other").json()).features) == 2
    assert len(ProjectCollection.model_validate(client.get("/api/projects?year=2029").json()).features) == 0
    assert TypeAdapter(list[Overlap]).validate_python(client.get("/api/overlaps?utility=Georgia%20Power").json()) == []
    both = client.get("/api/overlaps", params=[("utility", "Georgia Power"), ("utility", "Dominion Energy SC")])
    assert len(TypeAdapter(list[Overlap]).validate_python(both.json())) == 1
    assert TypeAdapter(list[Overlap]).validate_python(client.get("/api/overlaps?band=lt_40km").json()) == []
    assert len(TypeAdapter(list[Overlap]).validate_python(client.get("/api/overlaps?cross_state=true&limit=1&offset=0").json())) == 1
    assert TypeAdapter(list[Overlap]).validate_python(client.get("/api/overlaps?offset=1").json()) == []


@pytest.mark.parametrize("path", [
    "/api/projects?year=bogus",
    "/api/projects?voltage_kv=-1",
    "/api/projects?project_type=unlisted",
    "/api/projects?year_min=2030&year_max=2020",
    "/api/overlaps?limit=501",
    "/api/overlaps?limit=0",
    "/api/overlaps?offset=-1",
    "/api/overlaps?band=bogus",
    "/api/overlaps?cross_state=bogus",
    "/api/overlaps?year_min=2030&year_max=2020",
])
def test_invalid_filters_return_typed_422(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "invalid_request"


def test_unknown_project_and_bad_host_have_typed_errors(client: TestClient) -> None:
    missing = client.get("/api/projects/missing")
    assert missing.status_code == 404
    assert ErrorResponse.model_validate(missing.json()).error.code == "not_found"
    hostile = client.get("/api/health", headers={"Host": "example.com"})
    assert hostile.status_code == 400
    assert ErrorResponse.model_validate(hostile.json()).error.code == "invalid_host"


def test_security_headers_on_success_and_error(client: TestClient) -> None:
    for response in (client.get("/api/health"), client.get("/api/projects/missing")):
        assert response.headers["content-security-policy"] == "default-src 'self'"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert "access-control-allow-origin" not in response.headers


def test_page_and_modules_are_revalidated_so_updates_never_run_stale(client: TestClient) -> None:
    for path in ("/", "/web/js/app.js", "/web/css/app.css"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.headers["cache-control"] == "no-cache", path
    assert "cache-control" not in client.get("/api/health").headers


def test_startup_refuses_missing_and_invalid_artifacts(artifacts: Path) -> None:
    (artifacts / "meta.json").unlink()
    with pytest.raises(RuntimeError, match="meta.json"):
        with TestClient(create_app(artifact_dir=artifacts)):
            pass
    (artifacts / "meta.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="meta.json"):
        with TestClient(create_app(artifact_dir=artifacts)):
            pass


@pytest.mark.parametrize("artifact", ["projects.json", "overlaps.json", "meta.json", "basemap.json"])
def test_startup_names_each_invalid_artifact(artifacts: Path, artifact: str) -> None:
    (artifacts / artifact).write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match=artifact):
        with TestClient(create_app(artifact_dir=artifacts)):
            pass


def test_settings_read_environment_at_runtime(artifacts: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GRIDLOCK_ARTIFACT_DIR", str(artifacts))
    monkeypatch.setenv("GRIDLOCK_AI", "off")
    monkeypatch.setenv("GRIDLOCK_TEST_PORT", "8772")
    config = Settings.from_env()
    assert config.artifact_dir == artifacts
    assert config.ai == "off"
    assert config.port == 8772
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/api/health").status_code == 200


def test_geojson_artifact_takes_precedence_over_fixture_name(artifacts: Path) -> None:
    (artifacts / "projects.geojson").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="projects.geojson"):
        with TestClient(create_app(artifact_dir=artifacts)):
            pass


def test_artifacts_are_loaded_once_at_startup(artifacts: Path) -> None:
    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as client:
        original = client.get("/api/meta").json()
        (artifacts / "meta.json").write_text(json.dumps({"invalid": True}), encoding="utf-8")
        assert client.get("/api/meta").json() == original


def test_in_process_api_never_opens_a_socket(artifacts: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def deny_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("socket opened")

    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as client:
        monkeypatch.setattr(socket.socket, "connect", deny_socket)
        assert client.get("/api/projects").status_code == 200
