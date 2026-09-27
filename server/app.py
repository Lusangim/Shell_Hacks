"""Local read-only API over validated, prebuilt public-plan artifacts."""

from __future__ import annotations

import csv
import io
import json
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, AsyncIterator, Awaitable, Callable, Literal, TypeVar

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter, ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from pipeline.savings import UNIT_COSTS_ID, UNIT_COSTS_LABEL
from server.area import build_area
from server.brief_routes import register_brief_routes, stale_brief_count
from server.map_assets import GOOGLE_CSP, OFFLINE_CSP, MapConfig, archive_response, map_error, offline_available, same_origin
from server.schemas import Area, Band, ErrorResponse, LineGeometry, Meta, MultiLineGeometry, Overlap, PointGeometry, ProjectCollection, ProjectFeature, Savings, SearchResult, Source
from server.settings import ROOT, Settings


SOURCE_PDFS = MappingProxyType({
    "desc-scrtp-2026-2030": ROOT / "data" / "raw" / "desc_scrtp_2026_2030.pdf",
    "sertp-2025-rtp": ROOT / "data" / "raw" / "sertp_2025_rtp.pdf",
})
# What a planner reads first comes first; the evidence and reference columns follow. Codes appear as words.
CSV_COLUMNS = (
    "Rank", "Score", "Project A", "Utility A", "In-service year A", "Project B", "Utility B",
    "In-service year B", "Year gap", "Years to coordinate", "Distance km", "Band", "Touch reason",
    "Why they touch", "Accuracy A", "Accuracy B", "Savings low USD", "Savings high USD", "Savings status",
    "Savings basis", "Source A", "Source page A", "Source B", "Source page B", "Coordination status", "Notes",
    "Overlap ID", "Savings assumptions", "Savings caveat",
)
CSV_TOUCH_REASONS = MappingProxyType({
    "same_substation": "Same named substation", "shared_endpoint": "Shared named endpoint",
    "lines_cross": "Mapped lines cross", "proximity": "Nearby mapped locations",
    "same_area_approximate": "Same approximate area",
})
CSV_SAVINGS_STATUS = MappingProxyType({
    "range": "Screening estimate",
    "timing_too_far": "No estimate: in-service years more than 2 apart",
    "no_cost": "No estimate: no size, or nothing both jobs need at this distance",
    "unknown_year": "No estimate: an in-service year is not stated",
})
CSV_CAVEAT = "Shared work and savings are not verified; confirm scope, costs, and schedules with the utilities."


class Health(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: Literal["ok"]


class Basemap(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    type: Literal["FeatureCollection"]
    features: list[dict[str, JsonValue]]


class Place(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(min_length=1)
    state: Literal["GA", "SC"]
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)


class OverlapDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    overlap: Overlap
    project_a: ProjectFeature
    project_b: ProjectFeature
    savings: Savings
    sources: tuple[Source, Source]


@dataclass(frozen=True)
class Artifacts:
    projects: ProjectCollection
    overlaps: tuple[Overlap, ...]
    meta: Meta
    basemap: Basemap
    search_entries: tuple[SearchResult, ...]


ModelT = TypeVar("ModelT", bound=BaseModel)


def _read_json(path: Path) -> object:
    try:
        with path.open("r", encoding="utf-8") as source:
            return json.load(source)
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Cannot load required GridLock artifact {path}: {exc}") from exc


def _load_model(path: Path, model: type[ModelT]) -> ModelT:
    try:
        return model.model_validate(_read_json(path))
    except ValidationError as exc:
        raise RuntimeError(f"Invalid GridLock artifact {path}: {exc}") from exc


def _load_places(path: Path, *, required: bool) -> tuple[Place, ...]:
    if not required and not path.exists():
        return ()
    try:
        return tuple(TypeAdapter(list[Place]).validate_python(_read_json(path)))
    except ValidationError as exc:
        raise RuntimeError(f"Invalid GridLock artifact {path}: {exc}") from exc


def _project_anchor(project: ProjectFeature) -> tuple[float, float] | None:
    geometry = project.geometry
    if isinstance(geometry, PointGeometry | LineGeometry):
        return geometry.coordinates if isinstance(geometry, PointGeometry) else geometry.coordinates[0]
    if isinstance(geometry, MultiLineGeometry):
        return next((part[0] for part in geometry.coordinates if part), None)
    return None


def _search_entries(projects: ProjectCollection, places: tuple[Place, ...]) -> tuple[SearchResult, ...]:
    entries = [SearchResult(type="place", label=place.name, lat=place.lat, lon=place.lon, ref=None) for place in places]
    seen_stations: set[tuple[str, float, float]] = set()
    for project in projects.features:
        anchor = _project_anchor(project)
        if anchor is None:
            continue
        lon, lat = anchor
        props = project.properties
        entries.append(SearchResult(type="project", label=props.name, lat=lat, lon=lon, ref=props.id))
        if not isinstance(project.geometry, PointGeometry) or len(props.endpoints) != 1:
            continue
        endpoint = props.endpoints[0]
        location_source = props.location_source or ""
        if endpoint.casefold() not in location_source.casefold():
            continue
        if "substation" not in location_source.casefold() and "substation" not in props.name.casefold():
            continue
        key = (endpoint.casefold(), lat, lon)
        if key not in seen_stations:
            entries.append(SearchResult(type="substation", label=endpoint, lat=lat, lon=lon, ref=props.id))
            seen_stations.add(key)
    return tuple(entries)


def _match_rank(label: str, query: str) -> int | None:
    folded = label.casefold()
    if folded.startswith(query):
        return 0
    if any(word.startswith(query) for word in re.findall(r"\w+", folded)):
        return 1
    return None


def search_entries(entries: tuple[SearchResult, ...], query: str) -> list[SearchResult]:
    term = query.strip().casefold()
    if len(term) < 2:
        raise HTTPException(status_code=422, detail="q must contain at least two characters")
    priorities = {"place": 0, "substation": 1, "project": 2}
    matches = ((rank, item) for item in entries if (rank := _match_rank(item.label, term)) is not None)
    ordered = sorted(matches, key=lambda row: (row[0], priorities[row[1].type], row[1].label.casefold(), row[1].ref or ""))
    return [item for _, item in ordered[:10]]


def load_artifacts(directory: Path, *, fixture_dir: bool = False) -> Artifacts:
    """Validate the full API boundary once; never disguise a legacy artifact."""
    project_name = "projects.json" if fixture_dir and not (directory / "projects.geojson").exists() else "projects.geojson"
    try:
        projects = _load_model(directory / project_name, ProjectCollection)
        try:
            overlaps = tuple(Overlap.model_validate(item) for item in _require_list(_read_json(directory / "overlaps.json")))
        except (ValidationError, TypeError) as exc:
            raise RuntimeError(f"Invalid GridLock artifact {directory / 'overlaps.json'}: {exc}") from exc
        meta = _load_model(directory / "meta.json", Meta)
        basemap = _load_model(directory / "basemap.json", Basemap)
        places = _load_places(directory / "places.json", required=not fixture_dir)
        project_ids = {project.properties.id for project in projects.features}
        if len(project_ids) != len(projects.features):
            raise ValueError("duplicate project IDs")
        if any(pair.a not in project_ids or pair.b not in project_ids for pair in overlaps):
            raise ValueError("overlap references an absent project")
        if len({pair.id for pair in overlaps}) != len(overlaps):
            raise ValueError("duplicate overlap IDs")
    except (ValidationError, ValueError, TypeError) as exc:
        raise RuntimeError(f"Invalid GridLock artifacts in {directory}: {exc}") from exc
    return Artifacts(projects=projects, overlaps=overlaps, meta=meta, basemap=basemap, search_entries=_search_entries(projects, places))


def _require_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise TypeError("overlaps.json must be a JSON array")
    return value


def _error(status: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse.model_validate({"error": {"code": code, "message": message}})
    return JSONResponse(status_code=status, content=body.model_dump())


def _matches_project(
    project: ProjectFeature,
    utilities: list[str] | None,
    voltage_kv: float | None,
    year: int | None,
    year_min: int | None,
    year_max: int | None,
    project_type: str | None,
) -> bool:
    props = project.properties
    return (
        (not utilities or props.utility in utilities)
        and (voltage_kv is None or voltage_kv in props.voltage_kv)
        and (year is None or props.year == year)
        and (year_min is None or (props.year is not None and props.year >= year_min))
        and (year_max is None or (props.year is not None and props.year <= year_max))
        and (project_type is None or props.project_type == project_type)
    )


def filter_overlaps(
    artifacts: Artifacts,
    *,
    utility: list[str] | None = None,
    voltage_kv: float | None = None,
    year: int | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    project_type: str | None = None,
    band: Band | None = None,
    cross_state: bool | None = None,
) -> list[Overlap]:
    """Apply the same project and pair filters for list and export."""
    if year_min is not None and year_max is not None and year_min > year_max:
        raise HTTPException(status_code=422, detail="year_min must be <= year_max")
    eligible = {
        project.properties.id
        for project in artifacts.projects.features
        if _matches_project(project, utility, voltage_kv, year, year_min, year_max, project_type)
    }
    matched = (
        pair for pair in artifacts.overlaps
        if pair.a in eligible and pair.b in eligible
        and (band is None or pair.band == band)
        and (cross_state is None or pair.cross_state == cross_state)
    )
    return sorted(matched, key=lambda pair: (pair.rank, pair.distance_km, pair.id))


def _csv_text(value: str) -> str:
    return f"'{value}" if value and value[0] in "=+-@\t\r\n" else value


def _csv_assumption_labels() -> dict[str, str]:
    """Present the savings basis and its provenance without exposing assumption IDs."""
    return {UNIT_COSTS_ID: UNIT_COSTS_LABEL}


def _csv_utility(project: ProjectFeature) -> str:
    props = project.properties
    suffix = " (inferred)" if props.utility_basis == "inferred_from_location" else ""
    return _csv_text(props.utility + suffix)


def _csv_accuracy(project: ProjectFeature) -> str:
    props = project.properties
    return props.accuracy.value + (" (town only)" if props.town_only else "")


def years_to_coordinate(pair: Overlap, this_year: int) -> int | None:
    """Whole years from this year to the earlier in-service year; 0 means coordinate now."""
    if pair.a_year is None or pair.b_year is None:
        return None
    return max(0, min(pair.a_year, pair.b_year) - this_year)


def _csv_row(
    pair: Overlap, projects: dict[str, ProjectFeature], assumption_labels: dict[str, str], this_year: int,
) -> tuple[str | int | float | None, ...]:
    a = projects[pair.a].properties
    b = projects[pair.b].properties
    savings = pair.savings
    assumptions = " ".join(
        assumption_labels.get(assumption_id, "Assumption details unavailable; verify before using this estimate.")
        for assumption_id in savings.assumption_ids
    )
    return (
        pair.rank, pair.score, _csv_text(a.name), _csv_utility(projects[pair.a]), a.year,
        _csv_text(b.name), _csv_utility(projects[pair.b]), b.year, pair.year_gap,
        years_to_coordinate(pair, this_year), pair.distance_km, _csv_text(pair.band_label),
        CSV_TOUCH_REASONS[pair.touch_reason], _csv_text(pair.touch_detail),
        _csv_accuracy(projects[pair.a]), _csv_accuracy(projects[pair.b]), savings.low_usd, savings.high_usd,
        CSV_SAVINGS_STATUS[savings.status], _csv_text(savings.basis),
        _csv_text(a.source.doc), a.source.page, _csv_text(b.source.doc), b.source.page, "", "",
        _csv_text(pair.id), _csv_text(assumptions), CSV_CAVEAT,
    )


def export_csv(pairs: list[Overlap], projects: ProjectCollection) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    by_id = {project.properties.id: project for project in projects.features}
    assumption_labels = _csv_assumption_labels()
    this_year = date.today().year
    for pair in pairs:
        writer.writerow(_csv_row(pair, by_id, assumption_labels, this_year))
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def create_app(artifact_dir: Path | None = None, settings: Settings | None = None) -> FastAPI:
    """Create a loopback-only application with configurable validated artifacts."""
    config = settings or Settings.from_env()
    google_key = config.google_key if config.google == "on" else None
    directory = Path(artifact_dir) if artifact_dir is not None else config.artifact_dir
    explicit_dir = artifact_dir is not None or directory != ROOT / "data" / "build"
    fixture_dir = explicit_dir and (directory / "projects.json").exists() and not (directory / "projects.geojson").exists()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.artifacts = load_artifacts(directory, fixture_dir=fixture_dir)
        yield

    app = FastAPI(lifespan=lifespan)

    @app.middleware("http")
    async def local_security(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        host = request.headers.get("host", "")
        if not re.fullmatch(r"(?:127\.0\.0\.1|localhost)(?::[0-9]{1,5})?", host, re.IGNORECASE):
            response = _error(400, "invalid_host", "Use 127.0.0.1 or localhost")
        elif request.url.path == "/api/map-config" and not same_origin(request):
            response = map_error(403, "invalid_origin", "Same-origin request required")
        else:
            response = await call_next(request)
        response.headers["Content-Security-Policy"] = GOOGLE_CSP if google_key else OFFLINE_CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if google_key and (request.url.path == "/api/map-config" or response.headers.get("content-type", "").startswith("text/html")):
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.path == "/api/map-config":
            response.headers["Cache-Control"] = "no-store"
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return response

    @app.exception_handler(RequestValidationError)
    async def bad_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error(422, "invalid_request", "Invalid request parameters")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "invalid_request" if exc.status_code == 422 else "http_error"
        return _error(exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return _error(500, "internal_error", "Internal server error")

    @app.get("/api/health", response_model=Health, responses={400: {"model": ErrorResponse}})
    def health() -> Health:
        return Health(status="ok")

    @app.get("/api/map-config", response_model=MapConfig, responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
    def map_config() -> MapConfig:
        return MapConfig(google_enabled=google_key is not None, google_key=google_key, offline_available=offline_available(config.basemap_pmtiles))

    @app.get("/basemap/gasc.pmtiles", response_class=Response, response_model=None, responses={206: {"description": "Single byte range"}, 404: {"model": ErrorResponse}, 416: {"model": ErrorResponse}})
    def basemap_archive(request: Request) -> Response:
        ranges = request.headers.getlist("range")
        return archive_response(config.basemap_pmtiles, ",".join(ranges) if ranges else None)

    @app.get("/api/meta", response_model=Meta, responses={400: {"model": ErrorResponse}})
    def meta(request: Request) -> Meta:
        artifacts: Artifacts = request.app.state.artifacts
        count = stale_brief_count(
            config.brief_cache_dir, artifacts.overlaps, artifacts.projects,
            request.app.state.brief_contacts,
        )
        return artifacts.meta.model_copy(update={"stale_brief_count": count})

    @app.get("/api/basemap", response_model=Basemap, responses={400: {"model": ErrorResponse}})
    def basemap(request: Request) -> Basemap:
        return request.app.state.artifacts.basemap

    @app.get("/api/search", response_model=list[SearchResult], responses={422: {"model": ErrorResponse}})
    def search(request: Request, q: str) -> list[SearchResult]:
        return search_entries(request.app.state.artifacts.search_entries, q)

    @app.get("/api/area", response_model=Area, responses={422: {"model": ErrorResponse}})
    def area(
        request: Request,
        lat: Annotated[float, Query(ge=-90, le=90, allow_inf_nan=False)],
        lon: Annotated[float, Query(ge=-180, le=180, allow_inf_nan=False)],
        radius_km: Annotated[float, Query(ge=1, le=80, allow_inf_nan=False)] = 40.0,
    ) -> Area:
        artifacts: Artifacts = request.app.state.artifacts
        return build_area(artifacts.projects, artifacts.overlaps, lat=lat, lon=lon, radius_km=radius_km)

    @app.get("/api/projects", response_model=ProjectCollection, responses={422: {"model": ErrorResponse}})
    def projects(
        request: Request,
        utility: Annotated[list[str] | None, Query()] = None,
        voltage_kv: Annotated[float | None, Query(gt=0)] = None,
        year: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        year_min: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        year_max: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        project_type: Literal["new_line", "rebuild_line", "reconductor", "new_substation", "substation_upgrade", "equipment", "other"] | None = None,
    ) -> ProjectCollection:
        if year_min is not None and year_max is not None and year_min > year_max:
            raise HTTPException(status_code=422, detail="year_min must be <= year_max")
        matched = [project for project in request.app.state.artifacts.projects.features if _matches_project(project, utility, voltage_kv, year, year_min, year_max, project_type)]
        return ProjectCollection(type="FeatureCollection", features=matched)

    @app.get("/api/projects/{project_id}", response_model=ProjectFeature, responses={404: {"model": ErrorResponse}})
    def project_detail(request: Request, project_id: str) -> ProjectFeature:
        for project in request.app.state.artifacts.projects.features:
            if project.properties.id == project_id:
                return project
        raise HTTPException(status_code=404, detail="Project not found")

    @app.get("/api/overlaps", response_model=list[Overlap], responses={422: {"model": ErrorResponse}})
    def overlaps(
        request: Request,
        utility: Annotated[list[str] | None, Query()] = None,
        voltage_kv: Annotated[float | None, Query(gt=0)] = None,
        year: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        year_min: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        year_max: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        project_type: Literal["new_line", "rebuild_line", "reconductor", "new_substation", "substation_upgrade", "equipment", "other"] | None = None,
        band: Band | None = None,
        cross_state: bool | None = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 500,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> list[Overlap]:
        pairs = filter_overlaps(
            request.app.state.artifacts, utility=utility, voltage_kv=voltage_kv, year=year,
            year_min=year_min, year_max=year_max, project_type=project_type,
            band=band, cross_state=cross_state,
        )
        return pairs[offset:offset + limit]

    @app.get("/api/overlaps/{overlap_id}", response_model=OverlapDetail, responses={404: {"model": ErrorResponse}})
    def overlap_detail(request: Request, overlap_id: str) -> OverlapDetail:
        artifacts: Artifacts = request.app.state.artifacts
        pair = next((item for item in artifacts.overlaps if item.id == overlap_id), None)
        if pair is None:
            raise HTTPException(status_code=404, detail="Overlap not found")
        projects_by_id = {item.properties.id: item for item in artifacts.projects.features}
        a = projects_by_id[pair.a]
        b = projects_by_id[pair.b]
        return OverlapDetail(
            overlap=pair, project_a=a, project_b=b, savings=pair.savings,
            sources=(a.properties.source, b.properties.source),
        )

    @app.get("/api/export/overlaps.csv", response_class=Response, response_model=None, responses={422: {"model": ErrorResponse}})
    def overlap_export(
        request: Request,
        utility: Annotated[list[str] | None, Query()] = None,
        voltage_kv: Annotated[float | None, Query(gt=0)] = None,
        year: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        year_min: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        year_max: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        project_type: Literal["new_line", "rebuild_line", "reconductor", "new_substation", "substation_upgrade", "equipment", "other"] | None = None,
        band: Band | None = None,
        cross_state: bool | None = None,
    ) -> Response:
        artifacts: Artifacts = request.app.state.artifacts
        pairs = filter_overlaps(
            artifacts, utility=utility, voltage_kv=voltage_kv, year=year,
            year_min=year_min, year_max=year_max, project_type=project_type,
            band=band, cross_state=cross_state,
        )
        return Response(
            content=export_csv(pairs, artifacts.projects), media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="gridlock-overlaps.csv"'},
        )

    @app.get("/api/sources/{doc_id}", response_class=FileResponse, response_model=None, responses={404: {"model": ErrorResponse}})
    def source_pdf(doc_id: str) -> FileResponse:
        path = SOURCE_PDFS.get(doc_id)
        if path is None or not path.is_file():
            raise HTTPException(status_code=404, detail="Source document not found")
        return FileResponse(path, media_type="application/pdf", filename=path.name, content_disposition_type="inline")

    @app.get("/", response_class=FileResponse, response_model=None)
    def index() -> FileResponse:
        page = ROOT / "web" / "index.html"
        if not page.is_file():
            raise HTTPException(status_code=404, detail="Web shell not available")
        return FileResponse(page, media_type="text/html")

    register_brief_routes(app, config)
    app.mount("/web", StaticFiles(directory=ROOT / "web"), name="web")
    return app
