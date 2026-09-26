"""Offline extraction of the two public plan PDFs into reviewed source CSVs."""

from __future__ import annotations

import csv
import os
import re
import tempfile
from pathlib import Path

import pypdf

from pipeline.fields import clean_text


DESC_SOURCE = "SCRTP Planned Facilities 2026-2030 $2M & Above"
SERTP_SOURCE = "SERTP 2025 Regional Transmission Plan (Nov 26 2025)"
DESC_COLUMNS = ("previous_cost", "cost_2026", "cost_2027", "cost_2028", "cost_2029", "cost_2030")
TABLE_HEADER = re.compile(r"Previous\s+2026\s+2027\s+2028\s+2029\s+2030\s+Total")


def _section(body: str, start: str, end: str) -> str:
    match = re.search(rf"{re.escape(start)}\s*\n(.+?)\n\s*{re.escape(end)}", body, re.S)
    if not match:
        raise ValueError(f"missing PDF section {start} / {end}")
    return clean_text(match.group(1))


def _desc_costs(body: str, page: int) -> tuple[str, list[str]]:
    cost_section = body.split("Estimated Project Cost", 1)
    if len(cost_section) != 2:
        raise ValueError(f"DESC page {page} has no cost section")
    text = cost_section[1]
    header = TABLE_HEADER.search(text)
    if header:
        amounts = re.findall(r"\$?\s*\d[\d,]*", text[header.end():])
        if len(amounts) != 7:
            raise ValueError(f"DESC page {page} has {len(amounts)} cost values, expected 7")
        values = [str(int(re.sub(r"\D", "", amount))) for amount in amounts]
        return f"${int(values[-1]):,}", values[:-1]
    prose = re.search(r"Estimated cost of\s+\$([\d,]+)", text)
    if prose:
        return f"${int(prose.group(1).replace(',', '')):,}", [""] * 6
    raise ValueError(f"DESC page {page} has neither a cost table nor a stated prose estimate")


def extract_desc_rows(path: Path) -> list[dict[str, str]]:
    reader = pypdf.PdfReader(path)
    rows: list[dict[str, str]] = []
    total_pages = len(reader.pages)
    for page, pdf_page in enumerate(reader.pages, 1):
        body = pdf_page.extract_text() or ""
        if f"Project {page} of {total_pages}" not in body:
            raise ValueError(f"DESC page {page} project marker is missing or out of order")
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        try:
            first = lines.index("5 Year Budget") + 1
            last = lines.index("Project ID")
        except ValueError as exc:
            raise ValueError(f"DESC page {page} has no project name boundary") from exc
        name = clean_text(" ".join(lines[first:last]))
        if not name:
            raise ValueError(f"DESC page {page} has no project name")
        total, columns = _desc_costs(body, page)
        rows.append({
            "utility": "Dominion Energy South Carolina", "project_name": name,
            "project_id": _section(body, "Project ID", "Project Description"),
            "description": _section(body, "Project Description", "Project Need"),
            "need": _section(body, "Project Need", "Project Status"),
            "status": _section(body, "Project Status", "Planned In-Service Date"),
            "planned_in_service": _section(body, "Planned In-Service Date", "Estimated Project Cost"),
            "total_cost": total, **dict(zip(DESC_COLUMNS, columns)), "source": DESC_SOURCE,
        })
    if len(rows) != 54:
        raise ValueError(f"DESC parsed {len(rows)} rows, expected 54")
    return rows


def extract_sertp_rows(path: Path) -> tuple[list[dict[str, str]], list[dict[str, int | str]]]:
    reader = pypdf.PdfReader(path)
    rows: list[dict[str, str]] = []
    exclusions: list[dict[str, int | str]] = []
    balancing_area: str | None = None
    for page, pdf_page in enumerate(reader.pages, 1):
        body = pdf_page.extract_text() or ""
        area_match = re.search(r"(\S[\w &/\-]+?) Balancing Authority Area", body)
        if area_match:
            balancing_area = area_match.group(1).replace("SERTP TRANSMISSION PROJECTS (CEII)", "").strip()
        markers = body.count("Project Name:")
        parsed_on_page = 0
        for entry in re.split(r"In-Service\s*\n\s*Year:\s*\n", body)[1:]:
            year = re.match(r"\s*(\d{4})", entry)
            name = re.search(r"Project Name:\s*(.+?)\nDescription:", entry, re.S)
            description = re.search(r"Description:\s*(.+?)(?:\n\s*\nSupporting|\nSupporting)", entry, re.S)
            need = re.search(r"Statements:\s*(.+?)(?:\n\s*\n\s*\n|$)", entry, re.S)
            if name:
                if not balancing_area or not description:
                    raise ValueError(f"SERTP page {page} has an incomplete project")
                rows.append({
                    "utility_area": balancing_area, "in_service_year": year.group(1) if year else "",
                    "project_name": clean_text(name.group(1)),
                    "description": clean_text(description.group(1)),
                    "need": clean_text(need.group(1)) if need else "", "source_page": str(page),
                    "source": SERTP_SOURCE,
                })
                parsed_on_page += 1
        if parsed_on_page != markers:
            if 171 <= page <= 181 and "TVA Balancing Authority Area" in body and "In- Service" in body:
                exclusions.extend({"page": page, "marker_ordinal": ordinal,
                                   "reason": "TVA In- Service variant outside selected area"}
                                  for ordinal in range(1, markers + 1))
            else:
                raise ValueError(f"SERTP page {page}: {markers} markers but {parsed_on_page} rows")
    if len(rows) != 427 or len(exclusions) != 32:
        raise ValueError(f"SERTP row accounting changed: {len(rows)} rows, {len(exclusions)} exclusions")
    return rows, exclusions


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".extract-", suffix=".csv", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def extract_to_csv(raw: Path) -> tuple[int, int]:
    desc = extract_desc_rows(raw / "desc_scrtp_2026_2030.pdf")
    sertp, exclusions = extract_sertp_rows(raw / "sertp_2025_rtp.pdf")
    if len(desc) != 54 or len(sertp) + len(exclusions) != 459:
        raise ValueError("source project markers do not reconcile")
    _write_csv(raw / "desc_2026_2030_projects.csv", desc)
    _write_csv(raw / "sertp_2025_projects.csv", sertp)
    return len(desc), len(sertp)


if __name__ == "__main__":
    raw_dir = Path(__file__).resolve().parents[1] / "data" / "raw"
    desc_count, sertp_count = extract_to_csv(raw_dir)
    print(f"DESC projects: {desc_count}; SERTP projects: {sertp_count}")
