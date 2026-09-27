"""Download GridLock's modern offline base map (OpenStreetMap via Protomaps) for Georgia and South Carolina.

Usage:
    python scripts/get_map.py            download the map if it is missing
    python scripts/get_map.py --force    download it again
    python scripts/get_map.py --dry-run  report the download size only

It fetches Protomaps' official `pmtiles` tool (go-pmtiles, pinned version) and uses it to cut the
Georgia + South Carolina area (zoom 0-13, about 220 MB) out of the latest public Protomaps build.
The file goes where the GridLock server looks for it: ~/dev/gridlock-assets/gasc-z13.pmtiles
(on Windows %USERPROFILE%\\dev\\gridlock-assets\\gasc-z13.pmtiles), or GRIDLOCK_BASEMAP_PMTILES if set.
Map data (c) OpenStreetMap contributors (ODbL); tiles by Protomaps.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

PMTILES_VERSION = "1.31.2"
BUILDS_URL = "https://build-metadata.protomaps.dev/builds.json"
BUILD_BASE = "https://build.protomaps.com/"
BBOX = "-85.7,30.3,-78.4,35.3"  # Georgia + South Carolina
MAXZOOM = 13
MIN_BYTES = 100_000_000  # a complete GA + SC extract is about 220 MB
KNOWN_SHA256 = {
    "go-pmtiles_1.31.2_Windows_x86_64.zip": "a658baa4d7e55020aef6ca17bd9ff9faa1582671266b36f58c52db0ac8e785a1",
}


def target_path() -> Path:
    configured = os.environ.get("GRIDLOCK_BASEMAP_PMTILES")
    if configured:
        return Path(configured)
    return Path.home() / "dev" / "gridlock-assets" / "gasc-z13.pmtiles"


def release_asset() -> str:
    system = platform.system()
    arch = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x86_64"
    if system == "Windows":
        return f"go-pmtiles_{PMTILES_VERSION}_Windows_{arch}.zip"
    if system == "Darwin":
        return f"go-pmtiles-{PMTILES_VERSION}_Darwin_{arch}.zip"
    if system == "Linux":
        return f"go-pmtiles_{PMTILES_VERSION}_Linux_{arch}.tar.gz"
    raise SystemExit(f"Unsupported system for the pmtiles tool: {system}")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "gridlock-setup"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def pmtiles_tool(tools: Path) -> Path:
    executable = tools / ("pmtiles.exe" if platform.system() == "Windows" else "pmtiles")
    if executable.exists():
        return executable
    asset = release_asset()
    url = f"https://github.com/protomaps/go-pmtiles/releases/download/v{PMTILES_VERSION}/{asset}"
    print(f"Downloading Protomaps' pmtiles tool: {url}")
    data = fetch(url)
    digest = hashlib.sha256(data).hexdigest()
    expected = KNOWN_SHA256.get(asset)
    if expected and digest != expected:
        raise SystemExit(f"Checksum mismatch for {asset}: got {digest}, expected {expected}")
    print(f"  sha256 {digest}")
    tools.mkdir(parents=True, exist_ok=True)
    if asset.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            member = next(name for name in archive.namelist() if Path(name).name in ("pmtiles", "pmtiles.exe"))
            executable.write_bytes(archive.read(member))
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            member = next(item for item in archive.getmembers() if Path(item.name).name == "pmtiles")
            extracted = archive.extractfile(member)
            if extracted is None:
                raise SystemExit(f"Could not read the pmtiles tool from {asset}")
            executable.write_bytes(extracted.read())
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return executable


def latest_build() -> str:
    builds = json.loads(fetch(BUILDS_URL))
    return builds[-1]["key"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Download GridLock's modern offline base map for GA + SC.")
    parser.add_argument("--force", action="store_true", help="download again even if the map file exists")
    parser.add_argument("--dry-run", action="store_true", help="report the download size without downloading")
    args = parser.parse_args()

    target = target_path()
    if target.exists() and target.stat().st_size > MIN_BYTES and not (args.force or args.dry_run):
        print(f"Modern map already present: {target} ({target.stat().st_size:,} bytes)")
        return 0

    tool = pmtiles_tool(target.parent / "tools")
    build = latest_build()
    print(f"Latest public Protomaps build: {build}")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    command = [str(tool), "extract", BUILD_BASE + build, str(partial), f"--bbox={BBOX}", f"--maxzoom={MAXZOOM}"]
    if args.dry_run:
        command.append("--dry-run")
    print("Cutting Georgia + South Carolina out of the world map (about 220 MB)...")
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print("The map download failed; the app still runs with its plain fallback map.")
        return result.returncode
    if args.dry_run:
        return 0
    size = partial.stat().st_size
    if size < MIN_BYTES:
        partial.unlink(missing_ok=True)
        raise SystemExit(f"The downloaded map looks incomplete ({size:,} bytes); run again with --force.")
    os.replace(partial, target)
    print(f"Modern map ready: {target} ({size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
