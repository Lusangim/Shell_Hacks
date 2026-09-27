"""Overlap detail, conflict-matrix export, and whitelisted local PDF routes."""

from __future__ import annotations

import copy
import csv
import io
import json
import re
import shutil
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from server.app import OverlapDetail, create_app
from server.schemas import ErrorResponse, Overlap
from server.settings import ROOT


FIXTURES = ROOT / "tests" / "fixtures" / "api"
BUILD = ROOT / "data" / "build"
OVERLAPS = TypeAdapter(list[Overlap])
KEY_COLUMNS = [
    "Rank", "Score", "Utility A", "Project A", "In service A", "Utility B", "Project B", "In service B",
    "Distance (km)", "Proximity", "Years to coordinate", "Crosses state line",
    "Possible saving low (USD)", "Possible saving high (USD)", "Location accuracy", "Sources",
    "Coordination status", "Notes", "Overlap ID",
]


def km(value: float) -> str:
    """The page's toFixed(1): one decimal, exact ties rounded up."""
    return str(Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


@pytest.fixture
def real_client() -> TestClient:
    with TestClient(create_app(artifact_dir=BUILD), base_url="http://localhost") as client:
        yield client


@pytest.fixture
def artifacts(tmp_path: Path) -> Path:
    for source, target in (
        ("projects.json", "projects.json"),
        ("overlaps.json", "overlaps.json"),
        ("meta.json", "meta.json"),
        ("basemap.json", "basemap.json"),
    ):
        shutil.copyfile(FIXTURES / source, tmp_path / target)
    return tmp_path


def csv_rows(client: TestClient, params: list[tuple[str, str]] | None = None) -> list[dict[str, str]]:
    response = client.get("/api/export/overlaps.csv", params=params)
    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert response.headers["content-type"].startswith("text/csv")
    return list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"), newline="")))


def test_real_detail_includes_both_projects_savings_and_citations(real_client: TestClient) -> None:
    response = real_client.get("/api/overlaps/desc-p41__sertp-p107-9bc088")
    assert response.status_code == 200
    detail = OverlapDetail.model_validate(response.json())
    assert detail.overlap.id == "desc-p41__sertp-p107-9bc088"
    assert (detail.project_a.properties.id, detail.project_b.properties.id) == ("desc-p41", "sertp-p107-9bc088")
    assert detail.overlap.touch_reason == "shared_endpoint"
    assert detail.overlap.touch_detail
    assert (detail.savings.low_usd, detail.savings.high_usd) == (62000, 264000)
    assert [(source.doc, source.page) for source in detail.sources] == [
        ("SCRTP Planned Facilities 2026-2030 $2M & Above", 41),
        ("SERTP 2025 Regional Transmission Plan (Nov 26 2025)", 107),
    ]
    assert detail.sources[0] == detail.project_a.properties.source
    assert detail.sources[1] == detail.project_b.properties.source


@pytest.mark.parametrize("pair_id,source_page", [
    ("desc-p41__sertp-p107-9bc088", 107),
    ("desc-p41__sertp-p111-fe1e3b", 111),
])
def test_mcintosh_evidence_survives_detail_and_csv(
    real_client: TestClient, pair_id: str, source_page: int,
) -> None:
    pairs = json.loads((BUILD / "overlaps.json").read_text(encoding="utf-8"))
    artifact = next(pair for pair in pairs if pair["id"] == pair_id)
    response = real_client.get(f"/api/overlaps/{pair_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["overlap"] == artifact
    assert "Verify work locations" in artifact["can_share"]
    assert "Deerfield Switching Station, location not stated" in artifact["touch_detail"]
    if source_page == 111:
        assert "6.7-mile Goshen (Savannah)–Georgia Pacific (Rincon)" in artifact["touch_detail"]
        assert "does not establish work at McIntosh" in artifact["touch_detail"]
    row = next(row for row in csv_rows(real_client) if row["Overlap ID"] == pair_id)
    assert artifact["touch_reason"] == "shared_endpoint"
    # The key-facts file cites both plan pages; the evidence prose stays in the detail and the plans.
    assert row["Sources"] == ("SCRTP Planned Facilities 2026-2030 $2M & Above, p. 41; "
                              f"SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. {source_page}")
    assert artifact["touch_detail"] not in " ".join(row.values())


def test_synthetic_detail_and_unknown_id(artifacts: Path) -> None:
    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as client:
        response = client.get("/api/overlaps/desc-p1__sertp-p1-abcdef")
        assert response.status_code == 200
        detail = OverlapDetail.model_validate(response.json())
        assert (detail.savings.low_usd, detail.savings.high_usd) == (100, 200)
        assert detail.sources[0].page == 1
        missing = client.get("/api/overlaps/not-a-pair")
        assert missing.status_code == 404
        assert ErrorResponse.model_validate(missing.json()).error.code == "not_found"


@pytest.mark.parametrize("params", [
    [],
    [("utility", "Dominion Energy SC"), ("utility", "Georgia Power")],
    [("cross_state", "true")],
])
def test_export_rows_equal_filtered_list(real_client: TestClient, params: list[tuple[str, str]]) -> None:
    listing = real_client.get("/api/overlaps", params=params)
    assert listing.status_code == 200
    pairs = OVERLAPS.validate_python(listing.json())
    rows = csv_rows(real_client, params)
    assert pairs
    assert [row["Overlap ID"] for row in rows] == [pair.id for pair in pairs]
    assert [int(row["Rank"]) for row in rows] == [pair.rank for pair in pairs]
    assert [float(row["Score"]) for row in rows] == [pair.score for pair in pairs]
    assert [row["Proximity"] for row in rows] == [pair.band_label for pair in pairs]
    assert [row["Distance (km)"] for row in rows] == [km(pair.distance_km) for pair in pairs]
    assert [row["Crosses state line"] for row in rows] == ["Yes" if pair.cross_state else "No" for pair in pairs]


def test_export_has_only_the_key_columns(real_client: TestClient) -> None:
    response = real_client.get("/api/export/overlaps.csv", params=[("limit", "1")])
    assert response.content.startswith(b"\xef\xbb\xbf" + ",".join(KEY_COLUMNS).encode() + b"\r\n")
    rows = csv_rows(real_client, [("limit", "1")])
    assert len(rows) > 1
    assert list(rows[0]) == KEY_COLUMNS
    assert all(row["Coordination status"] == "" and row["Notes"] == "" for row in rows)


def test_export_reads_like_a_planner_worksheet(real_client: TestClient) -> None:
    from datetime import date

    rows = csv_rows(real_client)
    top = rows[0]
    assert (top["Rank"], top["Score"]) == ("1", "5.823")
    assert (top["Utility A"], top["Utility B"]) == ("Dominion Energy SC", "Georgia Power (inferred)")
    assert (top["In service A"], top["In service B"]) == ("2028", "2028")
    assert top["Years to coordinate"] == str(max(0, 2028 - date.today().year))
    assert (top["Distance (km)"], top["Proximity"], top["Crosses state line"]) == ("0.0", "Touching / crossing", "Yes")
    assert (top["Possible saving low (USD)"], top["Possible saving high (USD)"]) == ("62000", "264000")
    assert top["Location accuracy"] == "Approximate / Exact"
    town = [row for row in rows if "(town only)" in row["Location accuracy"]]
    assert town, "town-only placements are qualified in the accuracy column"
    for row in rows:
        # No internal codes in the reader-facing columns; numbers stay plain so Excel can sort them.
        for column in ("Proximity", "Location accuracy", "Crosses state line"):
            assert "_" not in row[column], (column, row[column])
        assert re.fullmatch(r"\d+\.\d", row["Distance (km)"]), row["Distance (km)"]
        for column in ("Possible saving low (USD)", "Possible saving high (USD)"):
            assert row[column] == "" or re.fullmatch(r"0|[1-9]\d*", row[column]), (column, row[column])
        assert re.fullmatch(r"(Exact|Approximate( \(town only\))?) / (Exact|Approximate( \(town only\))?)",
                            row["Location accuracy"]), row["Location accuracy"]


def test_export_empty_filter_is_header_only(real_client: TestClient) -> None:
    assert csv_rows(real_client, [("utility", "No such utility")]) == []


def test_export_all_real_rows_keep_key_fields_verbatim(real_client: TestClient) -> None:
    from datetime import date

    pairs = real_client.get("/api/overlaps").json()
    projects = {item["properties"]["id"]: item["properties"]
                for item in real_client.get("/api/projects").json()["features"]}
    response = real_client.get("/api/export/overlaps.csv")
    rows = csv_rows(real_client)
    assert len(rows) == len(pairs) == 465
    assert sum(pair["savings"]["status"] == "range" for pair in pairs) == 119
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert response.content.endswith(b"\r\n")
    assert b"\n" not in response.content.replace(b"\r\n", b"")
    assert list(rows[0]) == KEY_COLUMNS
    for row, pair in zip(rows, pairs, strict=True):
        savings = pair["savings"]
        assert row["Overlap ID"] == pair["id"]
        assert row["Rank"] == str(pair["rank"])
        assert row["Distance (km)"] == km(pair["distance_km"])
        assert row["Proximity"] == pair["band_label"]
        assert row["Crosses state line"] == ("Yes" if pair["cross_state"] else "No")
        years = [pair["a_year"], pair["b_year"]]
        assert row["Years to coordinate"] == (
            "unknown" if None in years else str(max(0, min(years) - date.today().year)))
        # A pair without an estimate leaves both cells blank, never 0.
        for bound in ("low", "high"):
            amount = savings[f"{bound}_usd"]
            cell = row[f"Possible saving {bound} (USD)"]
            assert cell == (str(amount) if savings["status"] == "range" else "")
        citations = []
        for side in ("A", "B"):
            project = projects[pair[side.lower()]]
            assert row[f"Project {side}"] == project["name"]
            assert row[f"In service {side}"] == (str(project["year"]) if project["year"] is not None else "unknown")
            citations.append(f'{project["source"]["doc"]}, p. {project["source"]["page"]}')
        assert row["Sources"] == "; ".join(citations)
        for assumption_id in savings["assumption_ids"]:
            assert assumption_id not in " ".join(row.values())
    assert any(row["Possible saving low (USD)"] == "" for row in rows)


def test_export_top_and_mileage_sized_pairs_keep_their_estimates(real_client: TestClient) -> None:
    rows = csv_rows(real_client)
    top = rows[0]
    assert top["Overlap ID"] == "desc-p41__sertp-p107-9bc088"
    assert (top["Possible saving low (USD)"], top["Possible saving high (USD)"]) == ("62000", "264000")
    mileage = rows[1]
    assert mileage["Rank"] == "2"
    assert (mileage["Possible saving low (USD)"], mileage["Possible saving high (USD)"]) == ("62000", "191000")


def test_csv_inferred_utility_qualifier_does_not_change_canonical_data(real_client: TestClient) -> None:
    before = real_client.get("/api/projects").json()
    rows = {row["Overlap ID"]: row for row in csv_rows(real_client)}
    assert rows["desc-p41__sertp-p107-9bc088"]["Utility B"] == "Georgia Power (inferred)"
    assert rows["desc-p41__sertp-p111-fe1e3b"]["Utility B"] == "Georgia Power"
    assert rows["desc-p41__sertp-p107-9bc088"]["Utility A"] == "Dominion Energy SC"
    for pair in real_client.get("/api/overlaps").json():
        for side in ("a", "b"):
            project = next(p["properties"] for p in before["features"] if p["properties"]["id"] == pair[side])
            suffix = " (inferred)" if project["utility_basis"] == "inferred_from_location" else ""
            assert rows[pair["id"]][f"Utility {side.upper()}"] == project["utility"] + suffix
            assert pair[f"{side}_utility"] == project["utility"]
    assert real_client.get("/api/projects").json() == before


@pytest.mark.parametrize("status,reason", [
    ("unknown_year", "At least one in-service year is not stated; no savings estimate."),
    ("no_cost", "No printed plan cost or eligible stated line mileage for a proxy estimate."),
    ("timing_too_far", "In-service years are 3 years apart; no savings estimate."),
])
def test_csv_non_range_reasons_have_no_amounts(artifacts: Path, status: str, reason: str) -> None:
    pairs = json.loads((artifacts / "overlaps.json").read_text(encoding="utf-8"))
    pairs[0]["savings"] = dict(status=status, basis=reason, low_usd=None, high_usd=None, assumption_ids=[])
    (artifacts / "overlaps.json").write_text(json.dumps(pairs), encoding="utf-8")
    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as client:
        row = csv_rows(client)[0]
    assert row["Possible saving low (USD)"] == row["Possible saving high (USD)"] == ""
    assert reason not in " ".join(row.values())


def test_csv_leaves_out_basis_prose_and_assumption_ids(artifacts: Path) -> None:
    pairs = json.loads((artifacts / "overlaps.json").read_text(encoding="utf-8"))
    pairs[0]["savings"]["basis"] = "=SYNTHETIC_FORMULA()"
    (artifacts / "overlaps.json").write_text(json.dumps(pairs), encoding="utf-8")
    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as client:
        row = csv_rows(client)[0]
    assert (row["Possible saving low (USD)"], row["Possible saving high (USD)"]) == ("100", "200")
    assert "SYNTHETIC_FORMULA" not in " ".join(row.values())
    assert "fixture-1" not in " ".join(row.values())


@pytest.mark.parametrize("params", [
    [("year_min", "2030"), ("year_max", "2020")],
    [("band", "invalid")],
    [("voltage_kv", "-1")],
])
def test_export_bad_filters_are_typed_422(real_client: TestClient, params: list[tuple[str, str]]) -> None:
    response = real_client.get("/api/export/overlaps.csv", params=params)
    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "invalid_request"


def test_export_is_not_truncated_by_list_page_limit(artifacts: Path) -> None:
    collection = json.loads((artifacts / "projects.json").read_text(encoding="utf-8"))
    original_pair = json.loads((artifacts / "overlaps.json").read_text(encoding="utf-8"))[0]
    sample = collection["features"][1]
    collection["features"] = [collection["features"][0]]
    pairs = []
    for number in range(1, 503):
        project = copy.deepcopy(sample)
        project_id = f"sertp-p{number}-abcdef"
        project["properties"]["id"] = project_id
        collection["features"].append(project)
        pair = copy.deepcopy(original_pair)
        pair["id"] = f"desc-p1__{project_id}"
        pair["b"] = project_id
        pair["rank"] = number
        pairs.append(pair)
    (artifacts / "projects.json").write_text(json.dumps(collection), encoding="utf-8")
    (artifacts / "overlaps.json").write_text(json.dumps(pairs), encoding="utf-8")
    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as client:
        listing = OVERLAPS.validate_python(client.get("/api/overlaps").json())
        rows = csv_rows(client)
    assert len(listing) == 500
    assert len(rows) == 502
    assert rows[-1]["Overlap ID"] == "desc-p1__sertp-p502-abcdef"


def test_csv_escapes_formula_and_control_prefixes_but_not_numbers(artifacts: Path) -> None:
    collection = json.loads((artifacts / "projects.json").read_text(encoding="utf-8"))
    collection["features"][0]["properties"]["name"] = "=SUM(1,1)"
    collection["features"][0]["properties"]["utility"] = "+Utility"
    collection["features"][0]["properties"]["source"]["doc"] = "@Document"
    collection["features"][1]["properties"]["name"] = "-Command"
    collection["features"][1]["properties"]["utility"] = "\t=SUM(1,1)\rnext"
    (artifacts / "projects.json").write_text(json.dumps(collection), encoding="utf-8")
    pairs = json.loads((artifacts / "overlaps.json").read_text(encoding="utf-8"))
    pairs[0]["band_label"] = "=HYPERLINK(1)"
    (artifacts / "overlaps.json").write_text(json.dumps(pairs), encoding="utf-8")
    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as client:
        row = csv_rows(client)[0]
    assert row["Project A"] == "'=SUM(1,1)"
    assert row["Utility A"] == "'+Utility"
    assert row["Project B"] == "'-Command"
    assert row["Sources"].startswith("'@Document, p. ")
    assert row["Utility B"] == "'\t=SUM(1,1)\rnext"
    assert row["Proximity"] == "'=HYPERLINK(1)"
    assert row["Rank"] == "1"
    assert row["Distance (km)"] == "0.0"
    assert row["Possible saving low (USD)"] == "100"
    collection["features"][1]["properties"]["utility"] = "\r=SUM(1,1)"
    (artifacts / "projects.json").write_text(json.dumps(collection), encoding="utf-8")
    with TestClient(create_app(artifact_dir=artifacts), base_url="http://localhost") as client:
        assert csv_rows(client)[0]["Utility B"] == "'\r=SUM(1,1)"


@pytest.mark.parametrize("doc_id,filename", [
    ("desc-scrtp-2026-2030", "desc_scrtp_2026_2030.pdf"),
    ("sertp-2025-rtp", "sertp_2025_rtp.pdf"),
])
def test_whitelisted_pdf_has_safe_inline_headers(real_client: TestClient, doc_id: str, filename: str) -> None:
    response = real_client.get(f"/api/sources/{doc_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == f'inline; filename="{filename}"'
    assert response.content.startswith(b"%PDF")
    assert len(response.content) == (ROOT / "data" / "raw" / filename).stat().st_size


@pytest.mark.parametrize("path", [
    "/api/sources/unknown",
    "/api/sources/..",
    "/api/sources/..%2Fdesc_scrtp_2026_2030.pdf",
    "/api/sources/%2e%2e%5csertp_2025_rtp.pdf",
])
def test_unknown_or_traversal_source_is_typed_404(real_client: TestClient, path: str) -> None:
    response = real_client.get(path)
    assert response.status_code == 404
    assert ErrorResponse.model_validate(response.json()).error.code == "not_found"
