"""Local map assets; no network clients and no request-controlled file paths."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import BinaryIO, Iterator

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse, Response, StreamingResponse

from server.schemas import ErrorResponse


OFFLINE_CSP = "default-src 'self'"
GOOGLE_CSP = "; ".join((
    OFFLINE_CSP,
    "script-src 'self' https://maps.googleapis.com https://maps.gstatic.com",
    "connect-src 'self' https://maps.googleapis.com https://maps.gstatic.com",
    "img-src 'self' data: https://maps.googleapis.com https://maps.gstatic.com https://maps.google.com https://khms0.googleapis.com https://khms1.googleapis.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
))


class MapConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    google_enabled: bool
    google_key: str | None = Field(repr=False)
    offline_available: bool


def map_error(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    body = ErrorResponse.model_validate({"error": {"code": code, "message": message}})
    return JSONResponse(status_code=status, content=body.model_dump(), headers=headers)


def same_origin(request: Request) -> bool:
    """SOP/no CORS remains primary; reject explicit foreign browser context too."""
    origin = request.headers.get("origin")
    expected = f"{request.url.scheme}://{request.headers.get('host', '')}"
    return (
        (origin is None or origin == expected)
        and request.headers.get("sec-fetch-site", "none") in {"none", "same-origin"}
    )


def offline_available(path: Path) -> bool:
    try:
        return path.is_file()
    except OSError:
        return False


def byte_range(value: str, size: int) -> tuple[int, int]:
    """One bounded byte range; end and suffix lengths may exceed the file size."""
    match = re.fullmatch(r"bytes=([0-9]{0,20})-([0-9]{0,20})", value)
    if match is None or size == 0:
        raise ValueError("invalid range")
    first, last = match.groups()
    if not first:
        if not last or int(last) == 0:
            raise ValueError("invalid range")
        return max(0, size - int(last)), size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise ValueError("invalid range")
    return start, end


def _chunks(source: BinaryIO, length: int) -> Iterator[bytes]:
    with source:
        remaining = length
        while remaining:
            block = source.read(min(remaining, 64 * 1024))
            if not block:
                raise OSError("Offline basemap changed during transfer")
            remaining -= len(block)
            yield block


def archive_response(path: Path, range_header: str | None) -> Response:
    """Open the fixed file once, stream bounded chunks and close after transfer."""
    try:
        source = path.open("rb")
    except OSError:
        return map_error(404, "not_found", "Offline basemap not available")
    try:
        size = os.fstat(source.fileno()).st_size
        headers = {"Accept-Ranges": "bytes"}
        try:
            start, end = byte_range(range_header, size) if range_header is not None else (0, size - 1)
        except ValueError:
            source.close()
            headers["Content-Range"] = f"bytes */{size}"
            return map_error(416, "invalid_range", "Requested range not satisfiable", headers)
        length = end - start + 1
        source.seek(start)
        headers["Content-Length"] = str(length)
        if range_header is not None:
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        return StreamingResponse(
            _chunks(source, length), status_code=206 if range_header is not None else 200,
            media_type="application/vnd.pmtiles", headers=headers, background=BackgroundTask(source.close),
        )
    except OSError:
        source.close()
        return map_error(404, "not_found", "Offline basemap not available")
