"""Message endpoints. Moved out of main.py as part of modularising — same behaviour,
now grouped with its own schema.

These still talk to the ORM directly (no service layer) because the logic is trivial.
When it stops being trivial, lift it into services/message_service.py exactly as the
user endpoints do — the router shouldn't grow business logic.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from logger import logger
from models import Message
from schemas.message import MessageCreate, MessageRead
from dependencies import get_current_active_user

router = APIRouter(prefix="/messages", tags=["messages"], dependencies=[Depends(get_current_active_user)])


@router.post("", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(
    payload: MessageCreate, session: AsyncSession = Depends(get_session)
):
    message = Message(body=payload.body)
    session.add(message)
    await session.commit()
    await session.refresh(message)  # fetch id + created_at that Postgres filled in
    logger.info(f"Stored message id={message.id}")
    return message


@router.get("", response_model=list[MessageRead])
async def list_messages(
    limit: int = 20, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Message).order_by(Message.created_at.desc()).limit(limit)
    )
    messages = result.scalars().all()
    logger.info(f"Returned {len(messages)} messages")
    return messages