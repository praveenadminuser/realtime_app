"""Auth endpoints. The login route that issues JWTs.

Uses OAuth2's "password" flow: the client POSTs username + password as FORM fields
(not JSON), and gets back a bearer token. Form encoding is what the OAuth2 spec
mandates and what OAuth2PasswordRequestForm parses — it needs python-multipart.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token
from db import get_session
from logger import logger
from schemas.auth import Token
from services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Token:
    user = await user_service.authenticate_user(
        session, form_data.username, form_data.password
    )
    if user is None:
        # ONE message for both "no such user" and "wrong password". Distinguishing them
        # would let an attacker enumerate valid usernames. The timing is equalised too
        # (see authenticate_user).
        logger.info(f"Failed login for username={form_data.username!r}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # `sub` is the user id as a string — JWT claims are strings by convention, and the
    # auth dependency casts it back to int to load the user.
    token = create_access_token(subject=str(user.id))
    logger.info(f"Issued token for user id={user.id}")
    return Token(access_token=token)
