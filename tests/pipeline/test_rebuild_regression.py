"""Regression checks for the offline data-package rebuild."""

import hashlib
import json
from pathlib import Path

import pytest

from pipeline import build_all


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ("projects.geojson", "placement_report.csv", "overlaps.json", "meta.json", "source_rows.json")
TOP_TEN = [
    ("desc-p41", "sertp-p107-9bc088"),
    ("sertp-p68-a0289a", "sertp-p72-81610d"),
    ("desc-p41", "sertp-p111-fe1e3b"),
    ("desc-p41", "sertp-p113-5484a4"),
    ("sertp-p124-e36f41", "sertp-p133-9ca229"),
    ("sertp-p124-e36f41", "sertp-p133-a3bd5b"),
    ("sertp-p68-fbd1c0", "sertp-p72-81610d"),
    ("sertp-p72-81610d", "sertp-p72-eda876"),
    ("sertp-p82-5bdb2b", "sertp-p92-ade224"),
    ("sertp-p114-46d04f", "sertp-p124-e36f41"),
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
    ledger = json.loads((artifact / "source_rows.json").read_text(encoding="utf-8"))
    projects = json.loads((artifact / "projects.geojson").read_text(encoding="utf-8"))
    overlaps = json.loads((artifact / "overlaps.json").read_text(encoding="utf-8"))

    assert meta["stage_counts"]["source_rows"] == 481
    assert meta["stage_counts"]["placement_candidates"] == 380
    assert meta["stage_counts"]["kept"] == 230
    assert meta["stage_counts"]["placed"] == 181
    assert meta["stage_counts"]["overlaps"] == 489
    assert meta["stage_counts"]["cross_state"] == 43
    assert meta["stage_counts"]["source_rows"] == (
        meta["stage_counts"]["kept"] + sum(ledger["dropped_by_reason"].values())
    )
    assert len(ledger["rows"]) == 481
    assert all(
        (row["reason"] is None) if row["kept"] else bool(row["reason"])
        for row in ledger["rows"].values()
    )
    assert len(projects["features"]) == 230
    assert len(overlaps) == 489
    assert [(pair["a"], pair["b"]) for pair in overlaps[:10]] == TOP_TEN


def test_reconciliation_rejects_a_missing_source_row() -> None:
    with pytest.raises(ValueError, match="source rows do not reconcile"):
        build_all.reconcile_rows(source_rows=3, kept=1, dropped_by_reason={"outside_area": 1})
