"""Runtime settings for the local GridLock server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


ROOT = Path(__file__).resolve().parents[1]


def _google_key_from_env() -> str | None:
    """Read only after explicit enablement; a missing key disables Google maps."""
    key = os.getenv("GRIDLOCK_GOOGLE_MAPS_KEY")
    if not key:
        path = Path(os.getenv("GRIDLOCK_GOOGLE_MAPS_KEY_FILE", str(Path.home() / "dev" / "gridlock-assets" / "google-maps-key.txt")))
        try:
            with path.open("r", encoding="utf-8") as source:
                key = source.read(257)
        except (OSError, UnicodeError):
            return None
    key = key.strip()
    if not key or len(key) > 256 or not all(char.isascii() and (char.isalnum() or char in "-_") for char in key):
        return None
    return key


@dataclass(frozen=True)
class Settings:
    artifact_dir: Path = ROOT / "data" / "build"
    ai: Literal["off", "on"] = "off"
    port: int = 8765
    basemap_pmtiles: Path = Path.home() / "dev" / "gridlock-assets" / "gasc-z13.pmtiles"
    google: Literal["off", "on"] = "off"
    google_key: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> Settings:
        """Read configuration only when an app or CLI is started."""
        ai = os.getenv("GRIDLOCK_AI", "off")
        if ai not in ("off", "on"):
            raise ValueError("GRIDLOCK_AI must be 'off' or 'on'")
        google = os.getenv("GRIDLOCK_GOOGLE", "off")
        if google not in ("off", "on"):
            raise ValueError("GRIDLOCK_GOOGLE must be 'off' or 'on'")
        port_text = os.getenv("GRIDLOCK_TEST_PORT")
        port = int(port_text) if port_text else 8765
        if not 1 <= port <= 65535:
            raise ValueError("GRIDLOCK_TEST_PORT must be between 1 and 65535")
        artifact_dir = Path(os.getenv("GRIDLOCK_ARTIFACT_DIR", str(ROOT / "data" / "build")))
        basemap_pmtiles = Path(os.getenv("GRIDLOCK_BASEMAP_PMTILES", str(Path.home() / "dev" / "gridlock-assets" / "gasc-z13.pmtiles")))
        return cls(
            artifact_dir=artifact_dir, ai=ai, port=port, basemap_pmtiles=basemap_pmtiles,
            google=google, google_key=_google_key_from_env() if google == "on" else None,
        )
