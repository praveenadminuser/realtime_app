"""Message endpoints — and the example of WHERE a shared Redis cache goes.

The pattern is "read-through + invalidate-on-write":
  - GET checks Redis first; on a miss it queries the DB and populates Redis.
  - POST writes to the DB, then invalidates the cached list so the new row shows up.

This is the multi-pod-safe version of caching: because the cache lives in Redis, a POST on
pod A invalidates the entry that a GET on pod B would read. An in-process cache (lru/TTL)
couldn't do that — pod B would keep serving its own stale copy.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from redis_cache import cache_delete_pattern, cache_get_json, cache_set_json
from db import get_session
from dependencies import get_current_active_user
from logger import logger
from models import Message
from schemas.message import MessageCreate, MessageRead

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    dependencies=[Depends(get_current_active_user)],
)

# Keys look like "messages:list:limit=20". The prefix lets one DELETE pattern wipe every
# cached listing regardless of its limit.
_LIST_KEY_PREFIX = "messages:list:"


@router.post("", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(
    payload: MessageCreate, session: AsyncSession = Depends(get_session)
):
    message = Message(body=payload.body)
    session.add(message)
    await session.commit()
    await session.refresh(message)

    # Invalidate AFTER the DB commit. A new message means every cached listing is stale, so
    # drop them all; the next GET rebuilds from the DB. Order matters: commit first, then
    # invalidate — invalidate-then-commit would leave a window where a read re-caches the
    # OLD data before the write lands.
    await cache_delete_pattern(f"{_LIST_KEY_PREFIX}*")
    logger.info(f"Stored message id={message.id}, invalidated message list cache")
    return message


@router.get("", response_model=list[MessageRead])
async def list_messages(
    limit: int = 20, session: AsyncSession = Depends(get_session)
):
    cache_key = f"{_LIST_KEY_PREFIX}limit={limit}"

    # 1. Try the shared cache. A hit skips the DB entirely — and every pod hits the SAME
    #    Redis, so they all agree.
    cached = await cache_get_json(cache_key)
    if cached is not None:
        logger.info(f"messages served from Redis ({cache_key})")
        return cached

    # 2. Miss (or Redis down): read the source of truth.
    result = await session.execute(
        select(Message).order_by(Message.created_at.desc()).limit(limit)
    )
    messages = result.scalars().all()

    # 3. Serialise to JSON-safe dicts and populate the cache for next time. We cache the
    #    serialised form (datetime -> ISO string) so a hit needs no re-serialisation.
    payload = [MessageRead.model_validate(m).model_dump(mode="json") for m in messages]
    await cache_set_json(cache_key, payload)
    logger.info(f"messages read from DB and cached: {len(payload)} ({cache_key})")
    return payload
