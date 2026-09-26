"""The draft named examples must be traceable to loaded pairs and local plan pages."""

import json
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
METHODOLOGY = ROOT / "docs/METHODOLOGY.md"
PDFS = {
    "DESC": ROOT / "data/raw/desc_scrtp_2026_2030.pdf",
    "SERTP": ROOT / "data/raw/sertp_2025_rtp.pdf",
}
PAIRS = json.loads((ROOT / "data/build/overlaps.json").read_text(encoding="utf-8"))
PROJECTS = {
    feature["properties"]["id"]: feature["properties"]
    for feature in json.loads((ROOT / "data/build/projects.geojson").read_text(encoding="utf-8"))["features"]
}
BY_PAIR = {pair["id"]: pair for pair in PAIRS}


def table(heading: str) -> list[dict[str, str]]:
    lines = METHODOLOGY.read_text(encoding="utf-8").splitlines()
    start = lines.index(f"### {heading}") + 1
    while not lines[start].startswith("|"):
        start += 1
    headers = [cell.strip() for cell in lines[start].strip("|").split("|")]
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert len(cells) == len(headers)
        rows.append(dict(zip(headers, cells)))
    return rows


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_each_required_named_example_has_a_supported_pair_or_absence() -> None:
    rows = {row["Example"]: row for row in table("Named-example status")}
    assert set(rows) == {"Jasper", "Okatie", "Bluffton", "Urquhart", "McIntosh", "Thomson–Vogtle"}
    expected = {
        "Jasper": "desc-p12__sertp-p107-9bc088",
        "Okatie": "desc-p41__sertp-p107-9bc088",
        "Urquhart": "desc-p7__sertp-p150-ef263c",
        "McIntosh": "desc-p41__sertp-p107-9bc088",
    }
    for example, pair_id in expected.items():
        assert rows[example]["Status"] == "found"
        assert rows[example]["Pair ID"] == pair_id
        assert pair_id in BY_PAIR
        assert example.casefold() in " ".join(
            PROJECTS[BY_PAIR[pair_id][side]]["name"] for side in ("a", "b")
        ).casefold()
    for example, terms in {"Bluffton": ("bluffton",), "Thomson–Vogtle": ("thomson", "vogtle")}.items():
        assert rows[example]["Status"] == "not in loaded plans"
        assert rows[example]["Pair ID"] == "—"
        assert all(term not in project["name"].casefold() for project in PROJECTS.values() for term in terms)
        assert all(term in rows[example]["Evidence"].casefold() for term in terms)


def test_pair_evidence_matches_artifacts_and_cited_pdf_pages() -> None:
    rows = table("Pair evidence")
    expected = {
        "Savannah": ["desc-p41__sertp-p107-9bc088", "desc-p41__sertp-p111-fe1e3b"],
        "Jasper": ["desc-p12__sertp-p107-9bc088"],
        "Augusta": ["desc-p7__sertp-p150-ef263c", "desc-p26__sertp-p150-ef263c"],
    }
    assert [(row["Area"], row["Pair ID"]) for row in rows] == [
        (area, pair_id) for area, ids in expected.items() for pair_id in ids
    ]
    readers = {name: PdfReader(str(path)) for name, path in PDFS.items()}
    for row in rows:
        pair = BY_PAIR[row["Pair ID"]]
        assert int(row["Rank"]) == pair["rank"]
        assert row["Touch reason"] == pair["touch_reason"]
        assert row["Touch detail"] == pair["touch_detail"]
        assert row["Pair accuracy"] == pair["accuracy_pair"]
        assert row["Distance km"] == f'{pair["distance_km"]:.3f}'
        for side in ("a", "b"):
            project = PROJECTS[pair[side]]
            citation = (f'{project["name"]} (`{project["id"]}`) — {project["utility"]} — '
                        f'{project["source"]["doc"]}, p. {project["source"]["page"]} '
                        f'({project["accuracy"]})')
            assert row[f"Project {side.upper()}"] == citation
            reader = readers["DESC" if project["id"].startswith("desc-") else "SERTP"]
            page_text = normalized(reader.pages[project["source"]["page"] - 1].extract_text() or "")
            assert normalized(project["name"]) in page_text


def test_missing_name_search_records_pdf_hits_and_artifact_name_absence() -> None:
    rows = {row["Term"]: row for row in table("Source-name search")}
    assert set(rows) == {"Bluffton", "Thomson", "Vogtle"}
    page_texts = {
        name: [(page.extract_text() or "").casefold() for page in PdfReader(str(path)).pages]
        for name, path in PDFS.items()
    }
    for term, row in rows.items():
        for name, texts in page_texts.items():
            pages = [index for index, text in enumerate(texts, 1) if term.casefold() in text]
            assert row[f"{name} PDF pages"] == (", ".join(map(str, pages)) if pages else "none")
        assert row["Kept project names"] == "none"
        assert not any(term.casefold() in project["name"].casefold() for project in PROJECTS.values())


def test_demo_pair_states_deerfield_distinction_and_unverified_shared_asset() -> None:
    text = METHODOLOGY.read_text(encoding="utf-8")
    assert "desc-p41__sertp-p107-9bc088" in text
    assert "Deerfield Switching Station" in text
    assert "location not stated" in text
    assert "McIntosh 230 kV bus" in text
    assert "shared physical asset is unverified" in text
    assert "Georgia Power IRP" in text and "founder question" in text
