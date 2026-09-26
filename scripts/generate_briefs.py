"""Offline batch preflight. Real client wiring is reserved for approved F6."""

from __future__ import annotations

import argparse
import os
from decimal import Decimal, InvalidOperation
from typing import Literal


def main(argv: list[str] | None = None, *, ai_mode: Literal["off", "on"] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GridLock brief batch preflight")
    parser.add_argument("--access-approved", action="store_true")
    parser.add_argument("--ceiling-usd")
    args = parser.parse_args(argv)
    mode = ai_mode if ai_mode is not None else os.getenv("GRIDLOCK_AI", "off")
    if mode != "on":
        print("Brief batch refused: Claude access is disabled.")
        return 2
    if not args.access_approved:
        print("Brief batch refused: explicit Claude access approval is required.")
        return 2
    try:
        ceiling = Decimal(args.ceiling_usd) if args.ceiling_usd is not None else None
    except InvalidOperation:
        ceiling = None
    if ceiling is None or not ceiling.is_finite() or ceiling <= 0:
        print("Brief batch refused: a positive dollar ceiling is required.")
        return 2
    print("Brief batch refused: real client wiring awaits F6 SDK verification and founder approval.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
