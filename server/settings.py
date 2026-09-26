"""Runtime settings for the local GridLock server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    artifact_dir: Path = ROOT / "data" / "build"
    ai: Literal["off", "on"] = "off"
    port: int = 8765

    @classmethod
    def from_env(cls) -> Settings:
        """Read configuration only when an app or CLI is started."""
        ai = os.getenv("GRIDLOCK_AI", "off")
        if ai not in ("off", "on"):
            raise ValueError("GRIDLOCK_AI must be 'off' or 'on'")
        port_text = os.getenv("GRIDLOCK_TEST_PORT")
        port = int(port_text) if port_text else 8765
        if not 1 <= port <= 65535:
            raise ValueError("GRIDLOCK_TEST_PORT must be between 1 and 65535")
        artifact_dir = Path(os.getenv("GRIDLOCK_ARTIFACT_DIR", str(ROOT / "data" / "build")))
        return cls(artifact_dir=artifact_dir, ai=ai, port=port)
