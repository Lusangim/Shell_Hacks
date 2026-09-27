"""The synthetic storm estimate is deterministic and honest about coverage."""

from __future__ import annotations

import json
from dataclasses import replace

from fastapi.testclient import TestClient
import pytest
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

from server.app import create_app
from server.export_contracts import exported_schemas
from server.settings import ROOT
from server.storm.data import RawAsset, TO_METRES
from server.storm.engine import WindContext, damage_exceedance, expected_cost, monte_carlo, shifted_wind, wind_speed
from server.storm.schemas import StormEstimate
from server.storm.service import _replacement, estimate


SCENARIO = json.loads((ROOT / "data" / "scenarios" / "gl1_hypothetical.json").read_text(encoding="utf-8"))
PHYSICS = SCENARIO["physics"]


def test_holland_wind_peaks_near_rmax_and_decays() -> None:
    parameters = {"air_density": PHYSICS["air_density_kg_m3"], "holland_b": PHYSICS["holland_b"],
                  "omega": PHYSICS["earth_omega_s"], "surface_factor": PHYSICS["surface_factor"]}
    near = wind_speed(35, 35, 60, 32.05, **parameters)
    assert near > wind_speed(5, 35, 60, 32.05, **parameters)
    assert near > wind_speed(120, 35, 60, 32.05, **parameters)


def test_fragility_is_monotonic() -> None:
    low = damage_exceedance(25, (30, 38, 45, 52), 0.25)
    high = damage_exceedance(50, (30, 38, 45, 52), 0.25)
    assert all(a < b for a, b in zip(low, high))
    assert all(high[i] >= high[i + 1] for i in range(3))


def test_line_and_substation_expected_cost_by_hand() -> None:
    probabilities = (0.8, 0.5, 0.3, 0.1)
    # Exact-state probabilities: 0.3, 0.2, 0.2, 0.1.
    assert expected_cost(probabilities, 1_000_000, (0.02, 0.10, 0.40, 1.0)) == pytest.approx(206_000)
    assert expected_cost(probabilities, 2_000_000, (0.02, 0.10, 0.40, 1.0)) == pytest.approx(412_000)


def test_same_seed_gives_same_quantiles() -> None:
    context = WindContext(20, 10, 35, 60, 32, 5, PHYSICS)
    assets = [(42.0, (30, 38, 45, 52), 0.25, 1_000_000.0, None, context)]
    options = {"seed": 42, "draws": 1000, "dp_multiplier": (0.9, 1.1),
               "cross_track_offset_km": (-25, 25), "median_multiplier": (0.85, 1.15),
               "ratios": (0.02, 0.10, 0.40, 1.0)}
    assert monte_carlo(assets, **options) == monte_carlo(assets, **options)


def test_signed_cross_track_shift_changes_wind_in_both_directions() -> None:
    context = WindContext(50, 0, 35, 60, 32, 0, PHYSICS)
    baseline = shifted_wind(context, 1, 0)
    assert shifted_wind(context, 1, 15) > baseline
    assert shifted_wind(context, 1, -15) < baseline


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app(artifact_dir=ROOT / "data" / "build"), base_url="http://localhost") as result:
        yield result


def test_line_and_station_use_sourced_reference_jobs(client: TestClient) -> None:
    data = client.app.state.storm_data
    x, y = TO_METRES(-81.16, 32.18)
    line = LineString([(x, y), (x + 1609.344, y)])
    station = Point(x, y)
    line_raw = RawAsset("line", "line_wood", "Test line", "HIFLD", line)
    station_raw = RawAsset("station", "substation", "Test station", "OSM", station)
    line_replacement, line_evidence = _replacement(line_raw, line, data)
    station_replacement, station_evidence = _replacement(station_raw, station, data)
    assert line_evidence == "cost:unit_costs_2026:rebuild_line"
    assert station_evidence == "cost:unit_costs_2026:new_substation"
    assert line_replacement == pytest.approx(data.costs.jobs["rebuild_line"].reference_cost)
    assert station_replacement == pytest.approx(data.costs.jobs["new_substation"].reference_cost)
    probabilities = (0.8, 0.5, 0.3, 0.1)
    manual_ratio = 0.3 * 0.02 + 0.2 * 0.10 + 0.2 * 0.40 + 0.1 * 1.0
    assert expected_cost(probabilities, line_replacement, SCENARIO["repair_ratios"]) == pytest.approx(line_replacement * manual_ratio)
    assert expected_cost(probabilities, station_replacement, SCENARIO["repair_ratios"]) == pytest.approx(station_replacement * manual_ratio)


def test_bad_parameters_return_422(client: TestClient) -> None:
    base = {"scenario": "gl1", "lat": 32.18, "lon": -81.16, "radius_km": 20}
    for change in ({"radius_km": 0}, {"radius_km": 81}, {"lat": "nan"}, {"lon": 190}, {"scenario": "unknown"}):
        response = client.get("/api/storm/estimate", params={**base, **change})
        assert response.status_code == 422


def test_scenarios_and_mcintosh_contract(client: TestClient) -> None:
    choices = client.get("/api/storm/scenarios")
    assert choices.status_code == 200
    assert choices.json()[0]["id"] == "gl1"
    response = client.get("/api/storm/estimate", params={"scenario": "gl1", "lat": 32.18, "lon": -81.16, "radius_km": 20})
    assert response.status_code == 200, response.text
    value = StormEstimate.model_validate(response.json())
    committed_schema = json.loads((ROOT / "contracts" / "storm-estimate.schema.json").read_text(encoding="utf-8"))
    assert committed_schema == exported_schemas()["storm-estimate"]
    assert value.scenario.mode == "hypothetical"
    assert len(value.scenario.frames) == 13
    assert value.summary.assets_total > 0
    assert value.summary.p10_usd <= value.summary.p50_usd <= value.summary.p90_usd
    assert value.summary.assets_with_cost <= value.summary.assets_total
    assert len(value.assets) <= 200
    assert value.decision.provider == "system-rule-v1"


def test_empty_area_requests_human_review(client: TestClient) -> None:
    response = client.get("/api/storm/estimate", params={"scenario": "gl1", "lat": 0, "lon": 0, "radius_km": 1})
    assert response.status_code == 200
    value = StormEstimate.model_validate(response.json())
    assert value.summary.assets_total == 0
    assert value.decision.action == "human_review"


def test_missing_cost_is_null_and_reduces_coverage(client: TestClient) -> None:
    x, y = TO_METRES(-81.16, 32.18)
    raw = (RawAsset("line-without-cost", "line_wood", "Test line", "HIFLD transmission lines (archived)",
                    LineString([(x, y), (x + 500, y)])),
           RawAsset("station-with-cost", "substation", "Test station", "OpenStreetMap substations", Point(x, y)))
    original = client.app.state.storm_data
    costs = replace(original.costs, jobs={key: value for key, value in original.costs.jobs.items() if key != "rebuild_line"})
    data = replace(original, assets=raw, tree=STRtree([item.geometry for item in raw]), costs=costs)
    value = estimate(data, client.app.state.artifacts.projects.model_copy(update={"features": []}),
                     lat=32.18, lon=-81.16, radius_km=1)
    assert value.summary.assets_total == 2
    assert value.summary.assets_with_cost == 1
    assert value.summary.coverage_share == 0.5
    assert value.decision.action == "human_review"
    missing = next(asset for asset in value.assets if asset.id.startswith("line-without-cost"))
    assert missing.replacement_usd is None
    assert missing.expected_usd is None
