"""Content keyed JSON brief cache with local atomic publication."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from collections.abc import Collection
from pathlib import Path
from threading import Lock

from pydantic import ValidationError

from server.schemas import Brief, Overlap, ProjectFeature


_SAFE_ID = re.compile(r"[a-z0-9-]+__[a-z0-9-]+\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
# Windows can deny two simultaneous replacements of one target. Serialize only
# publication; each writer still prepares a private temporary file.
_PUBLISH_LOCK = Lock()


def structured_input(
    pair: Overlap,
    project_a: ProjectFeature,
    project_b: ProjectFeature,
    contacts: Collection[str],
) -> dict[str, object]:
    """One canonical set of public contract fields for the prompt and cache key."""
    if (project_a.properties.id, project_b.properties.id) != (pair.a, pair.b):
        raise ValueError("Projects do not match overlap IDs")
    return {
        "overlap": pair.model_dump(mode="json", exclude={"brief_status"}),
        "project_a": project_a.model_dump(mode="json"),
        "project_b": project_b.model_dump(mode="json"),
        "contacts": sorted(set(contacts)),
    }


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def cache_key(
    pair: Overlap,
    project_a: ProjectFeature,
    project_b: ProjectFeature,
    contacts: Collection[str],
    prompt_version: str,
    model_id: str,
) -> str:
    payload = {
        "input": structured_input(pair, project_a, project_b, contacts),
        "prompt_version": prompt_version,
        "model_id": model_id,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def cache_path(directory: Path, overlap_id: str) -> Path:
    """Reject any ID that could escape the injected cache directory."""
    if not _SAFE_ID.fullmatch(overlap_id):
        raise ValueError("Invalid overlap ID for cache path")
    root = directory.resolve()
    path = (root / f"{overlap_id}.json").resolve()
    if path.parent != root:
        raise ValueError("Cache path escapes directory")
    return path


def load_cached_brief(
    directory: Path,
    overlap_id: str,
    expected_key: str,
    *,
    model_id: str | None = None,
    prompt_version: str | None = None,
) -> Brief | None:
    """Treat missing, corrupt and stale entries as misses; callers still grade hits."""
    path = cache_path(directory, overlap_id)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if document["cache_key"] != expected_key:
            return None
        brief = Brief.model_validate(document["brief"])
    except (OSError, UnicodeError, ValueError, RecursionError, KeyError, TypeError, ValidationError):
        return None
    if brief.overlap_id != overlap_id or brief.input_hash != expected_key:
        return None
    if model_id is not None and brief.generated_by != model_id:
        return None
    if prompt_version is not None and brief.prompt_version != prompt_version:
        return None
    return brief


def write_cached_brief(directory: Path, brief: Brief) -> Path:
    """Publish an already graded model brief; each writer has a unique same-dir temp file."""
    validated = Brief.model_validate(brief.model_dump(mode="json"))
    if validated.generated_by == "template" or not _SHA256.fullmatch(validated.input_hash):
        raise ValueError("Only a content keyed model brief can be cached")
    path = cache_path(directory, validated.overlap_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {"cache_key": validated.input_hash, "brief": validated.model_dump(mode="json")}
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=f".{validated.overlap_id}.", suffix=".tmp", delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(canonical_json(document) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        with _PUBLISH_LOCK:
            for attempt in range(10):
                try:
                    os.replace(temp_path, path)
                    break
                except PermissionError:
                    if attempt == 9:
                        raise
                    time.sleep(0.02 * (attempt + 1))
        return path
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
