"""Read-only brief lookup and an explicitly guarded local generation route."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from threading import Lock

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.responses import Response

from server.brief_cache import cache_key, cache_path, load_cached_brief
from server.brief_generator import MODEL_ID, PROMPT_VERSION, Budget, ParsedClient, generate_brief
from server.brief_template import make_template_brief
from server.schemas import Brief, ErrorResponse, Overlap, ProjectCollection, ProjectFeature
from server.settings import ROOT, Settings
from tests.eval.grader import grade_brief, load_contacts


BRIEF_STATUS = "X-GridLock-Brief-Status"
BRIEF_REASON = "X-GridLock-Brief-Reason"


@dataclass(frozen=True)
class BriefCase:
    pair: Overlap
    project_a: ProjectFeature
    project_b: ProjectFeature


def get_brief_client() -> ParsedClient | None:
    """The product has no real SDK client until founder-approved F6 verification."""
    return None


def _error(status: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse.model_validate({"error": {"code": code, "message": message}})
    return JSONResponse(status_code=status, content=body.model_dump())


def _case(request: Request, overlap_id: str) -> BriefCase | None:
    artifacts = request.app.state.artifacts
    pair = next((item for item in artifacts.overlaps if item.id == overlap_id), None)
    if pair is None:
        return None
    projects = {item.properties.id: item for item in artifacts.projects.features}
    return BriefCase(pair, projects[pair.a], projects[pair.b])


def _cache_state(cache_dir: Path, case: BriefCase, contacts: frozenset[str]) -> tuple[str, Brief | None]:
    pair, a, b = case.pair, case.project_a, case.project_b
    expected = cache_key(pair, a, b, contacts, PROMPT_VERSION, MODEL_ID)
    cached = load_cached_brief(
        cache_dir, pair.id, expected, model_id=MODEL_ID, prompt_version=PROMPT_VERSION,
    )
    if cached is not None and grade_brief(cached, pair, a, b, contacts).ok:
        return "cached", cached
    # A well-formed prior model entry with a different input key is stale. A
    # broken, incomplete, or ungraded current entry is simply a template miss.
    try:
        document = json.loads(cache_path(cache_dir, pair.id).read_text(encoding="utf-8"))
        old_key = document["cache_key"]
        old_brief = Brief.model_validate(document["brief"])
    except (OSError, UnicodeError, ValueError, RecursionError, KeyError, TypeError, ValidationError):
        return "template", None
    if (
        old_key != expected and old_brief.input_hash == old_key
        and old_brief.overlap_id == pair.id and old_brief.generated_by == MODEL_ID
        and old_brief.prompt_version == PROMPT_VERSION
    ):
        return "stale", None
    return "template", None


def _same_origin(request: Request) -> bool:
    host = request.headers.get("host", "")
    origin = request.headers.get("origin", "")
    # The outer app middleware already restricts Host to loopback. Compare the
    # complete origin, so a path, userinfo, subdomain, or alternate port fails.
    return origin.casefold() == f"http://{host}".casefold()


def _brief_response(brief: Brief, status: str, reason: str | None = None) -> Response:
    headers = {BRIEF_STATUS: status}
    if reason is not None:
        headers[BRIEF_REASON] = reason
    return JSONResponse(content=brief.model_dump(mode="json"), headers=headers)


def stale_brief_count(
    cache_dir: Path, overlaps: tuple[Overlap, ...], projects: ProjectCollection,
    contacts: frozenset[str],
) -> int:
    """Count only well-formed prior entries whose structured input key changed."""
    by_id = {item.properties.id: item for item in projects.features}
    return sum(
        _cache_state(cache_dir, BriefCase(pair, by_id[pair.a], by_id[pair.b]), contacts)[0] == "stale"
        for pair in overlaps
    )


def register_brief_routes(app: FastAPI, config: Settings) -> None:
    """Install brief routes with state scoped to this one local server run."""
    app.state.brief_contacts = load_contacts(ROOT / "data" / "manual" / "contacts.json")
    app.state.brief_budget = (
        Budget(config.spend_ceiling_usd) if config.spend_ceiling_usd > Decimal("0") else None
    )
    app.state.brief_lock = Lock()
    app.state.ondemand_count = 0

    @app.get("/api/briefs/{overlap_id:path}", response_model=Brief, responses={404: {"model": ErrorResponse}})
    def get_brief(request: Request, overlap_id: str) -> Brief | Response:
        case = _case(request, overlap_id)
        if case is None:
            return _error(404, "not_found", "Brief overlap not found")
        contacts = request.app.state.brief_contacts
        status, cached = _cache_state(config.brief_cache_dir, case, contacts)
        brief = cached or make_template_brief(case.pair, case.project_a, case.project_b, contacts)
        return _brief_response(brief, status)

    @app.post(
        "/api/briefs/{overlap_id:path}/generate", response_model=Brief,
        responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    def post_brief(
        request: Request, overlap_id: str,
        client: ParsedClient | None = Depends(get_brief_client),
    ) -> Brief | Response:
        case = _case(request, overlap_id)
        if case is None:
            return _error(404, "not_found", "Brief overlap not found")
        if request.headers.get("x-gridlock") != "1" or not _same_origin(request):
            return _error(403, "forbidden", "Brief generation request forbidden")
        budget: Budget | None = request.app.state.brief_budget
        if config.ai != "on" or budget is None or client is None:
            return _error(409, "unavailable", "Brief generation unavailable")
        lock: Lock = request.app.state.brief_lock
        if not lock.acquire(blocking=False):
            return _error(409, "busy", "Brief generation busy")
        try:
            if request.app.state.ondemand_count >= config.max_ondemand:
                return _error(409, "unavailable", "Brief generation unavailable")
            if budget.spent_usd + budget.reservation_usd > budget.ceiling_usd:
                return _error(409, "unavailable", "Brief generation unavailable")
            result = generate_brief(
                case.pair, case.project_a, case.project_b,
                request.app.state.brief_contacts, client=client, access=True,
                budget=budget, cache_dir=config.brief_cache_dir,
            )
            if result.calls:
                request.app.state.ondemand_count += 1
            status = "cached" if result.origin in {"cache", "model"} else "template"
            return _brief_response(result.brief, status, result.reason)
        finally:
            lock.release()
