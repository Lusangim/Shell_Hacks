"""Content hashes identify source data, independent of checkout line endings."""

from pathlib import Path

from pipeline import build_all


def test_source_hash_canonicalizes_text_line_endings_but_preserves_content(
    tmp_path: Path, monkeypatch,
) -> None:
    raw = tmp_path / "raw"
    manual = tmp_path / "manual"
    raw.mkdir()
    manual.mkdir()
    monkeypatch.setattr(build_all, "RAW_INPUTS", ("desc.csv", "shapes.geojson", "original.pdf"))
    (raw / "desc.csv").write_bytes(b"id,name\n1,McIntosh\n")
    (raw / "shapes.geojson").write_bytes(b'{"type":"FeatureCollection",\n"features":[]}\n')
    (raw / "original.pdf").write_bytes(b"PDF\r\nbytes")
    (manual / "manual_locations.csv").write_bytes(b"name,lat,lon\nA,1,2\n")
    (manual / "unit_costs_2026.csv").write_bytes(b"item,rate\nyard,0.4\n")
    first = build_all._input_hash(raw, manual)

    (raw / "desc.csv").write_bytes(b"id,name\r\n1,McIntosh\r\n")
    (raw / "shapes.geojson").write_bytes(b'{"type":"FeatureCollection",\r\n"features":[]}\r\n')
    (manual / "manual_locations.csv").write_bytes(b"name,lat,lon\r\nA,1,2\r\n")
    assert build_all._input_hash(raw, manual) == first

    (raw / "desc.csv").write_bytes(b"id,name\r\n1,Other\r\n")
    assert build_all._input_hash(raw, manual) != first

    (raw / "desc.csv").write_bytes(b"id,name\r\n1,McIntosh\r\n")
    (raw / "original.pdf").write_bytes(b"PDF\nbytes")
    assert build_all._input_hash(raw, manual) != first

    (raw / "original.pdf").write_bytes(b"PDF\r\nbytes")
    (manual / "unit_costs_2026.csv").write_bytes(b"item,rate\nyard,0.5\n")
    assert build_all._input_hash(raw, manual) != first
