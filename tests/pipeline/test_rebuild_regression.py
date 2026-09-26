"""Regression checks for the offline data-package rebuild."""

import hashlib
import json
from pathlib import Path

import pytest

from pipeline import build_all


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ("projects.geojson", "placement_report.csv", "overlaps.json", "meta.json")
TOP_TEN = [
    ("DESC-41", "SERTP-239"),
    ("SERTP-123", "SERTP-137"),
    ("DESC-41", "SERTP-250"),
    ("DESC-41", "SERTP-256"),
    ("SERTP-125", "SERTP-137"),
    ("SERTP-135", "SERTP-137"),
    ("SERTP-166", "SERTP-194"),
    ("SERTP-289", "SERTP-318"),
    ("SERTP-289", "SERTP-317"),
    ("SERTP-118", "SERTP-124"),
]


def _hashes() -> dict[str, str]:
    return {
        name: hashlib.sha256((ROOT / "data" / "build" / name).read_bytes()).hexdigest()
        for name in OUTPUTS
    }


def test_offline_rebuild_preserves_counts_pairs_and_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("offline rebuild attempted a network call")

    monkeypatch.setattr("urllib.request.urlopen", no_network)
    build_all.build(ROOT)
    first = _hashes()
    build_all.build(ROOT)
    assert _hashes() == first

    artifact = ROOT / "data" / "build"
    meta = json.loads((artifact / "meta.json").read_text(encoding="utf-8"))
    projects = json.loads((artifact / "projects.geojson").read_text(encoding="utf-8"))
    overlaps = json.loads((artifact / "overlaps.json").read_text(encoding="utf-8"))

    assert meta["stages"]["source_rows"] == 481
    assert meta["stages"]["placement_candidates"] == 380
    assert meta["stages"]["kept"] == 230
    assert meta["stages"]["placed"] == 181
    assert meta["stages"]["overlaps"] == 477
    assert meta["stages"]["cross_state"] == 44
    assert meta["stages"]["source_rows"] == (
        meta["stages"]["kept"] + sum(meta["dropped_by_reason"].values())
    )
    assert len(meta["source_rows"]) == 481
    assert all(
        (row["reason"] is None) if row["kept"] else bool(row["reason"])
        for row in meta["source_rows"].values()
    )
    assert len(projects["features"]) == 230
    assert len(overlaps) == 477
    assert [(pair["a"], pair["b"]) for pair in overlaps[:10]] == TOP_TEN


def test_reconciliation_rejects_a_missing_source_row() -> None:
    with pytest.raises(ValueError, match="source rows do not reconcile"):
        build_all.reconcile_rows(source_rows=3, kept=1, dropped_by_reason={"outside_area": 1})
