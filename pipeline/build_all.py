"""Rebuild committed map artifacts from local public data without network access."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


RAW_INPUTS = (
    "desc_2026_2030_projects.csv",
    "sertp_2025_projects.csv",
    "osm_substations_sc_ga.json",
    "hifld_lines_ga_sc.geojson",
    "us_states.geojson",
    "places_se.csv",
)
BUILD_OUTPUTS = ("projects.geojson", "placement_report.csv", "overlaps.json")


def reconcile_rows(source_rows: int, kept: int, dropped_by_reason: dict[str, int]) -> None:
    """Reject an unaccounted source row instead of silently losing it."""
    if any(not reason or count < 0 for reason, count in dropped_by_reason.items()):
        raise ValueError("source rows do not reconcile: invalid drop reason or count")
    if source_rows != kept + sum(dropped_by_reason.values()):
        raise ValueError("source rows do not reconcile")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _run_script(script: Path, cwd: Path) -> None:
    subprocess.run([sys.executable, str(script)], cwd=cwd, check=True)


def _row_dispositions(
    desc: list[dict[str, str]],
    sertp: list[dict[str, str]],
    placement: list[dict[str, str]],
    feature_ids: set[str],
) -> dict[str, dict[str, str | bool | None]]:
    expected = {f"DESC-{i:02d}" for i in range(1, len(desc) + 1)}
    expected.update(
        f"SERTP-{i:03d}"
        for i, row in enumerate(sertp, 1)
        if row["utility_area"] == "SOUTHERN"
    )
    by_id = {row["id"]: row for row in placement}
    if len(by_id) != len(placement) or set(by_id) != expected:
        raise ValueError("source rows do not reconcile: placement report is incomplete or duplicated")

    rows: dict[str, dict[str, str | bool | None]] = {}
    for i in range(1, len(desc) + 1):
        rows[f"DESC-{i:02d}"] = _placement_disposition(by_id[f"DESC-{i:02d}"])
    for i, source in enumerate(sertp, 1):
        row_id = f"SERTP-{i:03d}"
        rows[row_id] = (
            _placement_disposition(by_id[row_id])
            if source["utility_area"] == "SOUTHERN"
            else {"kept": False, "reason": "outside_selected_balancing_area"}
        )

    kept_ids = {row_id for row_id, disposition in rows.items() if disposition["kept"]}
    if kept_ids != feature_ids:
        raise ValueError("source rows do not reconcile: kept rows differ from project features")
    return rows


def _placement_disposition(row: dict[str, str]) -> dict[str, str | bool | None]:
    if row["kept"] == "True":
        return {"kept": True, "reason": None}
    if row["kept"] != "False":
        raise ValueError(f"source rows do not reconcile: invalid kept flag for {row['id']}")
    if row["utility"] == "PowerSouth":
        reason = "powersouth_excluded"
    elif row["state"] == "?":
        reason = "unlocated_outside_selected_area"
    elif row["state"] != "GA":
        reason = "outside_ga_sc_footprint"
    else:
        raise ValueError(f"source rows do not reconcile: unexplained drop for {row['id']}")
    return {"kept": False, "reason": reason}


def _input_hash(raw: Path, manual: Path) -> str:
    digest = hashlib.sha256()
    for path in [*(raw / name for name in RAW_INPUTS), manual / "manual_locations.csv"]:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build(root: Path) -> dict[str, object]:
    """Stage a complete rebuild, validate every row, then replace output files."""
    root = root.resolve()
    raw, manual, output = root / "data" / "raw", root / "data" / "manual", root / "data" / "build"
    output.mkdir(parents=True, exist_ok=True)
    scripts = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix=".stage-", dir=output) as temporary:
        stage = Path(temporary)
        for name in RAW_INPUTS:
            shutil.copyfile(raw / name, stage / name)
        shutil.copyfile(manual / "manual_locations.csv", stage / "manual_locations.csv")
        _run_script(scripts / "place_projects.py", stage)
        _run_script(scripts / "find_overlaps.py", stage)

        desc = _csv_rows(raw / "desc_2026_2030_projects.csv")
        sertp = _csv_rows(raw / "sertp_2025_projects.csv")
        placement = _csv_rows(stage / "placement_report.csv")
        projects = _load_json(stage / "projects.geojson")
        overlaps = _load_json(stage / "overlaps.json")
        features = projects["features"]
        feature_ids = {feature["properties"]["id"] for feature in features}
        if len(feature_ids) != len(features):
            raise ValueError("source rows do not reconcile: duplicate project feature ID")
        rows = _row_dispositions(desc, sertp, placement, feature_ids)
        dropped = Counter(str(item["reason"]) for item in rows.values() if not item["kept"])
        kept = len(feature_ids)
        reconcile_rows(len(desc) + len(sertp), kept, dict(dropped))

        placed = sum(feature["geometry"] is not None for feature in features)
        pair_ids = {project_id for pair in overlaps for project_id in (pair["a"], pair["b"])}
        if not pair_ids.issubset(feature_ids):
            raise ValueError("overlap references a project outside the kept rows")
        meta: dict[str, object] = {
            "build_time": None,
            "input_sha256": _input_hash(raw, manual),
            "source_documents": [
                {"file": "desc_scrtp_2026_2030.pdf", "date": None},
                {"file": "sertp_2025_rtp.pdf", "date": "2025-11-26"},
            ],
            "stages": {
                "source_rows": len(rows),
                "placement_candidates": len(placement),
                "kept": kept,
                "placed": placed,
                "unmapped": kept - placed,
                "overlaps": len(overlaps),
                "cross_state": sum(bool(pair["cross_state"]) for pair in overlaps),
            },
            "dropped_by_reason": dict(sorted(dropped.items())),
            "source_rows": rows,
            "counts_by_utility": dict(sorted(Counter(f["properties"]["utility"] for f in features).items())),
            "counts_by_accuracy": dict(sorted(Counter(f["properties"]["accuracy"] for f in features).items())),
            "counts_by_band": dict(sorted(Counter(pair["band"] for pair in overlaps).items())),
            "no_overlap_count": len(feature_ids - pair_ids),
            "unmapped_count": kept - placed,
            "stale_brief_count": 0,
        }
        (stage / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        for name in (*BUILD_OUTPUTS, "meta.json"):
            os.replace(stage / name, output / name)
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="refresh public HIFLD download before rebuilding")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.refresh:
        _run_script(Path(__file__).resolve().parent / "fetch_hifld.py", root / "data" / "raw")
    meta = build(root)
    print(json.dumps(meta["stages"], sort_keys=True))


if __name__ == "__main__":
    main()
