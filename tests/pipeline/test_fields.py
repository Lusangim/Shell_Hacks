"""Real plan examples that pin parsed project fields to printed evidence."""

import json
from pathlib import Path

import pytest

from pipeline import build_all
from pipeline.extract import extract_desc_rows
from pipeline.fields import clean_text


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def projects() -> dict[str, dict]:
    build_all.build(ROOT)
    artifact = json.loads((ROOT / "data" / "build" / "projects.geojson").read_text(encoding="utf-8"))
    return {feature["properties"]["id"]: feature["properties"] for feature in artifact["features"]}


@pytest.mark.parametrize(
    ("page", "field", "expected"),
    [
        (1, "year", None),
        (1, "voltage_kv", [115.0]),
        (1, "project_type", "rebuild_line"),
        (2, "cost_usd", 1_150_364),
        (2, "cost_flags", ["below_list_threshold"]),
        (3, "project_type", "new_substation"),
        (4, "cost_usd", 1_238_443),
        (4, "cost_flags", ["printed_total_differs_from_sum", "below_list_threshold"]),
        (4, "miles", 1.0),
        (5, "year", None),
        (5, "miles", 13.5),
        (6, "miles", 1.2),
        (7, "miles", 12.5),
        (8, "year", 2026),
        (10, "project_type", "new_line"),
        (11, "voltage_kv", [115.0, 230.0]),
        (12, "project_type", "new_line"),
        (14, "project_type", "new_substation"),
        (16, "project_type", "new_line"),
        (20, "voltage_kv", [46.0, 115.0]),
        (24, "project_type", "new_substation"),
        (33, "project_type", "new_substation"),
        (34, "miles", 1.4),
        (41, "project_type", "equipment"),
        (44, "miles", 17.5),
        (54, "miles", 40.0),
    ],
)
def test_real_desc_fields(projects: dict[str, dict], page: int, field: str, expected: object) -> None:
    assert projects[f"desc-p{page}"][field] == expected


@pytest.mark.parametrize(
    ("page", "expected"),
    [(1, 15_775_885), (2, 1_150_364), (4, 1_238_443), (8, 93_603_207), (41, 5_376_418), (54, 18_875_000)],
)
def test_printed_desc_totals(projects: dict[str, dict], page: int, expected: int) -> None:
    assert projects[f"desc-p{page}"]["cost_usd"] == expected


def test_names_keep_pdf_en_dashes_and_sertp_duplicate_is_distinct(projects: dict[str, dict]) -> None:
    assert projects["desc-p4"]["name"].startswith("Eastover – Sumter")
    assert projects["desc-p41"]["name"].startswith("Okatie – McIntosh")
    duplicate = [p for p in projects.values() if p["source"]["page"] == 133
                 and p["name"] == "WANSLEY 500 KV, OVERSTRESSED BREAKER REPLACEMENTS"]
    assert len(duplicate) == 2
    assert duplicate[0]["description"] != duplicate[1]["description"]


def test_cost_columns_follow_the_printed_pdf_table() -> None:
    rows = extract_desc_rows(ROOT / "data" / "raw" / "desc_scrtp_2026_2030.pdf")
    assert [rows[3][field] for field in
            ("previous_cost", "cost_2026", "cost_2027", "cost_2028", "cost_2029", "cost_2030")] == [
                "88443", "1150000", "850000", "0", "0", "0",
            ]
    assert rows[3]["total_cost"] == "$1,238,443"
    assert sum(int(rows[3][field]) for field in
               ("previous_cost", "cost_2026", "cost_2027", "cost_2028", "cost_2029", "cost_2030")) == 2_088_443
    assert rows[53]["previous_cost"] == "25000"
    assert rows[53]["cost_2030"] == "18000000"
    assert rows[17]["total_cost"] == "$20,350,000"
    assert rows[17]["previous_cost"] == ""


def test_pdf_text_cleaning_keeps_dashes_and_removes_controls() -> None:
    assert clean_text("A\u200b\u0000\u212b  –  B") == "AÅ – B"
