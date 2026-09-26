"""Deterministic IDs derived only from a source row and its real PDF page."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence


def desc_id(page: int) -> str:
    if page < 1:
        raise ValueError("DESC source page must be positive")
    return f"desc-p{page}"


def _normalize(text: str) -> str:
    words = re.sub(r"[^\w]+", " ", unicodedata.normalize("NFKC", text).casefold())
    return " ".join(words.split())


def sertp_ids(rows: Sequence[Mapping[str, str]]) -> list[str]:
    """Suffix same-page hash collisions in source-document order."""
    seen: Counter[str] = Counter()
    result: list[str] = []
    for row in rows:
        page = int(row["source_page"])
        if page < 1:
            raise ValueError("SERTP source page must be positive")
        normalized = _normalize(row["project_name"]) + "\n" + _normalize(row["description"])
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:6]
        base = f"sertp-p{page}-{digest}"
        seen[base] += 1
        result.append(base if seen[base] == 1 else f"{base}-{seen[base]}")
    return result
