"""Hand-computed screening savings, explicit assumptions, and build stability."""

import hashlib
import json
from pathlib import Path

import pytest

from pipeline import build_all
from pipeline.savings import estimate_savings, load_assumptions
from server.schemas import Savings


ROOT = Path(__file__).resolve().parents[2]
ASSUMPTIONS = ROOT / "data/manual/assumptions.json"


def project(project_id: str, *, year: int | None = 2028, cost: int | None = None,
            cost_basis: str = "none", miles: float | None = None,
            kind: str = "equipment", flags: list[str] | None = None) -> dict:
    return {"id": project_id, "year": year, "cost_usd": cost, "cost_basis": cost_basis,
            "miles": miles, "project_type": kind, "cost_flags": flags or []}


@pytest.fixture(scope="module")
def assumptions() -> dict:
    return load_assumptions(ASSUMPTIONS)


def test_assumptions_are_explicit_team_rates_with_declared_precision(assumptions: dict) -> None:
    assert set(assumptions) == {"coordination_fraction_v1", "line_cost_per_mile_v1"}
    fraction = assumptions["coordination_fraction_v1"]
    line = assumptions["line_cost_per_mile_v1"]
    assert (fraction["low"], fraction["high"], fraction["unit"]) == (0.01, 0.03, "fraction_of_reference_cost")
    assert fraction["precision"] == 0.01
    assert fraction["output_precision_usd"] == 1000
    assert (line["low"], line["high"], line["unit"], line["precision"]) == (
        1_000_000, 3_000_000, "USD_per_line_mile", 1_000_000,
    )
    for assumption in assumptions.values():
        assert assumption["rationale"]
        assert assumption["source"] == {"kind": "team assumption", "date": "2026-09-26"}


def test_real_mcintosh_pair_uses_only_printed_desc_plan_cost(assumptions: dict) -> None:
    features = json.loads((ROOT / "data/build/projects.geojson").read_text(encoding="utf-8"))["features"]
    by_id = {feature["properties"]["id"]: feature["properties"] for feature in features}
    desc, sertp = by_id["desc-p41"], by_id["sertp-p107-9bc088"]
    assert desc["cost_usd"] == 5_376_418 and desc["cost_basis"] == "plan"
    assert sertp["cost_usd"] is None and sertp["cost_basis"] == "none"
    result = estimate_savings(desc, sertp, assumptions)
    assert Savings.model_validate(result).status == "range"
    assert (result["low_usd"], result["high_usd"]) == (54_000, 161_000)
    assert result["assumption_ids"] == ["coordination_fraction_v1"]
    assert "plan" in result["basis"] and "desc-p41" in result["basis"]
    assert "partner cost not stated" in result["basis"]


def test_proxy_line_mileage_has_two_assumptions_and_wide_bounds(assumptions: dict) -> None:
    a = project("a", miles=2.5, kind="rebuild_line")
    b = project("b")
    result = estimate_savings(a, b, assumptions)
    assert (result["status"], result["low_usd"], result["high_usd"]) == ("range", 25_000, 225_000)
    assert result["assumption_ids"] == ["coordination_fraction_v1", "line_cost_per_mile_v1"]
    assert "proxy" in result["basis"] and "2.5 miles" in result["basis"]
    assert "unverified" in result["basis"]
    Savings.model_validate(result)


def test_plan_cost_takes_priority_and_flags_remain_visible(assumptions: dict) -> None:
    flags = ["printed_total_differs_from_sum", "below_list_threshold"]
    a = project("plan", cost=2_000_000, cost_basis="plan", flags=flags)
    b = project("line", miles=2.5, kind="new_line")
    result = estimate_savings(a, b, assumptions)
    assert (result["low_usd"], result["high_usd"]) == (20_000, 60_000)
    assert result["assumption_ids"] == ["coordination_fraction_v1"]
    assert "plan" in result["basis"] and all(flag in result["basis"] for flag in flags)
    assert a["cost_usd"] == 2_000_000 and a["cost_flags"] == flags


@pytest.mark.parametrize(
    ("year_a", "year_b", "expected"),
    [(2027, 2029, "range"), (2027, 2030, "timing_too_far"), (None, 2029, "unknown_year")],
)
def test_year_gap_two_is_eligible_three_is_not_and_missing_is_unknown(
    assumptions: dict, year_a: int | None, year_b: int, expected: str,
) -> None:
    result = estimate_savings(project("a", year=year_a, cost=2_000_000, cost_basis="plan"),
                              project("b", year=year_b), assumptions)
    assert result["status"] == expected
    if expected == "range":
        assert (result["low_usd"], result["high_usd"]) == (20_000, 60_000)
    else:
        assert result["low_usd"] is result["high_usd"] is None
        assert result["basis"] and result["assumption_ids"] == []
    Savings.model_validate(result)


def test_no_cost_without_plan_or_eligible_line_mileage(assumptions: dict) -> None:
    result = estimate_savings(project("a", miles=2.5, kind="equipment"), project("b"), assumptions)
    assert result["status"] == "no_cost"
    assert result["low_usd"] is result["high_usd"] is None
    assert result["basis"] and result["assumption_ids"] == []
    Savings.model_validate(result)


def test_round_half_up_at_declared_thousand_and_never_publish_collapsed_range(assumptions: dict) -> None:
    rounded = estimate_savings(project("a", cost=1_050_000, cost_basis="plan"), project("b"), assumptions)
    assert (rounded["low_usd"], rounded["high_usd"]) == (11_000, 32_000)
    assert rounded["low_usd"] < rounded["high_usd"]
    too_small = estimate_savings(project("a", cost=10_000, cost_basis="plan"), project("b"), assumptions)
    assert too_small["status"] == "no_cost"
    assert too_small["low_usd"] is too_small["high_usd"] is None


def test_built_pair_and_repeat_rebuild_are_contract_valid_and_byte_identical(assumptions: dict) -> None:
    build_all.build(ROOT)
    path = ROOT / "data/build/overlaps.json"
    first = hashlib.sha256(path.read_bytes()).hexdigest()
    build_all.build(ROOT)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == first
    pairs = json.loads(path.read_text(encoding="utf-8"))
    pair = next(item for item in pairs if item["id"] == "desc-p41__sertp-p107-9bc088")
    assert pair["savings"]["status"] == "range"
    assert (pair["savings"]["low_usd"], pair["savings"]["high_usd"]) == (54_000, 161_000)
    assert pair["score"] == 4.8 and pair["rank"] == 1
    assert all(Savings.model_validate(item["savings"]) for item in pairs)
