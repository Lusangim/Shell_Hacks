"""Runtime settings for the local GridLock server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    artifact_dir: Path = ROOT / "data" / "build"
    ai: Literal["off", "on"] = "off"
    port: int = 8765
    brief_cache_dir: Path = ROOT / "data" / "briefs"
    spend_ceiling_usd: Decimal = Decimal("0")
    max_ondemand: int = 5

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
        brief_cache_dir = Path(os.getenv("GRIDLOCK_BRIEF_CACHE_DIR", str(ROOT / "data" / "briefs")))
        try:
            ceiling = Decimal(os.getenv("GRIDLOCK_SPEND_CEILING_USD", "0"))
        except InvalidOperation as exc:
            raise ValueError("GRIDLOCK_SPEND_CEILING_USD must be a finite nonnegative dollar amount") from exc
        if not ceiling.is_finite() or ceiling < 0:
            raise ValueError("GRIDLOCK_SPEND_CEILING_USD must be a finite nonnegative dollar amount")
        try:
            max_ondemand = int(os.getenv("GRIDLOCK_MAX_ONDEMAND", "5"))
        except ValueError as exc:
            raise ValueError("GRIDLOCK_MAX_ONDEMAND must be between 0 and 100") from exc
        if not 0 <= max_ondemand <= 100:
            raise ValueError("GRIDLOCK_MAX_ONDEMAND must be between 0 and 100")
        return cls(
            artifact_dir=artifact_dir, ai=ai, port=port, brief_cache_dir=brief_cache_dir,
            spend_ceiling_usd=ceiling, max_ondemand=max_ondemand,
        )
