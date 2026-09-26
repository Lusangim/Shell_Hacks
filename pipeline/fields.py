"""Conservative, source-derived project fields."""

from __future__ import annotations

import re
import unicodedata
from datetime import date


def clean_text(value: str) -> str:
    """Normalize PDF whitespace and compatibility glyphs without rewriting dashes."""
    normalized = unicodedata.normalize("NFKC", value)
    stripped = "".join(" " if char.isspace() else char
                       for char in normalized
                       if unicodedata.category(char) not in {"Cf", "Cc"} or char.isspace())
    return " ".join(stripped.split())


def parse_in_service_year(value: str | None) -> int | None:
    if not value:
        return None
    text = clean_text(value)
    dates = list(re.finditer(r"\b(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})\b", text))
    if dates:
        month, day, year = (int(part) for part in dates[-1].groups())
        if year < 100:
            year += 2000
        try:
            date(year, month, day)
        except ValueError:
            return None
        return year
    return int(text) if re.fullmatch(r"20\d{2}", text) else None


def parse_cost(value: str | None, columns: list[str] | None = None) -> tuple[int | None, str, list[str]]:
    if not value:
        return None, "none", []
    if not re.fullmatch(r"\$[\d,]+", value):
        raise ValueError(f"unparseable printed total: {value}")
    total = int(value[1:].replace(",", ""))
    flags: list[str] = []
    if columns and all(columns):
        amounts = [int(column.replace(",", "")) for column in columns]
        if sum(amounts) != total:
            flags.append("printed_total_differs_from_sum")
    elif columns and any(columns):
        raise ValueError("incomplete printed cost columns")
    if total < 2_000_000:
        flags.append("below_list_threshold")
    return total, "plan", flags


def voltage_kv(name: str, description: str | None) -> list[float]:
    text = f"{name} {description or ''}"
    tokens = re.findall(r"\b(\d+(?:\.\d+)?(?:\s*[-/]\s*\d+(?:\.\d+)?)*)\s*kV\b", text, re.I)
    values = {float(piece) for token in tokens for piece in re.split(r"\s*[-/]\s*", token)}
    return sorted(value for value in values if value > 0)


def project_type(name: str, description: str | None) -> str:
    title = name.casefold()
    body = (description or "").casefold()
    if any(term in title for term in ("reactor", "breaker", "relay", "statcom")):
        return "equipment"
    if "reconductor" in title or "reconductoring" in title:
        return "reconductor"
    if re.search(r"\b(substation|sub)\b", title):
        if any(term in title for term in ("construct", "new sub", "new station")):
            return "new_substation"
        if any(term in title for term in ("upgrade", "expand", "replace")):
            return "substation_upgrade"
        return "other"
    if any(term in title for term in ("rebuild", "replace structure", "replace pole")):
        return "rebuild_line"
    if any(term in title for term in ("construct", "new line", "add 230kv line", "add 115kv line")):
        return "new_line"
    if "reconductor" in body and "rebuild" not in title:
        return "reconductor"
    return "other"


def miles(name: str, description: str | None) -> float | None:
    pattern = r"\b(\d+(?:\.\d+)?)\s*(?:miles?|mi\.?)\b"
    described = {float(match) for match in re.findall(pattern, description or "", re.I)}
    if described:
        return next(iter(described)) if len(described) == 1 else None
    titled = {float(match) for match in re.findall(pattern, name, re.I)}
    return next(iter(titled)) if len(titled) == 1 else None
