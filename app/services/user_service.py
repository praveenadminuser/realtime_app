"""User business logic and database access.

The router calls into here and never touches the ORM directly. That separation is what
lets the same logic be reused later — a CLI command, a bulk importer, or a login flow —
without dragging FastAPI request objects along. Services raise plain exceptions; turning
those into HTTP status codes is the router's job, not this module's.
"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import DUMMY_PASSWORD_HASH, hash_password, verify_password
from logger import logger
from models import User
from schemas.user import UserCreate


class UserAlreadyExistsError(Exception):
    """Raised when username or email is taken. `field` says which, for a precise message."""

    def __init__(self, field: str):
        self.field = field
        super().__init__(f"{field} already registered")


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    user = User(
        username=payload.username,
        email=payload.email,
        # The plaintext password never reaches the database, the ORM, or a log line —
        # it is hashed right here and only the digest is stored.
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        # The UNIQUE indexes on username/email are the real guard against duplicates —
        # they hold even when two requests race, which a "check first, then insert" in
        # Python cannot. We catch the violation and then figure out which column it was,
        # purely to return a helpful message.
        await session.rollback()
        raise await _which_field_collided(session, payload)

    await session.refresh(user)  # pull back id, created_at, is_active — filled by Postgres
    logger.info(f"Registered user id={user.id} username={user.username}")
    return user


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Used by the auth dependency to turn a token's `sub` back into a User."""
    return await session.get(User, user_id)


async def get_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """Return the user iff the username exists AND the password matches. Returns None
    (not an exception) on any failure — the router turns that into a 401. The caller
    must NOT reveal which half failed, or it becomes a username-enumeration oracle."""
    user = await get_by_username(session, username)
    if user is None:
        # Verify against a dummy hash anyway, so a missing user costs the same time as
        # a wrong password. See DUMMY_PASSWORD_HASH in core.security.
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _which_field_collided(
    session: AsyncSession, payload: UserCreate
) -> UserAlreadyExistsError:
    """Only runs on the error path, so the extra lookups cost nothing in the happy case."""
    if await get_by_username(session, payload.username):
        return UserAlreadyExistsError("username")
    return UserAlreadyExistsError("email")