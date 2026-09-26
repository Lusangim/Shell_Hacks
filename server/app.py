"""Local read-only API over validated, prebuilt public-plan artifacts."""

from __future__ import annotations

import json
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, AsyncIterator, Awaitable, Callable, Literal, TypeVar

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter, ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from server.schemas import Band, ErrorResponse, LineGeometry, Meta, MultiLineGeometry, Overlap, PointGeometry, ProjectCollection, ProjectFeature, SearchResult
from server.settings import ROOT, Settings


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


def create_app(artifact_dir: Path | None = None, settings: Settings | None = None) -> FastAPI:
    """Create a loopback-only application with configurable validated artifacts."""
    config = settings or Settings.from_env()
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
        else:
            response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
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

    @app.get("/api/meta", response_model=Meta, responses={400: {"model": ErrorResponse}})
    def meta(request: Request) -> Meta:
        return request.app.state.artifacts.meta

    @app.get("/api/basemap", response_model=Basemap, responses={400: {"model": ErrorResponse}})
    def basemap(request: Request) -> Basemap:
        return request.app.state.artifacts.basemap

    @app.get("/api/search", response_model=list[SearchResult], responses={422: {"model": ErrorResponse}})
    def search(request: Request, q: str) -> list[SearchResult]:
        return search_entries(request.app.state.artifacts.search_entries, q)

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
        if year_min is not None and year_max is not None and year_min > year_max:
            raise HTTPException(status_code=422, detail="year_min must be <= year_max")
        eligible = {project.properties.id for project in request.app.state.artifacts.projects.features if _matches_project(project, utility, voltage_kv, year, year_min, year_max, project_type)}
        matched = [pair for pair in request.app.state.artifacts.overlaps if pair.a in eligible and pair.b in eligible and (band is None or pair.band == band) and (cross_state is None or pair.cross_state == cross_state)]
        return sorted(matched, key=lambda pair: (pair.rank, pair.distance_km, pair.id))[offset:offset + limit]

    @app.get("/", response_class=FileResponse, response_model=None)
    def index() -> FileResponse:
        page = ROOT / "web" / "index.html"
        if not page.is_file():
            raise HTTPException(status_code=404, detail="Web shell not available")
        return FileResponse(page, media_type="text/html")

    app.mount("/web", StaticFiles(directory=ROOT / "web"), name="web")
    return app
