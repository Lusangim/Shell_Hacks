"""Public artifact and API contracts. Values absent from a plan remain null."""

from __future__ import annotations

from collections import Counter
from enum import Enum
from math import isfinite
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Accuracy(str, Enum):
    exact = "exact"
    approximate = "approximate"
    unknown = "unknown"


class Band(str, Enum):
    touching = "touching"
    lt_1_6km = "lt_1_6km"
    lt_8km = "lt_8km"
    lt_40km = "lt_40km"


class Source(Contract):
    doc: str = Field(min_length=1)
    page: int = Field(gt=0)
    url: str = Field(min_length=1)


Longitude = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
Latitude = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
Position = tuple[Longitude, Latitude]
LinePositions = Annotated[list[Position], Field(min_length=2)]
Count = Annotated[int, Field(ge=0)]


class PointGeometry(Contract):
    type: Literal["Point"]
    coordinates: Position


class LineGeometry(Contract):
    type: Literal["LineString"]
    coordinates: list[Position] = Field(min_length=2)


class MultiLineGeometry(Contract):
    type: Literal["MultiLineString"]
    coordinates: list[LinePositions] = Field(min_length=1)


Geometry = PointGeometry | LineGeometry | MultiLineGeometry


class ProjectProperties(Contract):
    id: str = Field(pattern=r"^(desc-p[1-9][0-9]*|sertp-p[1-9][0-9]*-[0-9a-f]{6}(?:-[2-9][0-9]*)?)$")
    project_id: str | None
    utility: str = Field(min_length=1)
    utility_basis: Literal["stated", "inferred_from_location"]
    name: str = Field(min_length=1)
    description: str | None
    need: str | None
    status: str | None
    in_service: str | None
    year: int | None = Field(ge=1900, le=2200)
    cost_usd: int | None = Field(ge=0)
    cost_basis: Literal["plan", "proxy", "none"]
    cost_flags: list[Literal["printed_total_differs_from_sum", "below_list_threshold"]]
    voltage_kv: list[float] = Field(default_factory=list)
    project_type: Literal["new_line", "rebuild_line", "reconductor", "new_substation", "substation_upgrade", "equipment", "other"]
    miles: float | None = Field(ge=0)
    endpoints: list[str]
    state: Literal["GA", "SC"] | None
    accuracy: Accuracy
    location_source: str | None
    source: Source

    @model_validator(mode="after")
    def cost_consistency(self) -> ProjectProperties:
        if self.cost_basis == "none" and self.cost_usd is not None:
            raise ValueError("cost_basis none requires null cost_usd")
        if self.cost_basis != "none" and self.cost_usd is None:
            raise ValueError("a cost basis requires cost_usd")
        if any(not isfinite(value) or value <= 0 for value in self.voltage_kv):
            raise ValueError("voltages must be positive finite numbers")
        return self


class ProjectFeature(Contract):
    type: Literal["Feature"]
    geometry: Geometry | None
    properties: ProjectProperties

    @model_validator(mode="after")
    def location_consistency(self) -> ProjectFeature:
        if (self.geometry is None) != (self.properties.accuracy == Accuracy.unknown):
            raise ValueError("unknown location must have null geometry, and placed project needs accuracy")
        return self


class ProjectCollection(Contract):
    type: Literal["FeatureCollection"]
    features: list[ProjectFeature]


class Savings(Contract):
    status: Literal["range", "timing_too_far", "no_cost", "unknown_year"]
    low_usd: int | None = Field(ge=0)
    high_usd: int | None = Field(ge=0)
    basis: str | None
    assumption_ids: list[str]

    @model_validator(mode="after")
    def range_consistency(self) -> Savings:
        if self.status == "range":
            if self.low_usd is None or self.high_usd is None or self.low_usd > self.high_usd:
                raise ValueError("range requires ordered bounds")
            if not self.basis or not self.assumption_ids:
                raise ValueError("range requires basis and assumptions")
        elif self.low_usd is not None or self.high_usd is not None:
            raise ValueError("non-range savings have no numeric bounds")
        return self


class Overlap(Contract):
    id: str
    a: str
    b: str
    a_utility: str = Field(min_length=1)
    b_utility: str = Field(min_length=1)
    a_name: str
    b_name: str
    distance_km: float = Field(ge=0, lt=40)
    band: Band
    band_label: str
    touch_reason: Literal["same_substation", "shared_endpoint", "lines_cross", "proximity", "same_area_approximate"]
    touch_detail: str
    can_share: str
    a_year: int | None
    b_year: int | None
    year_gap: int | None = Field(ge=0)
    timeline: str
    cross_state: bool
    pair_note: str | None
    accuracy_pair: Accuracy
    score: float = Field(ge=0)
    rank: int = Field(gt=0)
    savings: Savings
    brief_status: Literal["cached", "stale", "template", "none"]

    @model_validator(mode="after")
    def pair_consistency(self) -> Overlap:
        if self.a >= self.b or self.id != f"{self.a}__{self.b}":
            raise ValueError("pair IDs must be sorted and canonical")
        if self.a_utility == self.b_utility:
            raise ValueError("overlap requires different utilities")
        metres = self.distance_km * 1000
        expected = (
            Band.touching if metres <= 1 else
            Band.lt_1_6km if metres < 1600 else
            Band.lt_8km if metres < 8000 else Band.lt_40km
        )
        if self.band != expected:
            raise ValueError("band does not match distance")
        if self.a_year is not None and self.b_year is not None:
            if self.year_gap != abs(self.a_year - self.b_year):
                raise ValueError("year_gap does not match project years")
        elif self.year_gap is not None:
            raise ValueError("unknown year requires null year_gap")
        return self


class BriefSavings(Contract):
    status: Literal["range", "timing_too_far", "no_cost", "unknown_year"]
    low_usd: int | None = Field(ge=0)
    high_usd: int | None = Field(ge=0)
    basis: str | None

    @model_validator(mode="after")
    def range_consistency(self) -> BriefSavings:
        if self.status == "range":
            if self.low_usd is None or self.high_usd is None or self.low_usd > self.high_usd:
                raise ValueError("range requires ordered bounds")
            if not self.basis or not self.basis.strip():
                raise ValueError("range requires a basis")
        elif self.low_usd is not None or self.high_usd is not None:
            raise ValueError("non-range savings have no numeric bounds")
        return self


class Brief(Contract):
    overlap_id: str
    what: str
    where: str
    when: str
    what_to_share: list[str]
    savings_range: BriefSavings
    who_to_contact: list[str]
    caveats: list[str]
    sources: list[Source]
    generated_by: str
    prompt_version: str
    generated_at: str | None
    input_hash: str


class Center(Contract):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class Area(Contract):
    center: Center
    radius_km: float = Field(ge=1, le=80)
    projects: list[ProjectFeature]
    overlaps: list[Overlap]
    counts_by_utility: dict[str, Count]
    counts_by_band: dict[Band, Count]

    @model_validator(mode="after")
    def count_consistency(self) -> Area:
        if self.counts_by_utility != Counter(project.properties.utility for project in self.projects):
            raise ValueError("utility counts must match projects")
        if self.counts_by_band != Counter(overlap.band for overlap in self.overlaps):
            raise ValueError("band counts must match overlaps")
        return self


class SourceDocument(Contract):
    doc: str
    date: str | None
    url: str


class Meta(Contract):
    build_time: str | None
    source_documents: list[SourceDocument]
    stage_counts: dict[str, Count]
    counts_by_utility: dict[str, Count]
    counts_by_accuracy: dict[str, Count]
    counts_by_band: dict[str, Count]
    no_overlap_count: int = Field(ge=0)
    unmapped_count: int = Field(ge=0)
    unmapped_reasons: dict[str, Count]
    stale_brief_count: int = Field(ge=0)


class SearchResult(Contract):
    type: Literal["place", "project", "substation"]
    label: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    ref: str | None


class ErrorDetail(Contract):
    code: str
    message: str


class ErrorResponse(Contract):
    error: ErrorDetail
