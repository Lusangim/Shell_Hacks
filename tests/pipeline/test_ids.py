"""Stable IDs, source citations, and generated artifact contracts."""

import csv
import hashlib
import json
import re
from pathlib import Path

import pypdf
from pydantic import TypeAdapter

from pipeline import build_all
from pipeline.ids import desc_id, sertp_ids
from server.schemas import Meta, Overlap, ProjectCollection


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
BUILT = ROOT / "data" / "build"


def _rows(name: str) -> list[dict[str, str]]:
    with (RAW / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalized(text: str) -> str:
    return re.sub(r"[\W_]+", "", text.casefold())


def test_all_parsed_rows_have_unique_repeatable_ids() -> None:
    desc = _rows("desc_2026_2030_projects.csv")
    sertp = _rows("sertp_2025_projects.csv")
    ids = [desc_id(i) for i in range(1, len(desc) + 1)] + sertp_ids(sertp)
    assert len(ids) == 481 == len(set(ids))
    assert ids == [desc_id(i) for i in range(1, len(desc) + 1)] + sertp_ids(sertp)
    page_133 = [(row, row_id) for row, row_id in zip(sertp, sertp_ids(sertp)) if row["source_page"] == "133"]
    repeated_name = [row_id for row, row_id in page_133 if row["project_name"] == "WANSLEY 500 KV, OVERSTRESSED BREAKER REPLACEMENTS"]
    assert len(repeated_name) == len(set(repeated_name)) == 2
    duplicated = [sertp[0], dict(sertp[0])]
    assert sertp_ids(duplicated)[1] == sertp_ids(duplicated)[0] + "-2"


def test_two_rebuilds_have_identical_ids_and_schema_valid_artifacts() -> None:
    build_all.build(ROOT)
    first = {
        name: hashlib.sha256((BUILT / name).read_bytes()).hexdigest()
        for name in ("projects.geojson", "overlaps.json", "meta.json", "source_rows.json")
    }
    build_all.build(ROOT)
    assert first == {
        name: hashlib.sha256((BUILT / name).read_bytes()).hexdigest()
        for name in first
    }
    projects = json.loads((BUILT / "projects.geojson").read_text(encoding="utf-8"))
    overlaps = json.loads((BUILT / "overlaps.json").read_text(encoding="utf-8"))
    meta = json.loads((BUILT / "meta.json").read_text(encoding="utf-8"))
    ProjectCollection.model_validate(projects)
    TypeAdapter(list[Overlap]).validate_python(overlaps)
    Meta.model_validate(meta)
    ids = [feature["properties"]["id"] for feature in projects["features"]]
    assert len(ids) == len(set(ids)) == 230


def test_every_project_citation_and_name_matches_source_pdf() -> None:
    projects = json.loads((BUILT / "projects.geojson").read_text(encoding="utf-8"))
    desc = _rows("desc_2026_2030_projects.csv")
    sertp = _rows("sertp_2025_projects.csv")
    sertp_by_id = dict(zip(sertp_ids(sertp), sertp))
    pdfs = {
        "desc": pypdf.PdfReader(RAW / "desc_scrtp_2026_2030.pdf"),
        "sertp": pypdf.PdfReader(RAW / "sertp_2025_rtp.pdf"),
    }
    for feature in projects["features"]:
        props = feature["properties"]
        source = props["source"]
        kind = "desc" if props["id"].startswith("desc-") else "sertp"
        page = source["page"]
        assert 1 <= page <= len(pdfs[kind].pages)
        if kind == "desc":
            row = desc[page - 1]
        else:
            row = sertp_by_id[props["id"]]
            assert page == int(row["source_page"])
        assert props["name"] == row["project_name"]
        assert props["description"] == row["description"]
        pdf_text = _normalized(pdfs[kind].pages[page - 1].extract_text() or "")
        printed_id = row.get("project_id") or ""
        assert _normalized(props["name"]) in pdf_text or (
            bool(printed_id) and _normalized(printed_id) in pdf_text
        ), f"{props['id']} is not supported by page {page}"
