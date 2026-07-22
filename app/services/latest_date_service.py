"""Cached reader for the latest-date file.

Serves {"latest_date": "yyyymmdd"} from an in-memory cache, re-reading the file from disk
only when EITHER condition holds:
  1. the TTL (default 5 min) has expired  — handled by cachetools.TTLCache, and
  2. the file's modification time changed  — handled by the mtime check below.

TTLCache gives us (1) for free: an entry vanishes once it's older than the ttl. (2) is the
"...or on file modification" half — a cheap stat() on every call spots an external update
and busts the cache before the TTL would.
"""
import json
import threading
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from cachetools import TTLCache

from config import settings
from logger import logger


class LatestDateError(Exception):
    """The file is missing, unreadable, not valid JSON, or lacks a string latest_date."""


# maxsize=1 — we cache exactly one payload. TTL from config (seconds).
_cache: TTLCache = TTLCache(maxsize=1, ttl=settings.latest_date_ttl_seconds)
_CACHE_KEY = "latest_date"

# FastAPI runs sync `def` endpoints in a THREADPOOL, so this function can be entered by
# several threads at once. TTLCache is NOT thread-safe, so every access goes through this
# lock. The critical section includes the (rare) file read — fine, since it's small and
# only happens on a miss.
_lock = threading.Lock()


def _read_file(path: Path) -> tuple[str, float]:
    """Return (latest_date, mtime) from disk, or raise LatestDateError."""
    try:
        mtime = path.stat().st_mtime
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LatestDateError(f"cannot read {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LatestDateError(f"invalid JSON in {path}: {exc}") from exc
    value = data.get("latest_date")
    if not isinstance(value, str):
        raise LatestDateError("'latest_date' missing or not a string")
    return value, mtime


def get_latest_date() -> dict:
    """Return the payload, from cache when possible. Keys: latest_date, mtime, loaded_at,
    source ("cache" | "file"). Raises LatestDateError on any file problem."""
    path = Path(settings.latest_date_file)

    with _lock:
        # Cheap stat on EVERY call so an external file change is noticed before the TTL.
        try:
            current_mtime = path.stat().st_mtime
        except OSError as exc:
            raise LatestDateError(f"cannot stat {path}: {exc}") from exc

        cached = _cache.get(_CACHE_KEY)
        # Serve from cache only if it's still present (TTL not expired) AND the file
        # hasn't changed underneath us.
        if cached is not None and cached["mtime"] == current_mtime:
            logger.info(f"latest_date returned from cache")
            return {**cached, "source": "cache"}

        # Miss: first call, TTL expired, or the file changed. Re-read.
        value, mtime = _read_file(path)
        entry = {
            "latest_date": value,
            "mtime": mtime,
            "loaded_at": datetime.now(timezone.utc),
        }
        _cache[_CACHE_KEY] = entry
        logger.info(f"latest_date re-read from {path}: {value}")
        return {**entry, "source": "file"}


# ---------------------------------------------------------------------------
# Per-date content files: data/dates/<yyyymmdd>.json
#
# Different caching problem, so a different tool. These files are IMMUTABLE — a past
# date's content doesn't change — and they're keyed by the date string. That's the exact
# shape functools.lru_cache is built for: a pure function of its argument.
#
# Why lru_cache here but TTLCache above:
#   - The value for a given date NEVER changes -> no TTL or mtime check needed.
#   - Keyed by date, bounded by maxsize -> memory stays O(maxsize) as dates pile up.
#   - lru_cache is thread-safe internally -> no manual lock (unlike TTLCache above).
#
# The trade-off, stated plainly: lru_cache has NO invalidation. If a date file is ever
# corrected in place, this serves the old content until the process restarts (or you call
# _read_date_file.cache_clear()). That's acceptable ONLY because we treat these files as
# write-once. If they could change, this would need the mtime pattern like latest_date.
# ---------------------------------------------------------------------------
@lru_cache(maxsize=settings.date_files_cache_size)
def _load_date_file(date_str: str) -> dict:
    """Read and parse data/dates/<date_str>.json. Cached by date_str; the body runs ONLY
    on a cache miss.

    ⚠️ Returns the SAME dict object on every cache hit — callers must treat it as
    read-only. Mutating it would corrupt the cached copy for everyone. We only serialise
    it into a response, so that's safe here.
    """
    path = Path(settings.date_files_dir) / f"{date_str}.json"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LatestDateError(f"cannot read date file {path}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LatestDateError(f"invalid JSON in {path}: {exc}") from exc


def _read_date_file(date_str: str) -> dict:
    """Thin wrapper around the lru_cache'd loader that LOGS hit/miss + elapsed ms.

    We can't log from inside _load_date_file: on a hit its body never runs. So we detect
    the outcome by diffing cache_info().hits across the call, and time the whole thing with
    perf_counter (a monotonic, high-resolution clock — the right one for durations).
    """
    hits_before = _load_date_file.cache_info().hits
    start = time.perf_counter()
    content = _load_date_file(date_str)  # runs the body only on a miss
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    info = _load_date_file.cache_info()
    # If the hit counter advanced, this call was served from memory; otherwise it read disk.
    outcome = "HIT" if info.hits > hits_before else "MISS"
    logger.info(
        f"date_file {date_str} {outcome} in {elapsed_ms:.3f} ms "
        f"(hits={info.hits} misses={info.misses} size={info.currsize}/{info.maxsize})"
    )
    return content


def get_latest_data() -> dict:
    """Chain both caches: the TTL-cached pointer tells us the current date, then the
    LRU-cached reader returns that date's (immutable) content."""
    meta = get_latest_date()             # TTLCache + mtime
    date_str = meta["latest_date"]
    content = _read_date_file(date_str)  # lru_cache + hit/miss/ms logging
    info = _load_date_file.cache_info()  # hits/misses/size — handy to expose
    return {
        "latest_date": date_str,
        "data": content,
        "cache": {
            "hits": info.hits,
            "misses": info.misses,
            "size": info.currsize,
            "maxsize": info.maxsize,
        },
    }


# Note (from earlier): this module-level cache + functions could equally be a singleton
# class with a static/class-level cache. Functionally identical; module globals ARE a
# singleton in Python (imported once), so the extra class buys little here.