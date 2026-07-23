"""Response contracts for the latest-date endpoints."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class LatestDateResponse(BaseModel):
    latest_date: str  # the value from the file, "yyyymmdd"
    # "cache" if served from memory, "file" if the file was just (re)read. Handy for
    # SEEING the cache work: hit the endpoint twice quickly and the second says "cache".
    source: str
    loaded_at: datetime       # when the file was last read into the cache (UTC)
    file_modified_at: datetime  # the file's mtime (UTC) — changes bust the cache early


class CacheInfo(BaseModel):
    hits: int
    misses: int
    size: int
    maxsize: int | None


class LatestDataResponse(BaseModel):
    latest_date: str
    # The per-date file's content. `Any` because these files are free-form JSON — the
    # cache doesn't care about their shape.
    data: Any
    # lru_cache stats for the per-date reader — lets you watch hits climb across calls.
    cache: CacheInfo