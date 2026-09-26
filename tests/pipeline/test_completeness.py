"""Every printed project marker is parsed or explicitly excluded."""

import csv
import re
from pathlib import Path

import pypdf

from pipeline.extract import extract_desc_rows, extract_sertp_rows


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"


def _normalized(text: str) -> str:
    return re.sub(r"[\W_]+", "", text.casefold())


def _csv_rows(name: str) -> list[dict[str, str]]:
    with (RAW / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_desc_all_54_pages_have_one_row_and_source_text() -> None:
    reader = pypdf.PdfReader(RAW / "desc_scrtp_2026_2030.pdf")
    rows = extract_desc_rows(RAW / "desc_scrtp_2026_2030.pdf")
    assert len(reader.pages) == len(rows) == 54
    for page, row in enumerate(rows, 1):
        text = reader.pages[page - 1].extract_text() or ""
        assert f"Project {page} of 54" in text
        assert _normalized(row["project_name"]) in _normalized(text)
        assert _normalized(row["description"]) in _normalized(text)
    assert rows == _csv_rows("desc_2026_2030_projects.csv")


def test_sertp_459_markers_equal_rows_plus_listed_tva_exclusions() -> None:
    reader = pypdf.PdfReader(RAW / "sertp_2025_rtp.pdf")
    rows, exclusions = extract_sertp_rows(RAW / "sertp_2025_rtp.pdf")
    marker_counts = {page: (pdf_page.extract_text() or "").count("Project Name:")
                     for page, pdf_page in enumerate(reader.pages, 1)}
    assert sum(marker_counts.values()) == 459
    assert len(rows) == 427
    assert len(exclusions) == 32
    assert set(item["page"] for item in exclusions) == set(range(171, 182))
    assert all(item["reason"] == "TVA In- Service variant outside selected area" for item in exclusions)
    for page, count in marker_counts.items():
        assert count == sum(row["source_page"] == str(page) for row in rows) + sum(
            item["page"] == page for item in exclusions
        )
    assert rows == _csv_rows("sertp_2025_projects.csv")
    for row in rows:
        text = reader.pages[int(row["source_page"]) - 1].extract_text() or ""
        assert _normalized(row["project_name"]) in _normalized(text)
        assert _normalized(row["description"]) in _normalized(text)
