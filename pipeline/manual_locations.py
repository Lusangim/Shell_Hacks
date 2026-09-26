"""Validate provenance on hand-placed coordinates before a data build."""

import csv
from math import isfinite
from pathlib import Path


REQUIRED = ("name", "lat", "lon", "source", "note")


def load_manual_locations(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or any(field not in reader.fieldnames for field in REQUIRED):
            raise ValueError("manual locations require name, lat, lon, source, and note columns")
        rows = []
        for number, row in enumerate(reader, 2):
            for field in REQUIRED:
                if not row.get(field) or not row[field].strip():
                    raise ValueError(f"manual location row {number} missing {field}")
            lat, lon = float(row["lat"]), float(row["lon"])
            if not (isfinite(lat) and isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"manual location row {number} has invalid coordinates")
            rows.append({field: row[field].strip() for field in REQUIRED})
    return rows
