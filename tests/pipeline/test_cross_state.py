"""Cross-state flags and scores must follow the projects' sourced states."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline import build_all


ROOT = Path(__file__).resolve().parents[2]
BUILT = ROOT / "data" / "build"
GA_PAIR_NOTE = "May already plan jointly through Georgia's Integrated Transmission System"


@pytest.fixture(scope="module")
def built_pairs() -> tuple[dict[str, dict], list[dict], dict]:
    build_all.build(ROOT)
    projects = json.loads((BUILT / "projects.geojson").read_text(encoding="utf-8"))
    overlaps = json.loads((BUILT / "overlaps.json").read_text(encoding="utf-8"))
    meta = json.loads((BUILT / "meta.json").read_text(encoding="utf-8"))
    by_id = {feature["properties"]["id"]: feature["properties"] for feature in projects["features"]}
    return by_id, overlaps, meta


def test_real_georgia_only_pair_has_no_cross_state_bonus_or_claim(built_pairs: tuple) -> None:
    projects, overlaps, _ = built_pairs
    pair = next(item for item in overlaps if item["id"] == "desc-p26__sertp-p150-ef263c")
    assert (projects[pair["a"]]["state"], projects[pair["b"]]["state"]) == ("GA", "GA")
    assert pair["cross_state"] is False
    assert pair["score"] == 0.064  # 1 band * 0.1 timeline * 0.8 * 0.8 accuracy
    assert pair["rank"] == 395
    assert pair["pair_note"] == GA_PAIR_NOTE


def test_real_sc_ga_pair_keeps_cross_state_bonus(built_pairs: tuple) -> None:
    projects, overlaps, _ = built_pairs
    pair = next(item for item in overlaps if item["id"] == "desc-p41__sertp-p107-9bc088")
    assert (projects[pair["a"]]["state"], projects[pair["b"]]["state"]) == ("SC", "GA")
    assert pair["cross_state"] is True
    assert pair["score"] == 4.8  # 4 band * 1 timeline * 0.8 accuracy * 1.5
    assert pair["pair_note"] is None


def test_every_built_pair_flag_and_count_match_sourced_states(built_pairs: tuple) -> None:
    projects, overlaps, meta = built_pairs
    assert len(overlaps) == 489
    for pair in overlaps:
        a_state, b_state = projects[pair["a"]]["state"], projects[pair["b"]]["state"]
        assert pair["cross_state"] is bool(a_state and b_state and a_state != b_state), pair["id"]
        if a_state == b_state == "GA":
            assert pair["pair_note"] == GA_PAIR_NOTE, pair["id"]
        else:
            assert pair["pair_note"] is None, pair["id"]
    assert sum(pair["cross_state"] for pair in overlaps) == meta["stage_counts"]["cross_state"] == 43


def test_missing_state_does_not_claim_cross_state_or_earn_bonus(tmp_path: Path) -> None:
    features = [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-81, 33]},
         "properties": {"id": "a", "name": "A", "utility": "Dominion Energy SC",
                        "state": None, "accuracy": "exact", "year": 2027}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-81, 33]},
         "properties": {"id": "b", "name": "B", "utility": "MEAG Power",
                        "state": "GA", "accuracy": "exact", "year": 2027}},
    ]
    (tmp_path / "projects.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )
    shutil.copyfile(ROOT / "data/manual/assumptions.json", tmp_path / "assumptions.json")
    subprocess.run([sys.executable, str(ROOT / "pipeline" / "find_overlaps.py")],
                   cwd=tmp_path, capture_output=True, text=True, check=True)
    pair = json.loads((tmp_path / "overlaps.json").read_text(encoding="utf-8"))[0]
    assert pair["cross_state"] is False
    assert pair["score"] == 4.0
    assert pair["pair_note"] is None
    assert pair["savings"]["status"] == "no_cost"
