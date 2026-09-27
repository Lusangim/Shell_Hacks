"""Strict API boundary for the synthetic storm estimate."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Frame(StrictModel):
    index: int = Field(ge=0)
    t_hours: int
    lat: float
    lon: float
    dp_hpa: float = Field(gt=0)
    rmax_km: float = Field(gt=0)


class SyntheticFrame(Frame):
    radius_33_ms_km: float = Field(ge=0)


class ScenarioInfo(StrictModel):
    id: Literal["gl1", "synthetic"]
    name: str
    mode: Literal["hypothetical"]
    version: str
    label: str
    frames: list[Frame | SyntheticFrame]


class ScenarioChoice(StrictModel):
    id: Literal["gl1", "synthetic"]
    name: str
    mode: Literal["hypothetical"]
    version: str
    label: str


class StormArea(StrictModel):
    lat: float
    lon: float
    radius_km: float = Field(ge=1, le=80)


class PointGeometry(StrictModel):
    type: Literal["Point"]
    coordinates: tuple[float, float]


class LineGeometry(StrictModel):
    type: Literal["LineString"]
    coordinates: list[tuple[float, float]]


class Damage(StrictModel):
    minor: float = Field(ge=0, le=1)
    moderate: float = Field(ge=0, le=1)
    severe: float = Field(ge=0, le=1)
    failed: float = Field(ge=0, le=1)


class StormAsset(StrictModel):
    id: str
    asset_class: Literal["line_wood", "line_steel", "substation"] = Field(alias="class")
    name: str
    accuracy: Literal["exact", "approximate"]
    source: str
    geometry: PointGeometry | LineGeometry
    peak_wind_ms: float = Field(ge=0)
    peak_wind_mph: float = Field(ge=0)
    peak_frame: int = Field(ge=0)
    damage: Damage
    replacement_usd: float | None = Field(ge=0, default=None)
    expected_usd: float | None = Field(ge=0, default=None)
    evidence: list[str]


class StormSummary(StrictModel):
    assets_total: int = Field(ge=0)
    assets_exact: int = Field(ge=0)
    assets_with_cost: int = Field(ge=0)
    coverage_share: float = Field(ge=0, le=1)
    p10_usd: int = Field(ge=0)
    p50_usd: int = Field(ge=0)
    p90_usd: int = Field(ge=0)
    mean_usd: int = Field(ge=0)
    draws: int = Field(gt=0)
    seed: int
    method_version: Literal["storm-v1"]
    top_assumptions: list[str] = Field(min_length=3, max_length=3)


class DecisionReason(StrictModel):
    text: str
    evidence: list[str]


class StormDecision(StrictModel):
    action: Literal["human_review", "coordinate_project_timing", "inspect_asset", "preposition_crews", "verify_source"]
    provider: Literal["system-rule-v1"]
    confidence: float = Field(ge=0, le=1)
    reasons: list[DecisionReason] = Field(min_length=1)
    review_required: bool
    review_reason: str | None


class StormEstimate(StrictModel):
    scenario: ScenarioInfo
    area: StormArea
    assets: list[StormAsset]
    summary: StormSummary
    decision: StormDecision
