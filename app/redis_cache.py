"""Shared Redis cache.

Why this exists: lru_cache and TTLCache live INSIDE one Python process, so N pods means N
independent caches that drift — pod A can serve a value pod B has already invalidated.
Redis is a SEPARATE service every pod connects to, so all replicas share one cache and see
the same data. That's the whole reason to reach for it. See REDIS.md.

Design rule enforced here: **Redis is an optimization, never a hard dependency for reads.**
Every operation is wrapped so a Redis outage degrades to a cache miss (the caller then hits
the database) instead of failing the request. A cache that can take your app down is worse
than no cache.

We use redis.asyncio: non-blocking, so it fits FastAPI's async endpoints directly — no
threadpool needed (unlike the file caches).
"""
import json
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from config import settings
from logger import logger

# One client (and its connection pool) per process, shared by all requests. Created lazily
# on first use and reused — opening a connection per request would defeat the point.
_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        # decode_responses=True → we get str back, not bytes, so json.loads works directly.
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def cache_get_json(key: str) -> Any | None:
    """Return the cached value, or None on a miss OR if Redis is unavailable.

    A Redis error is logged and treated as a miss — the caller falls through to the source
    of truth (the DB). The request still succeeds, just without the cache speed-up.
    """
    try:
        raw = await get_client().get(key)
    except RedisError as exc:
        logger.warning(f"redis GET failed for {key}: {exc} — treating as miss")
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(f"corrupt cache value at {key} — treating as miss")
        return None


async def cache_set_json(key: str, value: Any, ttl: int | None = None) -> None:
    """Store value as JSON with an expiry. Best-effort: a failure is logged, not raised —
    failing to WRITE the cache must never fail the request that produced the data."""
    try:
        await get_client().set(
            key,
            json.dumps(value, default=str),  # default=str handles datetime, etc.
            ex=ttl if ttl is not None else settings.cache_ttl_seconds,
        )
    except RedisError as exc:
        logger.warning(f"redis SET failed for {key}: {exc}")


async def cache_delete_pattern(pattern: str) -> None:
    """Invalidate every key matching a glob (e.g. "messages:list:*"). Used on writes so the
    next read re-populates from the DB.

    scan_iter is cursor-based and non-blocking — it won't stall Redis the way the old KEYS
    command does. Fine for modest keyspaces; for millions of keys prefer a version-bump
    strategy (see REDIS.md) over pattern deletes.
    """
    try:
        client = get_client()
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)
    except RedisError as exc:
        logger.warning(f"redis invalidate failed for {pattern}: {exc}")


async def ping() -> bool:
    """True if Redis answers. Used at startup to log reachability (not to fail boot)."""
    try:
        return bool(await get_client().ping())
    except RedisError as exc:
        logger.warning(f"redis ping failed: {exc}")
        return False


async def close() -> None:
    """Release the connection pool on shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
