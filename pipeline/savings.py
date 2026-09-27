"""Screening savings by job type and distance, from the team's unit-cost file.

`data/manual/unit_costs_2026.csv` lists, for each 230 kV job type, the items a project pays for, which of
them two nearby projects could share, from what distance, and the team's saving rate for each. The
founder's distance benefits set the tiers: touching means coordinating outages and crossings (plus joint
engineering and shared station facilities), under 1.6 km means sharing land, access roads and permits,
under 8 km means sharing laydown yards and deliveries, and under 40 km means sharing crews and equipment.
Bulk material buying works at any distance.

For a pair, each project saves on its own items that are shareable at the pair's band AND that the
partner's job type also needs: two line jobs can share line crews, a line job and a relay upgrade cannot;
only a new line or a new substation needs new land. The low end counts items whose rate rests on public
precedent (Evidence, Evidence+Inference); the high end counts every shareable item. Estimates are direct
costs before contingency and financing, and they are screening estimates, not measured savings.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

UNIT_COSTS_ID = "unit_costs_2026"
UNIT_COSTS_LABEL = (
    "Team unit-cost file (2026-09-26): shareable cost items by job type and distance, priced from "
    "MISO's transmission cost guide (escalated to 2026 at 4% a year) and public land, wage and rental "
    "sources. Saving rates are team assumptions, not measured savings."
)
PRECISION_USD = 1000
MAX_YEAR_GAP = 2
MAX_BONUS = 0.3        # below 1/3, so savings alone never lift a pair past a closer band
BONUS_FLOOR_USD = 10_000
BONUS_FULL_USD = 1_000_000

BAND_TIERS = {
    "touching": frozenset({"any distance", "< 40 km", "< 8 km", "< 1.6 km", "touching / co-sited"}),
    "lt_1_6km": frozenset({"any distance", "< 40 km", "< 8 km", "< 1.6 km"}),
    "lt_8km": frozenset({"any distance", "< 40 km", "< 8 km"}),
    "lt_40km": frozenset({"any distance", "< 40 km"}),
}
BAND_WORDS = {"touching": "touching", "lt_1_6km": "under 1.6 km apart",
              "lt_8km": "under 8 km apart", "lt_40km": "under 40 km apart"}
JOB_TYPES = {
    "new_line": "New line 230 kV",
    "rebuild_line": "Rebuild line 230 kV",
    "reconductor": "Reconductor 230 kV",
    "new_substation": "New substation 230 kV (4-position ring bus)",
    "substation_upgrade": "Substation upgrade 230 kV (add 1 ring-bus position)",
    "equipment": "Equipment (300 MVA 230/115 kV transformer + 50 MVAr reactor)",
}
OTHER_TYPE = "Other (no scope known)"
JOB_WORDS = {"new_line": "new line", "rebuild_line": "line rebuild", "reconductor": "reconductoring job",
             "new_substation": "new substation", "substation_upgrade": "substation upgrade",
             "equipment": "equipment job", "other": "project of unstated scope"}
REFERENCE_WORDS = {"new_substation": "sized as a new 4-position 230 kV substation",
                   "substation_upgrade": "sized as one added 230 kV breaker position",
                   "equipment": "sized as a 300 MVA transformer and reactor job"}
# Most "equipment" jobs in the plans are breaker, relay or switch work, far smaller than the file's
# transformer-and-reactor reference; they are sized as its one-breaker-position substation upgrade.
LARGE_EQUIPMENT = re.compile(r"transformer|reactor|capacitor|statcom|\bsvc\b", re.IGNORECASE)
LINE_FAMILY = frozenset({"new_line", "rebuild_line", "reconductor"})
STATION_FAMILY = frozenset({"new_substation", "substation_upgrade", "equipment"})
EVIDENCE = frozenset({"Evidence", "Evidence+Inference"})
MECHANISM_WORDS = {
    "land": "land and permits",
    "corridor": "clearing, access roads and mats",
    "station": "a control house and station site",
    "yard": "a laydown yard",
    "heavy_haul": "heavy-haul deliveries",
    "crews": "crew and equipment moves",
    "materials": "bulk material buying",
    "overhead": "joint engineering and project management",
}
REQUIRED_COLUMNS = {"project_type", "cost_basis", "item", "category", "cost_2026_usd", "shareable",
                    "share_tier", "savings_rate", "saving_per_unit_usd", "rate_basis"}


@dataclass(frozen=True)
class Item:
    mechanism: str
    tier: str
    saving: float
    evidence: bool


@dataclass(frozen=True)
class Job:
    per_mile: bool
    reference_cost: float
    items: tuple[Item, ...]


@dataclass(frozen=True)
class UnitCosts:
    jobs: dict[str, Job]
    other_rates: dict[str, float] = field(default_factory=dict)


def _family(kind: str | None) -> str:
    return "line" if kind in LINE_FAMILY else "station" if kind in STATION_FAMILY else "other"


def partner_fits(mechanism: str, own: str, partner: str | None) -> bool:
    """Whether the partner's job type also needs what this item shares."""
    if mechanism in ("yard", "overhead"):
        return True
    if mechanism in ("materials", "crews"):
        return _family(own) == _family(partner) != "other"
    if mechanism == "land":
        return partner in ("new_line", "new_substation")
    if mechanism == "corridor":
        return partner in LINE_FAMILY or partner == "new_substation"
    if mechanism == "heavy_haul":
        return partner in ("equipment", "new_substation")
    if mechanism == "station":
        return partner in STATION_FAMILY
    raise ValueError(f"unknown sharing mechanism {mechanism}")


def _mechanism(row: dict[str, str]) -> str:
    category, item, tier = row["category"], row["item"].lower(), row["share_tier"]
    if category == "Material":
        return "materials" if tier == "any distance" else "station"
    if category in ("Land", "Permitting"):
        return "land"
    if category == "Site prep":
        return "station" if item.startswith("site work") else "corridor"
    if category == "Site logistics":
        return "yard" if "laydown" in item else "corridor"
    if category == "Engineering":
        return "corridor"
    if category == "Mobilization":
        return "crews"
    if category == "Logistics":
        return "heavy_haul"
    if category == "Overhead":
        return "overhead"
    if category == "Labor & equipment" and tier == "touching / co-sited":
        return "station"
    raise ValueError(f"shareable row has no sharing mechanism: {row['item']}")


def _positive(value: str, what: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{what} must be a finite non-negative number")
    return number


def load_unit_costs(path: Path) -> UnitCosts:
    """Load the unit-cost file; reject missing columns, job types, tiers or numbers."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not REQUIRED_COLUMNS <= set(reader.fieldnames or ()):
            raise ValueError("unit-cost file is missing required columns")
        rows = list(reader)
    all_tiers = BAND_TIERS["touching"]
    labels = {label: kind for kind, label in JOB_TYPES.items()}
    items: dict[str, list[Item]] = {kind: [] for kind in JOB_TYPES}
    references: dict[str, float] = {}
    other_rates: dict[str, float] = {}
    tier_band = {"< 40 km": "lt_40km", "< 8 km": "lt_8km", "< 1.6 km": "lt_1_6km", "touching / co-sited": "touching"}
    for row in rows:
        kind = labels.get(row["project_type"])
        if row["category"] == "Total":
            if row["project_type"] == OTHER_TYPE:
                other_rates[tier_band[row["share_tier"]]] = _positive(row["savings_rate"], "other rate")
            elif kind is not None:
                references[kind] = _positive(row["cost_2026_usd"], "reference cost")
            continue
        if row["category"] == "Scenario" or "(optional" in row["item"] or row["shareable"] != "Yes":
            continue
        if kind is None:
            raise ValueError(f"unknown job type in unit-cost file: {row['project_type']}")
        if row["share_tier"] not in all_tiers:
            raise ValueError(f"unknown sharing distance: {row['share_tier']}")
        items[kind].append(Item(_mechanism(row), row["share_tier"],
                                _positive(row["saving_per_unit_usd"], "saving"), row["rate_basis"] in EVIDENCE))
    if set(references) != set(JOB_TYPES) or set(other_rates) != set(BAND_TIERS):
        raise ValueError("unit-cost file needs a reference total for every job type and band")
    per_mile = {row["project_type"]: row["cost_basis"] == "per mile" for row in rows}
    jobs = {kind: Job(per_mile[JOB_TYPES[kind]], references[kind], tuple(items[kind])) for kind in JOB_TYPES}
    if any(job.reference_cost <= 0 or not job.items for job in jobs.values()):
        raise ValueError("every job type needs a positive reference cost and shareable items")
    return UnitCosts(jobs, other_rates)


def _applicable(kind: str, partner: str | None, band: str, costs: UnitCosts) -> list[Item]:
    return [item for item in costs.jobs[kind].items
            if item.tier in BAND_TIERS[band] and partner_fits(item.mechanism, kind, partner)]


def shared_mechanisms(kind_a: str | None, kind_b: str | None, band: str, costs: UnitCosts) -> list[str] | None:
    """What these two job types could share at this band, or None when a scope is not known."""
    if kind_a not in JOB_TYPES or kind_b not in JOB_TYPES:
        return None
    found = {item.mechanism for kind, partner in ((kind_a, kind_b), (kind_b, kind_a))
             for item in _applicable(kind, partner, band, costs)}
    return [MECHANISM_WORDS[name] for name in MECHANISM_WORDS if name in found]


def _plan_cost(project: dict) -> float | None:
    cost = project.get("cost_usd")
    return float(cost) if project.get("cost_basis") == "plan" and cost is not None and cost > 0 else None


def job_kind(project: dict) -> str | None:
    """The unit-cost job type used for this project (breaker and relay work sized as an upgrade)."""
    kind = project.get("project_type")
    text = f"{project.get('name') or ''} {project.get('description') or ''}"
    if kind == "equipment" and not LARGE_EQUIPMENT.search(text):
        return "substation_upgrade"
    return kind


def _share(project: dict, partner: dict, band: str, costs: UnitCosts) -> tuple[float, float, str] | None:
    """(low, high, how it was sized) for one project's own saving, or None when its size is unknown."""
    kind, partner_kind = job_kind(project), job_kind(partner)
    cost = _plan_cost(project)
    if kind not in JOB_TYPES:
        if cost is None:
            return None
        return 0.0, costs.other_rates[band] * cost, "average share of its printed cost"
    job = costs.jobs[kind]
    items = _applicable(kind, partner_kind, band, costs)
    low = sum(item.saving for item in items if item.evidence)
    high = sum(item.saving for item in items)
    miles = project.get("miles")
    if job.per_mile and miles:
        return low * miles, high * miles, f"{miles:g} stated miles"
    if cost is not None:
        factor = cost / job.reference_cost
        return low * factor, high * factor, f"sized to its printed cost of ${cost:,.0f}"
    if job.per_mile:
        return None
    return low, high, REFERENCE_WORDS[kind]


def _article(word: str) -> str:
    return f"an {word}" if word[:1] in "aeiou" else f"a {word}"


def _pair_words(first: str, second: str, band: str) -> str:
    where = "that touch" if band == "touching" else BAND_WORDS[band]
    if first == second:
        head, _, tail = first.partition(" of ")
        plural = head[:-1] + "ies" if head.endswith("y") else head + "s"
        return f"two {plural}{' of ' + tail if tail else ''} {where}"
    return f"{_article(first)} and {_article(second)} {where}"


def _round(value: float) -> int:
    return int((Decimal(str(value)) / PRECISION_USD).quantize(Decimal(1), rounding=ROUND_HALF_UP) * PRECISION_USD)


def _unavailable(status: str, reason: str) -> dict[str, object]:
    return {"status": status, "low_usd": None, "high_usd": None, "basis": reason, "assumption_ids": []}


def _join(words: list[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def estimate_savings(a: dict, b: dict, band: str, costs: UnitCosts) -> dict[str, object]:
    """A labelled screening range for the pair, or a visible reason there is none."""
    if a.get("year") is None or b.get("year") is None:
        return _unavailable("unknown_year", "At least one in-service year is not stated; no savings estimate.")
    gap = abs(int(a["year"]) - int(b["year"]))
    if gap > MAX_YEAR_GAP:
        return _unavailable("timing_too_far", f"In-service years are {gap} years apart; no savings estimate.")
    shares = [(project, _share(project, partner, band, costs)) for project, partner in ((a, b), (b, a))]
    sized = [(project, share) for project, share in shares if share is not None]
    words = [JOB_WORDS.get(project.get("project_type"), JOB_WORDS["other"]) for project in (a, b)]
    if not sized:
        return _unavailable("no_cost", "Neither plan gives a length or cost to size this pair; no savings estimate.")
    low = _round(sum(share[0] for _, share in sized))
    high = _round(sum(share[1] for _, share in sized))
    pair_words = _pair_words(words[0], words[1], band)
    if high <= 0:
        return _unavailable("no_cost", f"{pair_words[0].upper()}{pair_words[1:]} share no cost items in the "
                                       "team's unit-cost file; no savings estimate.")
    mechanisms = shared_mechanisms(job_kind(a), job_kind(b), band, costs)
    what = f"could share {_join(mechanisms)}" if mechanisms else "could share part of their costs"
    sizes = "; ".join(f"{JOB_WORDS.get(project.get('project_type'), JOB_WORDS['other'])}: {share[2]}"
                      for project, share in sized)
    unsized = "" if len(sized) == 2 else " The other project's size is not stated, so it adds nothing."
    basis = (f"Team unit-cost estimate: {pair_words} {what} ({sizes})."
             f"{unsized} The low end counts only items with public precedent; direct costs before contingency; "
             "shared savings unverified.")
    return {"status": "range", "low_usd": min(low, high), "high_usd": high, "basis": basis,
            "assumption_ids": [UNIT_COSTS_ID]}


def savings_bonus(savings: dict) -> float:
    """0 to +30% of score: +15% at $100,000 and the full 30% from $1,000,000 (log scale)."""
    high = savings.get("high_usd") or 0
    if savings.get("status") != "range" or high <= BONUS_FLOOR_USD:
        return 0.0
    share = math.log10(high / BONUS_FLOOR_USD) / math.log10(BONUS_FULL_USD / BONUS_FLOOR_USD)
    return round(MAX_BONUS * min(1.0, share), 4)
