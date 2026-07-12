"""Async database engine, session factory, and the FastAPI session dependency."""
import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    """Every model inherits from this; Alembic reads Base.metadata to diff the schema."""


def build_connect_args() -> dict:
    """Driver-level arguments. Also imported by alembic/env.py so migrations
    reach RDS over TLS the same way the app does."""
    if not settings.db_ssl:
        return {}
    # asyncpg wants a real ssl.SSLContext, not a "sslmode" string.
    return {"ssl": ssl.create_default_context()}


engine = create_async_engine(
    # Assembled from DB_HOST/DB_PORT/... unless DATABASE_URL overrides it — see config.py.
    settings.sqlalchemy_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    # RDS drops idle connections (and hands you a dead pool after a failover).
    # pool_pre_ping issues a cheap liveness check before handing out a
    # connection, turning a hard 500 into a transparent reconnect.
    pool_pre_ping=True,
    # Recycle before AWS's typical idle timeout closes the socket from under us.
    pool_recycle=1800,
    connect_args=build_connect_args(),
)

# expire_on_commit=False: without it, attributes are expired after commit and
# touching them triggers a lazy reload — which in async code raises instead of
# silently querying. Returning an object after commit is the common case, so
# this is the setting you want.
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, always closed."""
    async with SessionLocal() as session:
        yield session