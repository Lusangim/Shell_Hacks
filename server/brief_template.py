"""Deterministic, offline coordination note from validated public artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Collection

from server.schemas import Brief, BriefSavings, Overlap, ProjectFeature


PROMPT_VERSION = "template-v1"


def _input_hash(pair: Overlap, a: ProjectFeature, b: ProjectFeature) -> str:
    payload = {
        "overlap": pair.model_dump(mode="json"),
        "project_a": a.model_dump(mode="json"),
        "project_b": b.model_dump(mode="json"),
        "prompt_version": PROMPT_VERSION,
        "generator": "template",
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _savings(pair: Overlap) -> BriefSavings:
    source = pair.savings
    if source.status == "range":
        assert source.low_usd is not None and source.high_usd is not None
        detail = source.basis or ""
        sizes = [words for key, words in (
            ("printed cost", "a printed plan cost"), ("stated miles", "stated line mileage"),
            ("sized as", "a reference job size"), ("average share", "an average share of a printed cost"),
        ) if key in detail]
        sizing = " and ".join(sizes) if sizes else "reference job sizes"
        basis = (
            f"Estimated possible saving: ${source.low_usd:,} to ${source.high_usd:,}, from team "
            f"unit costs for these job types at this distance, sized by {sizing}. An estimate, "
            "not a measured or agreed saving."
        )
    elif source.status == "no_cost":
        basis = (
            "No savings range is available: the loaded plans do not size this pair, or these "
            "job types share no cost items at this distance. A planning team would need a verified scope and cost "
            "before estimating any benefit."
        )
    elif source.status == "timing_too_far":
        basis = (
            "No savings range is available because the plan years are too far apart for the "
            "app's coordination screen. A schedule change would require a fresh comparison."
        )
    else:
        basis = (
            "No savings range is available because at least one project year is not stated "
            "in the loaded plans. Timing must be confirmed before screening a benefit."
        )
    return BriefSavings(
        status=source.status,
        low_usd=source.low_usd,
        high_usd=source.high_usd,
        basis=basis,
    )


def _project_attribution(project: ProjectFeature, utility: str) -> str:
    if project.properties.utility_basis == "inferred_from_location":
        return f"{project.properties.name} is attributed to {utility} (inferred from location). "
    return f"{project.properties.name} is listed by {utility}. "


def make_template_brief(
    pair: Overlap,
    project_a: ProjectFeature,
    project_b: ProjectFeature,
    contacts: Collection[str],
) -> Brief:
    """Build a brief without reading descriptions as instructions or calling a model."""
    if (project_a.properties.id, project_b.properties.id) != (pair.a, pair.b):
        raise ValueError("Project IDs do not match the overlap")
    utility_a = pair.a_utility
    utility_b = pair.b_utility
    allowed = set(contacts)
    if utility_a not in allowed or utility_b not in allowed:
        raise ValueError("Both utility organizations need source-backed contact labels")

    what = (
        _project_attribution(project_a, utility_a)
        + _project_attribution(project_b, utility_b)
        + "These are separate plan entries. This note identifies a possible planning "
        "conversation; it does not establish that either project can use the other's "
        "equipment, contract, or work order."
    )
    band = {
        "touching": "possibly touching" if pair.accuracy_pair.value != "exact" else "touching",
        "lt_1_6km": "within 1.6 km",
        "lt_8km": "within 8 km",
        "lt_40km": "within 40 km",
    }[pair.band.value]
    jurisdiction = (
        "The entries span South Carolina and Georgia. " if pair.cross_state else
        "The entries are in the same state. "
    )
    where = (
        f"The app places this pair in its {band} screening band, with a mapped separation "
        f"of {pair.distance_km:.1f} km. {jurisdiction}"
        "This is a proximity screen, not a surveyed route or a confirmed shared site. "
        "Check the source drawings and named endpoints before identifying physical work "
        "that could be combined."
    )
    year_a = str(pair.a_year) if pair.a_year is not None else "not stated"
    year_b = str(pair.b_year) if pair.b_year is not None else "not stated"
    when = (
        f"The loaded plans list {year_a} for the first project and {year_b} for the second. "
        "These plan dates are a starting point for a schedule discussion. Planners should "
        "confirm current milestones, outages, and approvals with each organization before "
        "treating the work as concurrent."
    )
    caveats = [
        "Neither source confirms a joint project, shared scope, or saving."
    ]
    if pair.accuracy_pair.value != "exact":
        caveats.append(
            "At least one mapped location is approximate. Its point is a planning proxy; "
            "check the source document and site details before discussing a shared location."
        )
    else:
        caveats.append(
            "The mapped points support screening only. Check field geometry and engineering "
            "scope against current plans before proposing a shared site."
        )
    if project_a.properties.utility_basis == "inferred_from_location" or project_b.properties.utility_basis == "inferred_from_location":
        caveats.append(
            "At least one utility attribution is inferred from location. Confirm ownership "
            "with the plan source before outreach."
        )

    sharing_by_reason = {
        "same_substation": "Compare substation outage windows, switching plans, site access, and interface drawings for the named work area.",
        "shared_endpoint": "Compare endpoint design, outage windows, and site access; confirm whether the planned work reaches the same equipment.",
        "proximity": "Compare route plans, access, and outage windows; nearby mapped work does not by itself establish shared construction.",
        "same_area_approximate": "Compare site diagrams and timing for the broad area; the mapped point may only represent a planning proxy.",
        "lines_cross": "Compare crossing geometry, clearances, and outage windows after both routes are verified from source drawings.",
    }
    return Brief(
        overlap_id=pair.id,
        what=what,
        where=where,
        when=when,
        what_to_share=[
            sharing_by_reason[pair.touch_reason],
            "Confirm whether construction sequencing has a real shared scope; proximity by "
            "itself does not establish an asset that can be shared.",
        ],
        savings_range=_savings(pair),
        who_to_contact=[utility_a, utility_b],
        caveats=caveats,
        sources=[project_a.properties.source, project_b.properties.source],
        generated_by="template",
        prompt_version=PROMPT_VERSION,
        generated_at=None,
        input_hash=_input_hash(pair, project_a, project_b),
    )
