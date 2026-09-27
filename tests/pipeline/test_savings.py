"""Savings by job type and distance, from the team's unit-cost file (founder, 2026-09-26)."""

import csv
import hashlib
import json
from pathlib import Path

import pytest

from pipeline import build_all
from pipeline.savings import (
    BAND_TIERS, JOB_TYPES, MAX_BONUS, OTHER_TYPE, UNIT_COSTS_ID, estimate_savings, job_kind,
    load_unit_costs, partner_fits, savings_bonus, shared_mechanisms,
)
from server.schemas import Savings

ROOT = Path(__file__).resolve().parents[2]
UNIT_COSTS = ROOT / "data/manual/unit_costs_2026.csv"
TEAM_FILE = ROOT / "data/manual/unit_costs_team_2026-09-26.csv"
COLUMNS = ["project_type", "cost_basis", "item", "category", "unit", "unit_price_usd", "price_year", "qty",
           "cost_2026_usd", "shareable", "share_tier", "savings_rate", "saving_per_unit_usd", "rate_basis",
           "sharing_evidence_or_reasoning", "price_source", "price_source_url", "notes"]
# Synthetic file: (job, per, reference cost, [(item, category, tier, saving per unit, evidence?)])
SYNTHETIC = [
    ("new_line", "per mile", 100_000, [("Poles", "Material", "any distance", 10_000, False),
                                       ("Right-of-way", "Land", "< 1.6 km", 100_000, True),
                                       ("Laydown yard", "Site logistics", "< 8 km", 1_000, False),
                                       ("Crew moves", "Mobilization", "< 40 km", 5_000, True),
                                       ("Project management (7% of project)", "Overhead", "touching / co-sited", 500, False)]),
    ("rebuild_line", "per mile", 90_000, [("Poles", "Material", "any distance", 10_000, False),
                                          ("Laydown yard", "Site logistics", "< 8 km", 1_000, False),
                                          ("Crew moves", "Mobilization", "< 40 km", 5_000, True)]),
    ("reconductor", "per mile", 20_000, [("Conductor", "Material", "any distance", 3_000, False),
                                         ("Crew moves", "Mobilization", "< 40 km", 2_000, True)]),
    ("new_substation", "per project", 1_000_000, [("Control enclosure", "Material", "touching / co-sited", 50_000, True),
                                                  ("Substation land", "Land", "< 1.6 km", 20_000, True),
                                                  ("Breakers", "Material", "any distance", 10_000, False),
                                                  ("Crew moves", "Mobilization", "< 40 km", 4_000, True)]),
    ("substation_upgrade", "per project", 200_000, [("Breaker", "Material", "any distance", 6_000, False),
                                                    ("Laydown yard", "Site logistics", "< 8 km", 1_000, False),
                                                    ("Crew moves", "Mobilization", "< 40 km", 4_000, True)]),
    ("equipment", "per project", 500_000, [("Transformer", "Material", "any distance", 30_000, False),
                                           ("Heavy-haul rail", "Logistics", "< 40 km", 8_000, False),
                                           ("Crew moves", "Mobilization", "< 40 km", 4_000, True)]),
]
OTHER_RATES = {"< 40 km": 0.01, "< 8 km": 0.02, "< 1.6 km": 0.05, "touching / co-sited": 0.06}


def _row(**values) -> dict:
    return {column: values.get(column, "") for column in COLUMNS}


@pytest.fixture()
def synthetic(tmp_path: Path):
    rows = []
    for kind, per, reference, items in SYNTHETIC:
        for item, category, tier, saving, evidence in items:
            rows.append(_row(project_type=JOB_TYPES[kind], cost_basis=per, item=item, category=category,
                             cost_2026_usd="1", shareable="Yes", share_tier=tier, savings_rate="0.1",
                             saving_per_unit_usd=str(saving), rate_basis="Evidence+Inference" if evidence else "Inference"))
        for tier in OTHER_RATES:
            rows.append(_row(project_type=JOB_TYPES[kind], cost_basis=per, item="TOTAL", category="Total",
                             cost_2026_usd=str(reference), share_tier=tier, savings_rate="0.1"))
    for tier, rate in OTHER_RATES.items():
        rows.append(_row(project_type=OTHER_TYPE, cost_basis="share of stated budget", item="TOTAL",
                         category="Total", share_tier=tier, savings_rate=str(rate)))
    path = tmp_path / "unit_costs.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return load_unit_costs(path)


def project(pid: str, kind: str, *, year: int | None = 2028, miles: float | None = None,
            cost: int | None = None, name: str = "") -> dict:
    return {"id": pid, "project_type": kind, "year": year, "miles": miles, "cost_usd": cost,
            "cost_basis": "plan" if cost else "none", "name": name, "description": None}


def test_two_new_lines_that_touch_share_land_yard_crews_materials_and_overhead(synthetic) -> None:
    result = estimate_savings(project("a", "new_line", miles=10), project("b", "new_line", miles=10), "touching", synthetic)
    # each: (10,000 + 100,000 + 1,000 + 5,000 + 500) x 10 miles; evidence-backed: land + crews
    assert (result["status"], result["low_usd"], result["high_usd"]) == ("range", 2_100_000, 2_330_000)
    assert result["assumption_ids"] == [UNIT_COSTS_ID]
    assert "two new lines that touch" in result["basis"] and "land and permits" in result["basis"]
    Savings.model_validate(result)


def test_line_and_breaker_job_nearby_share_only_the_yard(synthetic) -> None:
    line = project("a", "new_line", miles=10)
    breaker = project("b", "equipment", name="GORDON 115 KV, BREAKER REPLACEMENT")
    result = estimate_savings(line, breaker, "lt_1_6km", synthetic)
    # no land (the partner needs none), no crews or materials (line versus station work): yards only
    assert (result["low_usd"], result["high_usd"]) == (0, 11_000)
    assert "a laydown yard" in result["basis"] and "land" not in result["basis"]
    far = estimate_savings(line, breaker, "lt_40km", synthetic)
    assert far["status"] == "no_cost" and "share no cost items" in far["basis"]
    Savings.model_validate(far)


def test_two_rebuilds_within_40_km_share_crews_and_bulk_buying(synthetic) -> None:
    result = estimate_savings(project("a", "rebuild_line", miles=5), project("b", "rebuild_line", miles=5), "lt_40km", synthetic)
    assert (result["low_usd"], result["high_usd"]) == (50_000, 150_000)
    assert shared_mechanisms("rebuild_line", "rebuild_line", "lt_40km", synthetic) == [
        "crew and equipment moves", "bulk material buying"]


def test_breaker_and_relay_work_is_sized_as_a_breaker_position_not_a_transformer() -> None:
    assert job_kind(project("a", "equipment", name="MORROW 115 KV, BREAKER REPLACEMENTS")) == "substation_upgrade"
    assert job_kind(project("a", "equipment", name="KLONDIKE, RELAY MODERNIZATION")) == "substation_upgrade"
    assert job_kind(project("a", "equipment", name="HAMMOND, REACTORS INSTALLATION")) == "equipment"
    assert job_kind(project("a", "equipment", name="NORTH DUBLIN 230/115 KV TRANSFORMERS")) == "equipment"


def test_printed_cost_scales_the_reference_and_unsized_partners_add_nothing(synthetic) -> None:
    sized = project("a", "equipment", cost=1_000_000, name="SERIES REACTOR")
    unsized_line = project("b", "rebuild_line")
    result = estimate_savings(sized, unsized_line, "touching", synthetic)
    # equipment items at touching with a line partner: none of materials/heavy-haul/crews fit -> nothing
    assert result["status"] == "no_cost"
    pair = estimate_savings(sized, project("c", "equipment", cost=500_000, name="REACTOR"), "lt_40km", synthetic)
    # (30,000 + 8,000 + 4,000) x 2 for the first, x 1 for the second; evidence-backed: crews only
    assert (pair["low_usd"], pair["high_usd"]) == (12_000, 126_000)
    assert "sized to its printed cost" in pair["basis"]
    one_side = estimate_savings(project("d", "rebuild_line", miles=4), unsized_line, "lt_40km", synthetic)
    assert one_side["high_usd"] == 60_000 and "adds nothing" in one_side["basis"]


def test_unstated_scope_uses_the_average_share_of_a_printed_cost(synthetic) -> None:
    result = estimate_savings(project("a", "other", cost=2_000_000), project("b", "other"), "lt_1_6km", synthetic)
    assert (result["low_usd"], result["high_usd"]) == (0, 100_000)
    none = estimate_savings(project("a", "other"), project("b", "other"), "touching", synthetic)
    assert none["status"] == "no_cost" and "Neither plan" in none["basis"]


@pytest.mark.parametrize(("year_a", "year_b", "expected"),
                         [(2027, 2029, "range"), (2027, 2030, "timing_too_far"), (None, 2029, "unknown_year")])
def test_year_gap_two_is_eligible_three_is_not_and_missing_is_unknown(synthetic, year_a, year_b, expected) -> None:
    result = estimate_savings(project("a", "rebuild_line", year=year_a, miles=5),
                              project("b", "rebuild_line", year=year_b, miles=5), "lt_40km", synthetic)
    assert result["status"] == expected
    if expected != "range":
        assert result["low_usd"] is result["high_usd"] is None and result["assumption_ids"] == []
    Savings.model_validate(result)


def test_partner_fits_follows_the_founder_distance_benefits() -> None:
    assert partner_fits("land", "new_line", "new_line") and partner_fits("land", "new_line", "new_substation")
    assert not partner_fits("land", "new_line", "rebuild_line")
    assert partner_fits("crews", "rebuild_line", "reconductor") and not partner_fits("crews", "rebuild_line", "equipment")
    assert partner_fits("station", "substation_upgrade", "equipment") and not partner_fits("station", "equipment", "new_line")
    assert partner_fits("yard", "new_line", "other") and not partner_fits("materials", "new_line", "other")


def test_savings_bonus_is_log_scaled_and_capped_below_a_band_step() -> None:
    def bonus(high: int) -> float:
        return savings_bonus({"status": "range", "low_usd": 0, "high_usd": high})
    assert bonus(10_000) == 0 and bonus(100_000) == pytest.approx(0.15) and bonus(5_000_000) == MAX_BONUS
    assert bonus(50_000) < bonus(200_000) < bonus(900_000)
    assert savings_bonus({"status": "no_cost", "low_usd": None, "high_usd": None}) == 0
    # all else equal, savings never lift a pair past the next closer band (weights 4/3/2/1)
    assert 3 * (1 + MAX_BONUS) < 4 and 2 * (1 + MAX_BONUS) < 3 and 1 * (1 + MAX_BONUS) < 2


def test_real_unit_cost_file_covers_every_job_type_and_band() -> None:
    costs = load_unit_costs(UNIT_COSTS)
    assert set(costs.jobs) == set(JOB_TYPES) and set(costs.other_rates) == set(BAND_TIERS)
    assert all(job.items and job.reference_cost > 0 for job in costs.jobs.values())
    assert costs.jobs["new_line"].per_mile and not costs.jobs["equipment"].per_mile


def test_adjusted_file_only_re_escalates_miso_prices_at_four_percent() -> None:
    def rows(path: Path) -> list[dict]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    team, adjusted = rows(TEAM_FILE), rows(UNIT_COSTS)
    assert len(team) == len(adjusted)
    for before, after in zip(team, adjusted, strict=True):
        for column in ("project_type", "item", "category", "shareable", "share_tier", "rate_basis", "price_source"):
            assert before[column] == after[column]
        if before["category"] in ("Total", "Scenario", "Overhead"):
            continue
        if before["price_source"].startswith("MISO"):
            expected = float(before["unit_price_usd"]) * float(before["qty"]) * 1.04 ** (2026 - int(before["price_year"]))
            assert after["cost_2026_usd"] == str(round(expected)), before["item"]
            assert before["savings_rate"] == after["savings_rate"]
        else:
            assert (before["cost_2026_usd"], before["saving_per_unit_usd"]) == (after["cost_2026_usd"], after["saving_per_unit_usd"])


def test_real_mcintosh_pair_and_repeat_rebuild_are_contract_valid_and_byte_identical() -> None:
    build_all.build(ROOT)
    path = ROOT / "data/build/overlaps.json"
    first = hashlib.sha256(path.read_bytes()).hexdigest()
    build_all.build(ROOT)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == first
    pairs = json.loads(path.read_text(encoding="utf-8"))
    pair = next(item for item in pairs if item["id"] == "desc-p41__sertp-p107-9bc088")
    assert (pair["savings"]["status"], pair["savings"]["low_usd"], pair["savings"]["high_usd"]) == ("range", 62_000, 264_000)
    assert "sized to its printed cost" in pair["savings"]["basis"]
    assert "sized as one added 230 kV breaker position" in pair["savings"]["basis"]
    assert pair["rank"] == 1 and pair["score"] == pytest.approx(4.8 * (1 + savings_bonus(pair["savings"])), abs=0.001)
    assert all(Savings.model_validate(item["savings"]) for item in pairs)
