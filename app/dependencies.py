"""Reusable FastAPI dependencies for authentication.

`get_current_user` is the gate every protected endpoint sits behind:

    @router.get("/me")
    async def me(user: User = Depends(get_current_active_user)):
        ...

Depending on it does three things at once — extracts the bearer token, validates it,
and loads the user — so endpoints stay free of auth plumbing.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_access_token
from db import get_session
from models import User
from services import user_service

# tokenUrl is the endpoint that ISSUES tokens. It does two things: it tells Swagger UI
# where its "Authorize" button should POST, and it documents the flow in the OpenAPI
# schema. It is a path relative to the app root — the same /auth/login the router mounts.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Bearer token -> User. Raises 401 if the token is missing, invalid, expired, or
    points at a user who no longer exists."""
    # WWW-Authenticate: Bearer is required by the OAuth2 spec on a 401 for this scheme.
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    claims = decode_access_token(token)
    if claims is None:
        raise credentials_error

    subject = claims.get("sub")
    if subject is None:
        raise credentials_error

    # The token proves WHO the caller is, but the user could have been deleted or the
    # id could be garbage — so we still load from the database and 401 if absent.
    user = await user_service.get_by_id(session, int(subject))
    if user is None:
        raise credentials_error
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """As above, but also refuses disabled accounts. Use this for real endpoints; a
    soft-deleted (is_active=False) user holding a still-valid token gets 403 here."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user
