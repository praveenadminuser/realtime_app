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
from dependencies import get_current_active_user
from logger import logger
from models import User
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


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)) -> dict:
    """Log out the current user.

    ⚠️ Read this — it's a real JWT gotcha, not a stub by accident. A JWT is STATELESS:
    the server stores nothing when it issues one, so there is nothing here to delete to
    "end the session." The token stays cryptographically valid until its `exp`. The
    ACTUAL logout happens on the CLIENT, which discards the token so it stops sending it.

    So why have this endpoint at all?
      - It's the honest place for the client to call, and the hook where real revocation
        will live later.
      - Requiring a valid token (the Depends) makes it an authenticated action we can log
        and, in future, audit.

    To make logout truly revoke server-side you need a denylist of token ids (a `jti`
    claim) checked on every request. Note an IN-MEMORY denylist breaks the moment you run
    more than one replica — each pod has its own memory — so it must be shared (Redis/DB),
    which is exactly the statefulness JWTs were chosen to avoid. That trade-off is why
    short token lifetimes (30 min) are the pragmatic answer for now. See AUTH.md.
    """
    logger.info(f"User id={current_user.id} logged out (client discards token)")
    return {"detail": "Logged out"}
