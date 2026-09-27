"""Select mapped assets and assemble the deterministic GL-1 API response."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from shapely.geometry import LineString, MultiLineString, Point, shape
from shapely.ops import substring, transform

from server.schemas import ProjectCollection
from server.storm.data import RawAsset, StormData, TO_DEGREES, TO_METRES
from server.storm.engine import WindContext, damage_exceedance, expected_cost, monte_carlo, wind_speed
from server.storm.schemas import (
    Damage, DecisionReason, Frame, LineGeometry, PointGeometry, ScenarioChoice,
    ScenarioInfo, StormArea, StormAsset, StormDecision, StormEstimate, StormSummary, SyntheticFrame,
)


DIRECTION_VECTOR = {"N": (0, 1), "NE": (1, 1), "E": (1, 0), "SE": (1, -1),
                    "S": (0, -1), "SW": (-1, -1), "W": (-1, 0), "NW": (-1, 1)}
STRENGTH = {1: (25, 40), 2: (40, 38), 3: (55, 35), 4: (70, 32)}


def synthetic_scenario(base: dict, *, lat: float, lon: float, direction: str, category: int) -> dict:
    """Project a straight hypothetical track through the selected centre."""
    x, y = TO_METRES(lon, lat)
    east, north = DIRECTION_VECTOR[direction]
    length = math.hypot(east, north)
    east, north = east / length, north / length
    pressure, rmax = STRENGTH[category]
    anchors = []
    for hour, distance, pressure_share in ((-18, -350, .4), (-17, -340, .4 + .6 * 10 / 180),
                                           (-8.5, -170, 1), (0, 0, 1), (3.5, 70, 1),
                                           (12, 240, .6 + .4 * 10 / 180), (13, 250, .6)):
        point_lon, point_lat = TO_DEGREES(x - east * distance * 1000, y - north * distance * 1000)
        anchors.append({"t_hours": hour, "lat": point_lat, "lon": point_lon,
                        "dp_hpa": pressure * pressure_share, "rmax_km": rmax})
    return {**base, "id": "synthetic", "name": f"Category {category} from {direction}",
            "version": "1", "label": "Hypothetical storm: not a forecast, not observed damage",
            "anchors": anchors}


def _radius_33(frame: Frame, physics: dict) -> float:
    radii = np.linspace(0.1, 300, 601)
    speeds = wind_speed(radii, frame.rmax_km, frame.dp_hpa, frame.lat,
                        air_density=physics["air_density_kg_m3"], holland_b=physics["holland_b"],
                        omega=physics["earth_omega_s"], surface_factor=physics["surface_factor"])
    reached = radii[np.asarray(speeds) >= 33]
    return round(float(reached[-1]), 2) if len(reached) else 0.0


def scenario_frames(scenario: dict, step_hours: int = 6) -> list[Frame]:
    anchors = scenario["anchors"]
    times = list(range(anchors[0]["t_hours"], anchors[-1]["t_hours"] + 1, step_hours))
    frames: list[Frame] = []
    for index, hour in enumerate(times):
        before, after = next((a, b) for a, b in zip(anchors, anchors[1:]) if a["t_hours"] <= hour <= b["t_hours"])
        fraction = (hour - before["t_hours"]) / (after["t_hours"] - before["t_hours"])
        frames.append(Frame(index=index, t_hours=hour, **{
            key: before[key] + fraction * (after[key] - before[key]) for key in ("lat", "lon", "dp_hpa", "rmax_km")
        }))
    return frames


def _fragments(geometry: LineString | MultiLineString) -> Iterable[LineString]:
    for part in (geometry.geoms if isinstance(geometry, MultiLineString) else (geometry,)):
        if part.length == 0:
            continue
        for index in range(max(1, math.ceil(part.length / 1000))):
            section = substring(part, index * 1000, min((index + 1) * 1000, part.length))
            if isinstance(section, LineString) and section.length > 0:
                yield section


def _selected(data: StormData, circle: object) -> list[tuple[RawAsset, LineString | Point, str]]:
    selected: list[tuple[RawAsset, LineString | Point, str]] = []
    for index in data.tree.query(circle, predicate="intersects"):
        raw = data.assets[int(index)]
        if isinstance(raw.geometry, Point):
            selected.append((raw, raw.geometry, raw.id))
            continue
        clipped = raw.geometry.intersection(circle)
        for ordinal, section in enumerate(_fragments(clipped) if isinstance(clipped, LineString | MultiLineString) else ()):
            selected.append((raw, section, f"{raw.id}-{ordinal}"))
    return selected


def _hourly_track(frames: list[Frame]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    six = np.asarray([frame.t_hours for frame in frames])
    hourly = np.arange(six[0], six[-1] + 1)
    lat = np.interp(hourly, six, [frame.lat for frame in frames])
    lon = np.interp(hourly, six, [frame.lon for frame in frames])
    pressure = np.interp(hourly, six, [frame.dp_hpa for frame in frames])
    rmax = np.interp(hourly, six, [frame.rmax_km for frame in frames])
    x, y = TO_METRES(lon, lat)
    x, y = np.asarray(x), np.asarray(y)
    vx = np.gradient(x, 3600)
    vy = np.gradient(y, 3600)
    return hourly, lat, x, y, pressure, rmax, np.stack((vx, vy))


def _wind_at(x: float, y: float, track: tuple, physics: dict) -> tuple[float, int, int]:
    hourly, latitudes, xs, ys, pressures, rmaxes, velocity = track
    dx, dy = x - xs, y - ys
    distance_m = np.hypot(dx, dy)
    speeds = np.asarray(wind_speed(distance_m / 1000, rmaxes, pressures, latitudes,
                                  air_density=physics["air_density_kg_m3"], holland_b=physics["holland_b"],
                                  omega=physics["earth_omega_s"], surface_factor=physics["surface_factor"]))
    forward = np.hypot(velocity[0], velocity[1])
    # Right of travel is the clockwise normal of the forward velocity.
    cosine = (velocity[1] * dx - velocity[0] * dy) / np.maximum(forward * distance_m, 1)
    speeds = np.maximum(0, speeds + physics["forward_speed_factor"] * forward * cosine)
    index = int(np.argmax(speeds))
    return float(speeds[index]), int(round((hourly[index] - hourly[0]) / 6)), index


def _wind_context(x: float, y: float, track: tuple, physics: dict, hour_index: int) -> WindContext:
    _, latitudes, xs, ys, pressures, rmaxes, velocity = track
    vx, vy = velocity[:, hour_index]
    forward = math.hypot(vx, vy)
    dx, dy = x - xs[hour_index], y - ys[hour_index]
    along = (dx * vx + dy * vy) / max(forward, 0.001) / 1000
    cross = (dx * vy - dy * vx) / max(forward, 0.001) / 1000
    return WindContext(cross, along, float(rmaxes[hour_index]), float(pressures[hour_index]),
                       float(latitudes[hour_index]), forward, physics)


def _geometry(geometry: LineString | Point) -> LineGeometry | PointGeometry:
    simplified = geometry.simplify(50, preserve_topology=True)
    if isinstance(simplified, Point):
        lon, lat = TO_DEGREES(simplified.x, simplified.y)
        return PointGeometry(type="Point", coordinates=(lon, lat))
    return LineGeometry(type="LineString", coordinates=[TO_DEGREES(x, y) for x, y in simplified.coords])


def _replacement(raw: RawAsset, geometry: LineString | Point, data: StormData) -> tuple[float | None, str]:
    kind = "new_substation" if raw.asset_class == "substation" else "rebuild_line"
    job = data.costs.jobs.get(kind)
    evidence = f"cost:unit_costs_2026:{kind}"
    if job is None or job.reference_cost <= 0:
        return None, evidence
    if isinstance(geometry, LineString):
        return geometry.length / 1609.344 * job.reference_cost, evidence
    return job.reference_cost, evidence


def _project_in_swath(projects: ProjectCollection, circle: object, track: tuple, physics: dict) -> tuple[str, str] | None:
    for project in projects.features:
        if project.geometry is None:
            continue
        mapped = transform(TO_METRES, shape(project.geometry.model_dump(mode="json")))
        if not mapped.intersects(circle):
            continue
        inside = mapped.intersection(circle)
        points: list[Point]
        if isinstance(inside, Point):
            points = [inside]
        elif isinstance(inside, LineString | MultiLineString):
            points = [part.interpolate(distance) for part in (inside.geoms if isinstance(inside, MultiLineString) else (inside,))
                      for distance in np.linspace(0, part.length, max(2, math.ceil(part.length / 1000) + 1))]
        else:
            continue
        if any(_wind_at(point.x, point.y, track, physics)[0] >= 33 for point in points):
            return project.properties.id, project.properties.name
    return None


def estimate(data: StormData, projects: ProjectCollection, *, lat: float, lon: float, radius_km: float,
             direction: str | None = None, category: int | None = None) -> StormEstimate:
    from shapely.geometry import Point as ShapelyPoint

    synthetic = direction is not None and category is not None
    scenario = synthetic_scenario(data.scenario, lat=lat, lon=lon, direction=direction, category=category) if synthetic else data.scenario
    frames = scenario_frames(scenario, step_hours=1 if synthetic else 6)
    if synthetic:
        frames = [SyntheticFrame(**frame.model_dump(), radius_33_ms_km=_radius_33(frame, scenario["physics"])) for frame in frames]
    circle = ShapelyPoint(*TO_METRES(lon, lat)).buffer(radius_km * 1000)
    track = _hourly_track(frames)
    physics = scenario["physics"]
    assets: list[StormAsset] = []
    simulations = []
    scenario_id = "synthetic-v1" if synthetic else "gl1-v1"
    for raw, geometry, asset_id in _selected(data, circle):
        point = geometry if isinstance(geometry, Point) else geometry.interpolate(0.5, normalized=True)
        peak, frame_index, hour_index = _wind_at(point.x, point.y, track, physics)
        if synthetic:
            frame_index = hour_index
        fragility = scenario["fragility"][raw.asset_class]
        probabilities = damage_exceedance(peak, fragility["medians_ms"], fragility["beta"])
        replacement, cost_id = _replacement(raw, geometry, data)
        expected = expected_cost(probabilities, replacement, scenario["repair_ratios"])
        evidence = [f"asset:{asset_id}", f"frame:{frame_index}", f"fragility:gl1-v1:{raw.asset_class}", cost_id]
        assets.append(StormAsset(id=asset_id, **{"class": raw.asset_class}, name=raw.name, accuracy="exact",
                                 source=raw.source, geometry=_geometry(geometry), peak_wind_ms=round(peak, 2), peak_wind_mph=round(peak * 2.2369362921, 1),
                                 peak_frame=frame_index, damage=Damage(**dict(zip(("minor", "moderate", "severe", "failed"), probabilities))),
                                 replacement_usd=round(replacement, 2) if replacement is not None else None,
                                 expected_usd=round(expected, 2) if expected is not None else None, evidence=evidence))
        simulations.append((peak, fragility["medians_ms"], fragility["beta"], replacement, None,
                            _wind_context(point.x, point.y, track, physics, hour_index)))
    covered = [asset for asset in assets if asset.expected_usd is not None]
    coverage = len(covered) / len(assets) if assets else 0.0
    expected_total = sum(asset.expected_usd or 0 for asset in assets)
    confidence = sum(asset.expected_usd or 0 for asset in assets if asset.accuracy == "exact" and asset.expected_usd is not None) / expected_total if expected_total else 0.0
    mc = scenario["monte_carlo"]
    p10, p50, p90, mean = monte_carlo(simulations, draws=mc["draws"], seed=mc["seed"],
                                     dp_multiplier=tuple(mc["dp_multiplier"]), cross_track_offset_km=tuple(mc["cross_track_offset_km"]),
                                     median_multiplier=tuple(mc["fragility_median_multiplier"]), ratios=scenario["repair_ratios"])
    summary = StormSummary(assets_total=len(assets), assets_exact=len(assets), assets_with_cost=len(covered),
                           coverage_share=coverage, p10_usd=p10, p50_usd=p50, p90_usd=p90, mean_usd=mean,
                           draws=mc["draws"], seed=mc["seed"], method_version="storm-v1",
                           top_assumptions=scenario["top_assumptions"])
    reasons: list[DecisionReason] = []
    if not assets or coverage < 0.6:
        action = "human_review"
        reasons.append(DecisionReason(text="No mapped assets or insufficient sourced cost coverage in this area.", evidence=[f"scenario:{scenario_id}", "cost:unit_costs_2026:coverage"]))
    elif match := _project_in_swath(projects, circle, track, physics):
        action = "coordinate_project_timing"
        reasons.append(DecisionReason(text=f"Planned project {match[1]} intersects this area and the 33 m/s synthetic wind swath.", evidence=[f"project:{match[0]}", f"scenario:{scenario_id}", "frame:swath-33ms"]))
    elif severe := next((asset for asset in sorted(assets, key=lambda item: item.damage.severe, reverse=True) if asset.accuracy == "exact" and asset.damage.severe > 0.3), None):
        action = "inspect_asset"
        reasons.append(DecisionReason(text=f"Mapped asset {severe.name} has illustrative severe-or-failed damage chance above 30%.", evidence=severe.evidence))
    elif sum(asset.peak_wind_ms >= 33 for asset in assets) >= 10:
        action = "preposition_crews"
        reasons.append(DecisionReason(text="At least 10 mapped assets exceed 33 m/s in this synthetic scenario.", evidence=[asset.evidence[0] for asset in assets if asset.peak_wind_ms >= 33][:10] + [f"scenario:{scenario_id}"]))
    else:
        action = "verify_source"
        reasons.append(DecisionReason(text="Confirm source locations and unit costs before operational use.", evidence=[f"scenario:{scenario_id}", "cost:unit_costs_2026:rebuild_line"]))
    review = confidence < 0.7
    decision = StormDecision(action=action, provider="system-rule-v1", confidence=round(confidence, 4),
                             reasons=reasons, review_required=review,
                             review_reason="Exact mapped assets with sourced costs account for less than 70% of expected cost." if review else None)
    ranked = sorted(assets, key=lambda asset: (asset.expected_usd is None, -(asset.expected_usd or 0), asset.id))[:200]
    info = ScenarioInfo(id=scenario["id"], name=scenario["name"], mode=scenario["mode"], version=scenario["version"], label=scenario["label"], frames=frames)
    return StormEstimate(scenario=info, area=StormArea(lat=lat, lon=lon, radius_km=radius_km), assets=ranked, summary=summary, decision=decision)
