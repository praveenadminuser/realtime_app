"""User endpoints. HTTP concerns only — validation is the schema's job, logic the
service's. This file's whole responsibility is mapping requests and exceptions to
status codes.

Adding a future endpoint (GET /users/{id}, login, ...) means adding a function here plus
a service call — no other file changes. That is the modular payoff.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from dependencies import get_current_active_user
from models import User
from schemas.user import UserCreate, UserRead
from services import user_service

# The prefix and tag live here, so main.py just includes the router without repeating them.
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead, summary="Current authenticated user")
async def read_current_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """A PROTECTED endpoint — the whole point of the auth layer. Depends on
    get_current_active_user, so an absent or invalid bearer token gets 401 before this
    body ever runs, and `current_user` is guaranteed to be a real, active user.

    Declared before "" isn't necessary here (no /{id} route yet), but /me must always
    precede any future /{user_id} route, or "me" would be parsed as an id.
    """
    return current_user


@router.post(
    "",
    response_model=UserRead,  # filters the ORM object down to safe fields — no password_hash
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register_user(
    payload: UserCreate, session: AsyncSession = Depends(get_session)
) -> UserRead:
    try:
        return await user_service.create_user(session, payload)
    except user_service.UserAlreadyExistsError as exc:
        # 409 Conflict is the correct code for a duplicate resource — not 400.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{exc.field} already registered",
        )