"""Deterministic evidence gate for a coordination brief; no model or network access."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from server.schemas import Brief, Overlap, ProjectFeature


_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}(?!\d)")
_PERSON = re.compile(r"\b(?:Mr|Mrs|Ms|Dr)\.?\s+[A-Z][a-z]+|\b(?:contact|call|email|ask)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b")
_TITLE_PAIR = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b")
_BUZZWORD = re.compile(r"\b(?:seamless|unleash|revolutioniz\w*|synergy|transformative|game.changing|cutting.edge)\b", re.I)
_INJECTION = re.compile(r"BANANA_OVERRIDE|ignore previous instructions|synthetic test instruction|system prompt", re.I)
_REALIZED = re.compile(r"\b(?:saved|realized|achieved|guaranteed|will save)\b", re.I)
_YEAR = re.compile(r"\b(?:19|20|21)\d{2}\b")
_MONEY = re.compile(r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*(million|M)?\b", re.I)
_PAGE = re.compile(r"\b(?:page|p\.)\s*(\d+)\b", re.I)
_NUMBER = re.compile(r"(?<![\w$])\d[\d,]*(?:\.\d+)?")
_CODE_NUMBER = re.compile(r"\b[A-Za-z_]+[A-Za-z_0-9]*\d+[A-Za-z_0-9]*\b")
_WORD = re.compile(r"\b[\w]+(?:['-][\w]+)*\b")


@dataclass(frozen=True)
class GradeResult:
    errors: tuple[str, ...]
    word_count: int

    @property
    def ok(self) -> bool:
        return not self.errors


def load_contacts(path: Path) -> frozenset[str]:
    """Load the committed organization whitelist, rejecting personal or unsupported labels."""
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document["contacts"]
    labels: set[str] = set()
    for row in rows:
        label = row["label"]
        if not label or label != row["organization"] or not row["evidence_project_id"]:
            raise ValueError("Contact needs an organization label and project evidence")
        if row["planning_function"] is not None or row["public_url"] is not None:
            raise ValueError("No public planning function or contact URL is verified for this set")
        if _EMAIL.search(label) or _PHONE.search(label) or _PERSON.search(label):
            raise ValueError("Personal contact data is not allowed")
        labels.add(label)
    if len(labels) != len(rows):
        raise ValueError("Duplicate contact label")
    return frozenset(labels)


def _own_text(brief: Brief) -> str:
    return " ".join([
        brief.what, brief.where, brief.when, *brief.what_to_share,
        brief.savings_range.basis or "", *brief.who_to_contact, *brief.caveats,
    ])


def _source_free_text(text: str, a: ProjectFeature, b: ProjectFeature) -> str:
    # Names are source text, not the author's copy. Remove every verbatim occurrence.
    for name in sorted((a.properties.name, b.properties.name), key=len, reverse=True):
        text = text.replace(name, " ")
    return text


def _money_matches(value: str, unit: str | None, allowed: set[int]) -> bool:
    digits = value.replace(",", "").replace(".", "")
    if len(digits) > 64:
        return False
    try:
        with localcontext() as context:
            context.prec = max(28, len(digits) + 24)
            amount = Decimal(value.replace(",", ""))
            multiplier = Decimal(1_000_000) if unit else Decimal(1)
            precision = Decimal(1).scaleb(-max(0, -amount.as_tuple().exponent))
            for source in allowed:
                source_display = (Decimal(source) / multiplier).quantize(precision, rounding=ROUND_HALF_UP)
                if source_display == amount:
                    return True
    except InvalidOperation:
        return False
    return False


def _check_numbers(
    text: str, pair: Overlap, a: ProjectFeature, b: ProjectFeature,
) -> list[str]:
    errors: list[str] = []
    residual = text
    expected_years = {value for value in (pair.a_year, pair.b_year) if value is not None}
    expected_years.update(value for value in (a.properties.year, b.properties.year) if value is not None)
    for match in _YEAR.finditer(residual):
        if int(match.group()) not in expected_years:
            errors.append(f"year: unsupported {match.group()}")
    residual = _YEAR.sub(" ", residual)

    allowed_dollars = {
        value for value in (
            a.properties.cost_usd, b.properties.cost_usd,
            pair.savings.low_usd, pair.savings.high_usd,
        ) if value is not None
    }
    for match in _MONEY.finditer(residual):
        if not _money_matches(match.group(1), match.group(2), allowed_dollars):
            errors.append(f"number: unsupported dollar amount {match.group()}")
    residual = _MONEY.sub(" ", residual)

    pages = {a.properties.source.page, b.properties.source.page}
    for match in _PAGE.finditer(residual):
        if len(match.group(1)) > 64 or int(match.group(1)) not in pages:
            errors.append(f"number: unsupported page {match.group(1)}")
    residual = _PAGE.sub(" ", residual)

    for match in _CODE_NUMBER.finditer(residual):
        errors.append(f"number: unsupported embedded value {match.group()}")

    distance = Decimal(str(pair.distance_km)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    miles = {Decimal(str(p.properties.miles)) for p in (a, b) if p.properties.miles is not None}
    voltages = {Decimal(str(kv)) for p in (a, b) for kv in p.properties.voltage_kv}
    for match in _NUMBER.finditer(residual):
        if len(match.group()) > 64:
            errors.append("number: unsupported overlong value")
            continue
        value = Decimal(match.group().replace(",", ""))
        following = residual[match.end():]
        unit = re.match(r"\s*(km|kV|miles?|years?)\b", following, re.I)
        kind = unit.group(1).lower() if unit else ""
        valid = (
            (kind == "km" and value in {distance, Decimal("40"), Decimal("1.6"), Decimal("8")})
            or (kind == "kv" and value in voltages)
            or (kind in {"mile", "miles"} and value in miles)
            or (kind in {"year", "years"} and (
                value in {Decimal("2"), Decimal("3")}
                or (pair.year_gap is not None and value == Decimal(pair.year_gap))
            ))
        )
        if not valid:
            errors.append(f"number: unsupported value {match.group()}")
    return errors


def grade_brief(
    brief: Brief | dict[str, Any],
    pair: Overlap,
    project_a: ProjectFeature,
    project_b: ProjectFeature,
    contacts: frozenset[str] | set[str],
) -> GradeResult:
    """Return all evidence and copy failures, rather than approving plausible prose."""
    try:
        candidate = Brief.model_validate(brief)
    except ValidationError as exc:
        return GradeResult((f"schema: {exc.errors()[0]['msg']}",), 0)

    errors: list[str] = []
    if candidate.overlap_id != pair.id:
        errors.append("overlap: ID does not match input")
    if (project_a.properties.id, project_b.properties.id) != (pair.a, pair.b):
        errors.append("overlap: project IDs do not match input")

    raw = _own_text(candidate)
    own = _source_free_text(raw, project_a, project_b)
    word_count = len(_WORD.findall(raw))
    if not 150 <= word_count <= 300:
        errors.append(f"length: {word_count} words, expected 150 to 300")
    schedule_text = _source_free_text(candidate.when, project_a, project_b)
    schedule_years = {int(value) for value in _YEAR.findall(schedule_text)}
    for year in {value for value in (pair.a_year, pair.b_year) if value is not None}:
        if year not in schedule_years:
            errors.append(f"year: missing {year}")
    if (pair.a_year is None or pair.b_year is None) and not re.search(
        r"\b(?:not stated|unknown|not provided|unavailable)\b", schedule_text, re.I
    ):
        errors.append("year: unknown source year must be explicit")
    for utility in (pair.a_utility, pair.b_utility):
        if utility not in own:
            errors.append(f"utility: missing {utility}")
    if any(contact not in contacts for contact in candidate.who_to_contact):
        errors.append("contact: entry is absent from the committed organization whitelist")
    if set(candidate.who_to_contact) != {pair.a_utility, pair.b_utility}:
        errors.append("contact: include both project organizations")
    entity_free = own
    for entity in (*contacts, "South Carolina"):
        entity_free = entity_free.replace(entity, " ")
    if _EMAIL.search(raw) or _PHONE.search(raw) or _PERSON.search(own) or _TITLE_PAIR.search(entity_free):
        errors.append("contact: personal name, email, or phone is not allowed")
    if _INJECTION.search(own):
        errors.append("injection: source instruction appeared in the brief")
    if "\u2014" in own or "\u2013" in own:
        errors.append("dash: author prose contains an em or en dash")
    if _BUZZWORD.search(own):
        errors.append("buzzword: author prose contains barred marketing language")
    if _REALIZED.search(own):
        errors.append("realized: candidate asserts a confirmed or guaranteed saving")

    expected_sources = [project_a.properties.source, project_b.properties.source]
    if candidate.sources != expected_sources:
        errors.append("source: both exact project document and page citations are required")
    if candidate.savings_range.status != pair.savings.status:
        errors.append("savings: status does not match the overlap")
    if (candidate.savings_range.low_usd, candidate.savings_range.high_usd) != (
        pair.savings.low_usd, pair.savings.high_usd
    ):
        errors.append("savings: bounds do not match the overlap")
    basis = candidate.savings_range.basis or ""
    if pair.savings.status == "range":
        if "estimat" not in basis.lower():
            errors.append("savings: range must be labeled an estimate")
    elif not any(reason in basis.lower() for reason in ("cost", "year", "timing", "far apart")):
        errors.append("savings: missing reason for unavailable estimate")
    if pair.accuracy_pair.value != "exact" and not any(
        ("approximate" in caveat.lower() or "unknown" in caveat.lower()) and
        ("check" in caveat.lower() or "verify" in caveat.lower() or "confirm" in caveat.lower())
        for caveat in candidate.caveats
    ):
        errors.append("location: approximate or unknown placement needs a checking caveat")
    errors.extend(_check_numbers(own, pair, project_a, project_b))
    return GradeResult(tuple(errors), word_count)
