"""Alembic environment — async engine, URL sourced from DATABASE_URL."""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Resolved via `prepend_sys_path` in alembic.ini — works from the repo root and
# from inside the container, where the layout differs.
from config import settings
from db import Base, build_connect_args

import models  # noqa: F401 — imported for its side effect: registering tables on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (`alembic upgrade head --sql`).

    Useful for RDS when a DBA wants to review the SQL before it touches production.
    """
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Without this, Alembic ignores column type changes on autogenerate.
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Built directly rather than from alembic.ini so it reuses the app's SSL
    # settings — migrations must reach RDS over TLS exactly like the app does.
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
        connect_args=build_connect_args(),
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
