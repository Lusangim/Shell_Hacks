"""Fixed local archive ranges and explicitly enabled browser-map configuration."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.schemas import ErrorResponse
from server.settings import Settings


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "api"
ARCHIVE = b"0123456789abcdefghijklmnopqrstuvwxyz"
URL = "/basemap/gasc.pmtiles"


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    archive = tmp_path / "test.pmtiles"
    archive.write_bytes(ARCHIVE)
    monkeypatch.setenv("GRIDLOCK_BASEMAP_PMTILES", str(archive))
    monkeypatch.setenv("GRIDLOCK_GOOGLE", "off")
    monkeypatch.delenv("GRIDLOCK_GOOGLE_MAPS_KEY", raising=False)
    monkeypatch.setenv("GRIDLOCK_GOOGLE_MAPS_KEY_FILE", str(tmp_path / "fake-key.txt"))
    return archive


def client() -> TestClient:
    return TestClient(create_app(artifact_dir=FIXTURES), base_url="http://localhost:8792")


def test_full_archive_and_typed_config(configured: Path) -> None:
    with client() as browser:
        response = browser.get(URL)
        assert response.status_code == 200
        assert response.content == ARCHIVE
        assert response.headers["content-length"] == "36"
        assert response.headers["accept-ranges"] == "bytes"
        assert response.headers["content-type"] == "application/vnd.pmtiles"
        assert "content-range" not in response.headers
        config = browser.get("/api/map-config")
        assert config.json() == {"google_enabled": False, "google_key": None, "offline_available": True}
        schema = browser.get("/openapi.json").json()
        model = schema["components"]["schemas"]["MapConfig"]
        assert set(model["required"]) == {"google_enabled", "google_key", "offline_available"}


@pytest.mark.parametrize(("range_header", "expected", "content_range"), [
    ("bytes=0-3", b"0123", "bytes 0-3/36"),
    ("bytes=10-15", b"abcdef", "bytes 10-15/36"),
    ("bytes=-4", b"wxyz", "bytes 32-35/36"),
    ("bytes=32-", b"wxyz", "bytes 32-35/36"),
    ("bytes=35-35", b"z", "bytes 35-35/36"),
    ("bytes=32-99", b"wxyz", "bytes 32-35/36"),
    ("bytes=-99", ARCHIVE, "bytes 0-35/36"),
])
def test_single_ranges(configured: Path, range_header: str, expected: bytes, content_range: str) -> None:
    with client() as browser:
        response = browser.get(URL, headers={"Range": range_header})
    assert response.status_code == 206
    assert response.content == expected
    assert response.headers["content-range"] == content_range
    assert response.headers["content-length"] == str(len(expected))
    assert response.headers["accept-ranges"] == "bytes"


@pytest.mark.parametrize("range_header", [
    "bytes=36-", "bytes=99-100", "bytes=5-4", "bytes=-0", "bytes=-", "bytes=",
    "bytes=abc-3", "items=0-1", "bytes=0-1,3-4", "bytes=+1-2", "bytes=0-1\tbad",
    "bytes=" + "9" * 5000 + "-", "bytes=0-" + "9" * 5000,
])
def test_invalid_ranges_are_fixed_typed_416(configured: Path, range_header: str) -> None:
    with client() as browser:
        response = browser.get(URL, headers={"Range": range_header})
    assert response.status_code == 416
    assert response.headers["content-range"] == "bytes */36"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.json() == {"error": {"code": "invalid_range", "message": "Requested range not satisfiable"}}
    ErrorResponse.model_validate(response.json())


def test_missing_archive_is_normal_fallback(configured: Path) -> None:
    configured.unlink()
    with client() as browser:
        assert browser.get("/api/health").status_code == 200
        assert browser.get("/api/map-config").json()["offline_available"] is False
        for headers in ({}, {"Range": "bytes=0-3"}):
            response = browser.get(URL, headers=headers)
            assert response.status_code == 404
            assert response.json() == {"error": {"code": "not_found", "message": "Offline basemap not available"}}
            assert str(configured) not in response.text


def test_empty_archive_range_is_unsatisfiable(configured: Path) -> None:
    configured.write_bytes(b"")
    with client() as browser:
        assert browser.get(URL).content == b""
        response = browser.get(URL, headers={"Range": "bytes=0-"})
        assert response.status_code == 416
        assert response.headers["content-range"] == "bytes */0"


def test_duplicate_range_headers_are_rejected(configured: Path) -> None:
    with client() as browser:
        response = browser.get(URL, headers=[("Range", "bytes=0-1"), ("Range", "bytes=4-5")])
        assert response.status_code == 416
        assert response.headers["content-range"] == "bytes */36"
        assert ErrorResponse.model_validate(response.json()).error.code == "invalid_range"


@pytest.mark.parametrize("path", [
    "/basemap/other.pmtiles", "/basemap/%2e%2e/server/settings.py",
    "/basemap/gasc.pmtiles/../../server/settings.py", "/basemap/gasc.pmtiles%2f..%2fsettings.py",
])
def test_path_cannot_choose_file(configured: Path, path: str) -> None:
    with client() as browser:
        response = browser.get(path)
        assert response.status_code == 404
        ErrorResponse.model_validate(response.json())
        assert str(configured) not in response.text
        assert browser.get(URL, params={"path": "../server/settings.py"}).content == ARCHIVE


def test_google_off_never_reads_or_stats_key_file(configured: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original_open, original_stat = Path.open, Path.stat

    def trapped_open(path: Path, *args, **kwargs):
        assert path.name != "fake-key.txt", "disabled Google touched the fake key"
        return original_open(path, *args, **kwargs)

    def trapped_stat(path: Path, *args, **kwargs):
        assert path.name != "fake-key.txt", "disabled Google touched the fake key"
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", trapped_open)
    monkeypatch.setattr(Path, "stat", trapped_stat)
    monkeypatch.setenv("GRIDLOCK_GOOGLE_MAPS_KEY", "fake-ignored-browser-key")
    with client() as browser:
        response = browser.get("/api/map-config")
        assert response.status_code == 200
        assert response.json()["google_key"] is None
        assert response.json()["google_enabled"] is False
        assert response.headers["content-security-policy"] == "default-src 'self'"


@pytest.mark.parametrize("key_source", ["file", "environment", "missing", "empty"])
def test_google_enabled_only_with_configured_fake_key(
    configured: Path, monkeypatch: pytest.MonkeyPatch, key_source: str,
) -> None:
    monkeypatch.setenv("GRIDLOCK_GOOGLE", "on")
    fake_key = "fake-browser-key-for-tests"
    if key_source in {"file", "empty"}:
        (configured.parent / "fake-key.txt").write_text(fake_key + "\n" if key_source == "file" else "\n", encoding="utf-8")
    if key_source == "environment":
        monkeypatch.setenv("GRIDLOCK_GOOGLE_MAPS_KEY", fake_key)
    enabled = key_source in {"file", "environment"}

    def no_outbound(*args, **kwargs):
        raise AssertionError("map configuration attempted outbound traffic")

    with client() as browser:
        monkeypatch.setattr(socket.socket, "connect", no_outbound)
        response = browser.get("/api/map-config")
        assert response.status_code == 200
        assert response.json() == {"google_enabled": enabled, "google_key": fake_key if enabled else None, "offline_available": True}
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["cross-origin-resource-policy"] == "same-origin"
        assert "access-control-allow-origin" not in response.headers
        csp = browser.get("/").headers["content-security-policy"]
        if enabled:
            assert "https://maps.googleapis.com" in csp
            assert "https://maps.gstatic.com" in csp
            assert "default-src 'self'" in csp
            assert "https:" not in csp.split("; ")
        else:
            assert csp == "default-src 'self'"


@pytest.mark.parametrize("headers", [
    {"Origin": "https://example.com"}, {"Origin": "null"},
    {"Origin": "http://localhost:8793"}, {"Sec-Fetch-Site": "cross-site"},
    {"Sec-Fetch-Site": "same-site"},
])
def test_map_config_rejects_cross_origin_reads(configured: Path, monkeypatch: pytest.MonkeyPatch, headers: dict[str, str]) -> None:
    monkeypatch.setenv("GRIDLOCK_GOOGLE", "on")
    monkeypatch.setenv("GRIDLOCK_GOOGLE_MAPS_KEY", "fake-browser-key-for-tests")
    with client() as browser:
        response = browser.get("/api/map-config", headers=headers)
        assert response.status_code == 403
        assert response.json() == {"error": {"code": "invalid_origin", "message": "Same-origin request required"}}
        assert response.headers["cache-control"] == "no-store"
        assert "access-control-allow-origin" not in response.headers


def test_same_origin_and_host_guard(configured: Path) -> None:
    with client() as browser:
        assert browser.get("/api/map-config", headers={"Origin": "http://localhost:8792", "Sec-Fetch-Site": "same-origin"}).status_code == 200
        for path in (URL, "/api/map-config"):
            response = browser.get(path, headers={"Host": "evil.example"})
            assert response.status_code == 400
            assert ErrorResponse.model_validate(response.json()).error.code == "invalid_host"


def test_external_archive_small_read_only_range(configured: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = Path.home() / "dev" / "gridlock-assets" / "gasc-z13.pmtiles"
    monkeypatch.setenv("GRIDLOCK_BASEMAP_PMTILES", str(archive))
    with client() as browser:
        response = browser.get(URL, headers={"Range": "bytes=0-7"})
        if archive.is_file():
            assert response.status_code == 206
            assert response.content == b"PMTiles\x03"
            assert response.headers["content-length"] == "8"
        else:
            assert response.status_code == 404
            assert browser.get("/api/map-config").json()["offline_available"] is False


def test_google_mode_validation(configured: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GRIDLOCK_GOOGLE", "invalid")
    with pytest.raises(ValueError, match="GRIDLOCK_GOOGLE must be 'off' or 'on'"):
        Settings.from_env()


@pytest.mark.parametrize(("google", "has_fake_file", "expected"), [
    ("off", True, "no-referrer"),
    ("on", False, "no-referrer"),
    ("on", True, "strict-origin-when-cross-origin"),
])
def test_referrer_policy_for_browser_key(
    configured: Path, monkeypatch: pytest.MonkeyPatch, google: str, has_fake_file: bool, expected: str,
) -> None:
    monkeypatch.setenv("GRIDLOCK_GOOGLE", google)
    if has_fake_file:
        (configured.parent / "fake-key.txt").write_text("fake-browser-key-for-tests", encoding="utf-8")
    with client() as browser:
        for path in ("/", "/web/index.html", "/api/map-config"):
            response = browser.get(path)
            assert response.status_code == 200
            assert response.headers["referrer-policy"] == expected
