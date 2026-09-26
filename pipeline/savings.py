"""Cautious screening ranges from printed plan costs or explicit team proxies."""

import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


FRACTION_ID = "coordination_fraction_v1"
LINE_RATE_ID = "line_cost_per_mile_v1"
LINE_TYPES = {"new_line", "rebuild_line", "reconductor"}


def _number(value: object) -> Decimal:
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("assumption contains a non-finite number")
    return number


def load_assumptions(path: Path) -> dict[str, dict]:
    """Load the committed, dated rates; reject missing provenance or invalid ranges."""
    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict) or not isinstance(document.get("assumptions"), list):
        raise ValueError("assumptions must be a list")
    by_id = {}
    for row in document["assumptions"]:
        if not isinstance(row, dict) or any(key not in row for key in
                                            ("id", "low", "high", "unit", "precision", "rationale", "source")):
            raise ValueError("assumption missing required fields")
        source = row["source"]
        if (not row["id"] or not row["unit"] or not row["rationale"]
                or not isinstance(source, dict) or source.get("kind") != "team assumption"
                or not source.get("date")):
            raise ValueError("assumption requires an explicit dated team source")
        date.fromisoformat(source["date"])
        if not (Decimal(0) < _number(row["low"]) < _number(row["high"])
                and _number(row["precision"]) > 0):
            raise ValueError(f'assumption {row["id"]} has invalid bounds or precision')
        if row["id"] in by_id:
            raise ValueError(f'duplicate assumption {row["id"]}')
        by_id[row["id"]] = row
    if set(by_id) != {FRACTION_ID, LINE_RATE_ID}:
        raise ValueError("required savings assumptions are missing")
    required_units = {FRACTION_ID: "fraction_of_reference_cost", LINE_RATE_ID: "USD_per_line_mile"}
    for assumption_id, unit in required_units.items():
        if by_id[assumption_id]["unit"] != unit:
            raise ValueError(f"{assumption_id} requires unit {unit}")
    precision = by_id[FRACTION_ID].get("output_precision_usd")
    if not isinstance(precision, int) or precision <= 0:
        raise ValueError("coordination fraction requires positive output_precision_usd")
    return by_id


def _unavailable(status: str, reason: str) -> dict[str, object]:
    return {"status": status, "low_usd": None, "high_usd": None,
            "basis": reason, "assumption_ids": []}


def _round_usd(value: Decimal, precision: int) -> int:
    return int((value / precision).quantize(Decimal(1), rounding=ROUND_HALF_UP) * precision)


def _rate_label(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _range(low: Decimal, high: Decimal, basis: str, ids: list[str], precision: int) -> dict[str, object]:
    low_usd, high_usd = _round_usd(low, precision), _round_usd(high, precision)
    if low_usd <= 0 or high_usd <= low_usd:
        return _unavailable("no_cost", "Positive screening bounds collapse at the stated rounding precision.")
    return {"status": "range", "low_usd": low_usd, "high_usd": high_usd,
            "basis": basis, "assumption_ids": ids}


def estimate_savings(a: dict, b: dict, assumptions: dict[str, dict]) -> dict[str, object]:
    """Return a labelled estimate or a visible reason for null bounds."""
    if a.get("year") is None or b.get("year") is None:
        return _unavailable("unknown_year", "At least one in-service year is not stated; no savings estimate.")
    gap = abs(int(a["year"]) - int(b["year"]))
    if gap > 2:
        return _unavailable("timing_too_far", f"In-service years are {gap} years apart; no savings estimate.")

    fraction = assumptions[FRACTION_ID]
    low_fraction, high_fraction = _number(fraction["low"]), _number(fraction["high"])
    fraction_label = f"{_rate_label(low_fraction * 100)}%-{_rate_label(high_fraction * 100)}%"
    precision = fraction["output_precision_usd"]
    plan = sorted(
        (project for project in (a, b)
         if project.get("cost_basis") == "plan" and project.get("cost_usd") is not None
         and _number(project["cost_usd"]) > 0),
        key=lambda project: (_number(project["cost_usd"]), project["id"]),
    )
    if plan:
        chosen = plan[0]
        cost = _number(chosen["cost_usd"])
        scope = "smaller of two printed plan costs" if len(plan) == 2 else "printed plan cost; partner cost not stated"
        flags = chosen.get("cost_flags") or []
        flag_note = f'; source cost flags: {", ".join(flags)}' if flags else ""
        basis = (f'Estimated coordination saving on {scope} for {chosen["id"]} (${int(cost):,}); '
                 f'team-assumed {fraction_label} of this known scope only; shared savings unverified{flag_note}.')
        return _range(cost * low_fraction, cost * high_fraction, basis, [FRACTION_ID], precision)

    lines = sorted(
        (project for project in (a, b)
         if project.get("project_type") in LINE_TYPES and project.get("miles") is not None
         and _number(project["miles"]) > 0),
        key=lambda project: (_number(project["miles"]), project["id"]),
    )
    if not lines:
        return _unavailable("no_cost", "No printed plan cost or eligible stated line mileage for a proxy estimate.")
    chosen = lines[0]
    miles = _number(chosen["miles"])
    rate = assumptions[LINE_RATE_ID]
    low_rate, high_rate = _number(rate["low"]), _number(rate["high"])
    rate_label = f"${_rate_label(low_rate / 1_000_000)}M-${_rate_label(high_rate / 1_000_000)}M"
    basis = (f'Estimated coordination saving using a team proxy for {chosen["id"]} '
             f'({miles} miles); {rate_label} per line mile and {fraction_label} of proxy cost. '
             'The other project cost and physical shared scope are unverified.')
    return _range(miles * low_rate * low_fraction,
                  miles * high_rate * high_fraction,
                  basis, [FRACTION_ID, LINE_RATE_ID], precision)
