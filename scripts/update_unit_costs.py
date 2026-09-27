"""Rebuild data/manual/unit_costs_2026.csv from the team's unit-cost file with newer escalation.

Input:  data/manual/unit_costs_team_2026-09-26.csv (the founder's file, kept verbatim)
Output: data/manual/unit_costs_2026.csv (what the pipeline reads)

One change, from a newer public source: MISO's Transmission Cost Estimation Guide for MTEP26 (Planning
Subcommittee, March 11, 2026) escalates most costs 4% a year, and circuit breakers, disconnect switches
and power transformers by more. The team file escalated its 2024 MISO prices at about 2.5% a year. This
script re-escalates rows priced from the MISO guide at 4% a year to 2026 (a floor for the breaker,
switch and transformer rows), leaves every other row's cost as the team wrote it, and recomputes what
depends on those costs: the 3% engineering and 7% project-management rows (now on direct cost without
the optional spare, which the file's totals already exclude), each item's saving, and the TOTAL rows.
Savings rates, tiers, evidence labels and sources are unchanged.

Run: python scripts/update_unit_costs.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "manual" / "unit_costs_team_2026-09-26.csv"
TARGET = ROOT / "data" / "manual" / "unit_costs_2026.csv"
MISO_ESCALATION = 0.04
TEAM_ESCALATION = 0.025
YEAR = 2026
BANDS = ("< 40 km", "< 8 km", "< 1.6 km", "touching / co-sited")
TIERS_AT = {
    "< 40 km": {"any distance", "< 40 km"},
    "< 8 km": {"any distance", "< 40 km", "< 8 km"},
    "< 1.6 km": {"any distance", "< 40 km", "< 8 km", "< 1.6 km"},
    "touching / co-sited": {"any distance", "< 40 km", "< 8 km", "< 1.6 km", "touching / co-sited"},
}
LINE_TYPES = ("New line 230 kV", "Rebuild line 230 kV", "Reconductor 230 kV")


def _is_miso(row: dict) -> bool:
    return row["price_source"].startswith("MISO Transmission Cost Estimation Guide")


def _optional(row: dict) -> bool:
    return "(optional" in row["item"]


def _overhead_share(row: dict) -> float | None:
    if row["category"] != "Overhead":
        return None
    if "(3% of project)" in row["item"]:
        return 0.03
    if "(7% of project)" in row["item"]:
        return 0.07
    raise ValueError(f"unrecognised overhead row: {row['item']}")


def main() -> None:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    assert fields is not None

    items = [row for row in rows if row["category"] not in ("Total", "Scenario")]
    for row in items:
        if row["category"] == "Overhead" or not _is_miso(row):
            continue
        cost = float(row["unit_price_usd"]) * float(row["qty"]) * (1 + MISO_ESCALATION) ** (YEAR - int(row["price_year"]))
        row["cost_2026_usd"] = str(round(cost))
        row["saving_per_unit_usd"] = str(round(cost * float(row["savings_rate"])))

    totals: dict[str, float] = {}
    for job in dict.fromkeys(row["project_type"] for row in items):
        job_rows = [row for row in items if row["project_type"] == job]
        direct = sum(float(row["cost_2026_usd"]) for row in job_rows
                     if row["category"] != "Overhead" and not _optional(row))
        for row in job_rows:
            share = _overhead_share(row)
            if share is not None:
                cost = direct * share
                row["unit_price_usd"] = f"{cost:.2f}"
                row["cost_2026_usd"] = str(round(cost))
                row["saving_per_unit_usd"] = str(round(cost * float(row["savings_rate"])))
        totals[job] = direct + sum(float(row["cost_2026_usd"]) for row in job_rows if row["category"] == "Overhead")

    rates: dict[tuple[str, str], float] = {}
    for row in rows:
        job = row["project_type"]
        if row["category"] == "Scenario" and _is_miso(row):
            factor = ((1 + MISO_ESCALATION) / (1 + TEAM_ESCALATION)) ** (YEAR - int(row["price_year"]))
            row["cost_2026_usd"] = str(round(float(row["cost_2026_usd"]) * factor))
            row["saving_per_unit_usd"] = str(round(float(row["saving_per_unit_usd"]) * factor))
        elif row["category"] == "Total" and job in totals:
            tier = row["share_tier"]
            saving = sum(float(item["saving_per_unit_usd"]) for item in items
                         if item["project_type"] == job and item["shareable"] == "Yes"
                         and not _optional(item) and item["share_tier"] in TIERS_AT[tier])
            row["cost_2026_usd"] = str(round(totals[job]))
            row["savings_rate"] = f"{saving / totals[job]:.4f}"
            row["saving_per_unit_usd"] = str(round(saving))
            rates[(job, tier)] = saving / totals[job]
    for row in rows:
        if row["category"] == "Total" and row["project_type"].startswith("Other"):
            average = sum(rates[(job, row["share_tier"])] for job in LINE_TYPES) / len(LINE_TYPES)
            row["savings_rate"] = f"{average:.4f}"

    with TARGET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {TARGET.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
