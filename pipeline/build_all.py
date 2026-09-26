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
from math import isfinite
from pathlib import Path

from pipeline.ids import desc_id, sertp_ids


RAW_INPUTS = (
    "desc_2026_2030_projects.csv",
    "sertp_2025_projects.csv",
    "osm_substations_sc_ga.json",
    "hifld_lines_ga_sc.geojson",
    "us_states.geojson",
    "places_se.csv",
)
BUILD_OUTPUTS = (
    "projects.geojson", "placement_report.csv", "overlaps.json", "source_rows.json",
    "places.json", "basemap.json",
)


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
    expected = {desc_id(i) for i in range(1, len(desc) + 1)}
    sertp_row_ids = sertp_ids(sertp)
    expected.update(
        row_id
        for row, row_id in zip(sertp, sertp_row_ids)
        if row["utility_area"] == "SOUTHERN"
    )
    by_id = {row["id"]: row for row in placement}
    if len(by_id) != len(placement) or set(by_id) != expected:
        raise ValueError("source rows do not reconcile: placement report is incomplete or duplicated")

    rows: dict[str, dict[str, str | bool | None]] = {}
    for i in range(1, len(desc) + 1):
        row_id = desc_id(i)
        rows[row_id] = _placement_disposition(by_id[row_id])
    for source, row_id in zip(sertp, sertp_row_ids):
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
        content = path.read_bytes()
        if path.suffix.lower() in {".csv", ".json", ".geojson", ".txt"}:
            content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        digest.update(content)
    return digest.hexdigest()


def _places(raw: Path) -> list[dict[str, str | float]]:
    """Keep each GA/SC Census place and its published coordinate verbatim."""
    places: list[dict[str, str | float]] = []
    for row in _csv_rows(raw / "places_se.csv"):
        if row["state"] not in {"GA", "SC"}:
            continue
        lat, lon = float(row["lat"]), float(row["lon"])
        if not isfinite(lat) or not isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"invalid Census place coordinate: {row['state']} {row['name']}")
        places.append({"state": row["state"], "name": row["name"], "lat": lat, "lon": lon})
    return places


def _basemap(raw: Path, places: list[dict[str, str | float]]) -> dict[str, object]:
    states = _load_json(raw / "us_states.geojson")
    outlines = []
    for feature in states["features"]:
        name = feature["properties"]["name"]
        if name in {"Georgia", "South Carolina"}:
            if not feature.get("geometry"):
                raise ValueError(f"missing state geometry: {name}")
            outlines.append({"type": "Feature", "properties": {"kind": "state_outline", "name": name},
                             "geometry": feature["geometry"]})
    if {feature["properties"]["name"] for feature in outlines} != {"Georgia", "South Carolina"}:
        raise ValueError("both GA and SC outlines are required for the local basemap")
    labels = [
        {"type": "Feature", "properties": {"kind": "city_label", "name": place["name"],
                                             "state": place["state"]},
         "geometry": {"type": "Point", "coordinates": [place["lon"], place["lat"]]}}
        for place in places if str(place["name"]).endswith((" city", " town"))
    ]
    return {"type": "FeatureCollection", "features": outlines + labels}


def _unmapped_reasons(placement: list[dict[str, str]]) -> dict[str, int]:
    reasons: Counter[str] = Counter()
    for row in placement:
        if row["accuracy"] != "unknown":
            continue
        if row["kept"] == "True":
            reason = "kept_not_located"
        elif row["kept"] == "False" and row["utility"] == "Southern Company":
            reason = "unprefixed_southern_not_located"
        elif row["kept"] == "False" and row["utility"] == "PowerSouth":
            reason = "powersouth_not_located_excluded"
        else:
            raise ValueError(f"unmapped source row has no truthful reason: {row['id']}")
        reasons[reason] += 1
    return dict(sorted(reasons.items()))


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
        places = _places(raw)
        basemap = _basemap(raw, places)
        unmapped_reasons = _unmapped_reasons(placement)
        unmapped = sum(unmapped_reasons.values())
        if unmapped != sum(row["accuracy"] == "unknown" for row in placement):
            raise ValueError("unmapped source rows do not reconcile")
        stage_counts = {
            "source_rows": len(rows),
            "placement_candidates": len(placement),
            "kept": kept,
            "placed": placed,
            "unmapped": unmapped,
            "kept_unmapped": kept - placed,
            "dropped_unmapped": unmapped - (kept - placed),
            "overlaps": len(overlaps),
            "cross_state": sum(bool(pair["cross_state"]) for pair in overlaps),
            "places": len(places),
            "state_outlines": 2,
            "city_labels": len(basemap["features"]) - 2,
        }
        stage_counts.update({f"dropped_{reason}": count for reason, count in dropped.items()})
        meta: dict[str, object] = {
            "build_time": None,
            "source_documents": [
                {"doc": "SCRTP Planned Facilities 2026-2030 $2M & Above", "date": None,
                 "url": "https://www.scrtp.com/assets/pdfs/home/2026-2030-2million-and-above-project-descriptions.pdf"},
                {"doc": "SERTP 2025 Regional Transmission Plan (Nov 26 2025)", "date": "2025-11-26",
                 "url": "https://www.southeasternrtp.com/docs/general/2025/2025%20Regional%20Transmission%20Plan%20and%20Input%20Assumptions.pdf"},
            ],
            "stage_counts": stage_counts,
            "counts_by_utility": dict(sorted(Counter(f["properties"]["utility"] for f in features).items())),
            "counts_by_accuracy": dict(sorted(Counter(f["properties"]["accuracy"] for f in features).items())),
            "counts_by_band": dict(sorted(Counter(pair["band"] for pair in overlaps).items())),
            "no_overlap_count": len(feature_ids - pair_ids),
            "unmapped_count": unmapped,
            "unmapped_reasons": unmapped_reasons,
            "stale_brief_count": 0,
        }
        (stage / "source_rows.json").write_text(
            json.dumps({"input_sha256": _input_hash(raw, manual), "rows": rows,
                        "dropped_by_reason": dict(sorted(dropped.items()))},
                       ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        (stage / "places.json").write_text(
            json.dumps(places, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        (stage / "basemap.json").write_text(
            json.dumps(basemap, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
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
    print(json.dumps(meta["stage_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
