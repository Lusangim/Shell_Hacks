"""Local brief routes: validated cache, fixed fallbacks, and spend guards."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.brief_cache import cache_key, cache_path, write_cached_brief
from server.brief_generator import MODEL_ID, PROMPT_VERSION
from server.brief_routes import get_brief_client
from server.brief_template import make_template_brief
from server.schemas import Brief, ErrorResponse, Meta
from server.settings import Settings
from tests.eval.grader import grade_brief, load_contacts


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "data" / "build"
CONTACTS = load_contacts(ROOT / "data" / "manual" / "contacts.json")
PAIR_ID = "desc-p41__sertp-p107-9bc088"
URL = f"/api/briefs/{PAIR_ID}"
POST_HEADERS = {"Origin": "http://localhost", "X-GridLock": "1"}


class FakeMessages:
    def __init__(self, responses: list[object]):
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def parse(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeClient:
    def __init__(self, responses: list[object]):
        self.messages = FakeMessages(responses)


def app_for(tmp_path: Path, *, ai: str = "off", ceiling: str = "0", cap: int = 5,
            fake: FakeClient | None = None):
    config = Settings(
        artifact_dir=BUILD, ai=ai, port=8772, brief_cache_dir=tmp_path,
        spend_ceiling_usd=Decimal(ceiling), max_ondemand=cap,
    )
    app = create_app(settings=config)
    if fake is not None:
        app.dependency_overrides[get_brief_client] = lambda: fake
    return app


def case(client: TestClient):
    artifacts = client.app.state.artifacts
    pair = next(item for item in artifacts.overlaps if item.id == PAIR_ID)
    projects = {item.properties.id: item for item in artifacts.projects.features}
    return pair, projects[pair.a], projects[pair.b]


def model_response(client: TestClient, *, stop_reason: str = "end_turn") -> object:
    pair, a, b = case(client)
    return SimpleNamespace(stop_reason=stop_reason, parsed_output=make_template_brief(pair, a, b, CONTACTS))


def validated(client: TestClient, response, status: str) -> Brief:
    assert response.status_code == 200
    assert response.headers["x-gridlock-brief-status"] == status
    brief = Brief.model_validate(response.json())
    pair, a, b = case(client)
    assert brief.overlap_id == pair.id
    assert grade_brief(brief, pair, a, b, CONTACTS).ok
    return brief


def seeded_cache(client: TestClient, tmp_path: Path) -> Brief:
    pair, a, b = case(client)
    key = cache_key(pair, a, b, CONTACTS, PROMPT_VERSION, MODEL_ID)
    brief = make_template_brief(pair, a, b, CONTACTS).model_copy(update={
        "generated_by": MODEL_ID, "prompt_version": PROMPT_VERSION,
        "generated_at": "2026-09-26T10:00:00+00:00", "input_hash": key,
    })
    write_cached_brief(tmp_path, brief)
    return brief


def test_get_template_cached_stale_and_meta_count(tmp_path: Path) -> None:
    with TestClient(app_for(tmp_path), base_url="http://localhost") as client:
        template = validated(client, client.get(URL), "template")
        assert template.generated_by == "template"
        assert Meta.model_validate(client.get("/api/meta").json()).stale_brief_count == 0
        cached = seeded_cache(client, tmp_path)
        assert validated(client, client.get(URL), "cached") == cached
        assert Meta.model_validate(client.get("/api/meta").json()).stale_brief_count == 0

        path = cache_path(tmp_path, PAIR_ID)
        document = json.loads(path.read_text(encoding="utf-8"))
        document["cache_key"] = "0" * 64
        document["brief"]["input_hash"] = "0" * 64
        path.write_text(json.dumps(document), encoding="utf-8")
        assert validated(client, client.get(URL), "stale") == template
        assert Meta.model_validate(client.get("/api/meta").json()).stale_brief_count == 1

        path.write_text("{bad json", encoding="utf-8")
        assert validated(client, client.get(URL), "template") == template
        assert Meta.model_validate(client.get("/api/meta").json()).stale_brief_count == 0


@pytest.mark.parametrize("bad_id", ["unknown__pair", "..%2F..%2Fetc", "DESC-P41__sertp-p107-9bc088"])
def test_unknown_or_noncanonical_id_is_fixed_404(tmp_path: Path, bad_id: str) -> None:
    with TestClient(app_for(tmp_path), base_url="http://localhost") as client:
        response = client.get(f"/api/briefs/{bad_id}")
        assert response.status_code == 404
        assert ErrorResponse.model_validate(response.json()).error.message == "Brief overlap not found"
        post = client.post(f"/api/briefs/{bad_id}/generate", headers=POST_HEADERS)
        assert post.status_code == 404
        assert ErrorResponse.model_validate(post.json()).error.message == "Brief overlap not found"


@pytest.mark.parametrize("headers", [
    {}, {"X-GridLock": "1"}, {"Origin": "http://localhost"},
    {"Origin": "https://evil.example", "X-GridLock": "1"},
    {"Origin": "http://localhost.evil.example", "X-GridLock": "1"},
    {"Origin": "http://localhost@evil.example", "X-GridLock": "1"},
    {"Origin": "http://localhost/path", "X-GridLock": "1"},
    {"Origin": "https://localhost", "X-GridLock": "1"},
    {"Origin": "http://localhost:8772", "X-GridLock": "1"},
    {"Origin": "null", "X-GridLock": "1"},
    {"Origin": "http://localhost", "X-GridLock": "0"},
])
def test_post_rejects_forged_origin_or_header_without_calls(tmp_path: Path, headers: dict[str, str]) -> None:
    fake = FakeClient([])
    with TestClient(app_for(tmp_path, ai="on", ceiling="1", fake=fake), base_url="http://localhost") as client:
        response = client.post(f"{URL}/generate", headers=headers)
        assert response.status_code == 403
        assert ErrorResponse.model_validate(response.json()).error.message == "Brief generation request forbidden"
        assert fake.messages.calls == []


def test_post_rejects_bad_host_ai_off_missing_client_and_ceiling(tmp_path: Path) -> None:
    fake = FakeClient([])
    with TestClient(app_for(tmp_path, ai="on", ceiling="1", fake=fake), base_url="http://localhost") as client:
        response = client.post(f"{URL}/generate", headers={**POST_HEADERS, "Host": "evil.example"})
        assert response.status_code == 400
        assert ErrorResponse.model_validate(response.json()).error.code == "invalid_host"
    for ai, ceiling, injected in (("off", "1", fake), ("on", "0", fake), ("on", "1", None)):
        with TestClient(app_for(tmp_path, ai=ai, ceiling=ceiling, fake=injected), base_url="http://localhost") as client:
            response = client.post(f"{URL}/generate", headers=POST_HEADERS)
            assert response.status_code == 409
            assert ErrorResponse.model_validate(response.json()).error.message == "Brief generation unavailable"
    assert fake.messages.calls == []


def test_same_origin_127_port_accepts_fake_but_forwarded_host_cannot_bypass(tmp_path: Path) -> None:
    fake = FakeClient([])
    with TestClient(app_for(tmp_path, ai="on", ceiling="1", fake=fake), base_url="http://127.0.0.1:8772") as client:
        forged = client.post(
            f"{URL}/generate",
            headers={"Origin": "http://evil.example", "X-GridLock": "1", "X-Forwarded-Host": "evil.example"},
        )
        assert forged.status_code == 403
        assert fake.messages.calls == []
        fake.messages.responses.append(model_response(client))
        accepted = client.post(
            f"{URL}/generate", headers={"Origin": "http://127.0.0.1:8772", "X-GridLock": "1"},
        )
        validated(client, accepted, "cached")
        assert len(fake.messages.calls) == 1


def test_budget_below_single_reservation_rejects_without_call(tmp_path: Path) -> None:
    fake = FakeClient([])
    with TestClient(app_for(tmp_path, ai="on", ceiling="0.23", fake=fake), base_url="http://localhost") as client:
        response = client.post(f"{URL}/generate", headers=POST_HEADERS)
        assert response.status_code == 409
        assert ErrorResponse.model_validate(response.json()).error.message == "Brief generation unavailable"
        assert fake.messages.calls == []


def test_post_model_cache_atomic_publication_and_cap(tmp_path: Path) -> None:
    fake = FakeClient([])
    with TestClient(app_for(tmp_path, ai="on", ceiling="1", cap=1, fake=fake), base_url="http://localhost") as client:
        fake.messages.responses.append(model_response(client))
        model = validated(client, client.post(f"{URL}/generate", headers=POST_HEADERS), "cached")
        assert model.generated_by == MODEL_ID
        document = json.loads(cache_path(tmp_path, PAIR_ID).read_text(encoding="utf-8"))
        assert document["cache_key"] == model.input_hash
        assert Brief.model_validate(document["brief"]) == model
        assert validated(client, client.get(URL), "cached") == model
        response = client.post(f"{URL}/generate", headers=POST_HEADERS)
        assert response.status_code == 409
        assert len(fake.messages.calls) == 1


@pytest.mark.parametrize("mode,reason,calls", [
    ("refusal", "refusal", 1), ("max_tokens", "max_tokens", 1),
    ("client_error", "client_error", 2), ("grade_rejected", "grade_rejected", 2),
    ("budget_exhausted", "budget_exhausted", 1),
])
def test_post_failures_return_graded_template_without_cache(
    tmp_path: Path, mode: str, reason: str, calls: int,
) -> None:
    fake = FakeClient([])
    ceiling = "0.24" if mode == "budget_exhausted" else "1"
    with TestClient(app_for(tmp_path, ai="on", ceiling=ceiling, fake=fake), base_url="http://localhost") as client:
        good = model_response(client)
        if mode == "client_error":
            fake.messages.responses[:] = [RuntimeError("SECRET_RESPONSE"), RuntimeError("SECRET_RESPONSE")]
        elif mode == "grade_rejected":
            pair, a, b = case(client)
            bad = make_template_brief(pair, a, b, CONTACTS).model_copy(update={"what": "Invented cost $9,999,999. " + good.parsed_output.what})
            fake.messages.responses[:] = [SimpleNamespace(stop_reason="end_turn", parsed_output=bad)] * 2
        elif mode == "budget_exhausted":
            fake.messages.responses[:] = [RuntimeError("SECRET_RESPONSE")]
        else:
            fake.messages.responses[:] = [SimpleNamespace(stop_reason=mode, parsed_output=good.parsed_output)]
        response = client.post(f"{URL}/generate", headers=POST_HEADERS)
        brief = validated(client, response, "template")
        assert brief.generated_by == "template"
        assert response.headers["x-gridlock-brief-reason"] == reason
        assert len(fake.messages.calls) == calls
        assert not cache_path(tmp_path, PAIR_ID).exists()
        assert "SECRET_RESPONSE" not in response.text


def test_simultaneous_posts_reject_second_without_queuing_spend(tmp_path: Path) -> None:
    entered, release = Event(), Event()

    class BlockingMessages(FakeMessages):
        def parse(self, **kwargs: object) -> object:
            entered.set()
            assert release.wait(5)
            return super().parse(**kwargs)

    fake = FakeClient([])
    fake.messages = BlockingMessages([])
    with TestClient(app_for(tmp_path, ai="on", ceiling="1", fake=fake), base_url="http://localhost") as client:
        fake.messages.responses.append(model_response(client))
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(client.post, f"{URL}/generate", headers=POST_HEADERS)
            assert entered.wait(5)
            second = client.post(f"{URL}/generate", headers=POST_HEADERS)
            assert second.status_code == 409
            assert ErrorResponse.model_validate(second.json()).error.message == "Brief generation busy"
            release.set()
            validated(client, first.result(timeout=5), "cached")
        assert len(fake.messages.calls) == 1
