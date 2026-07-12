"""ORM models. Alembic autogenerate compares these against the live schema.

Every model must be reachable from this module — alembic/env.py imports it, which is
what registers the tables on Base.metadata. A model in a file nobody imports is
invisible to autogenerate, and Alembic will cheerfully propose DROPPING its table.
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(String(500), nullable=False)
    # server_default=now() means Postgres stamps the time, not the app. With
    # several pods whose clocks may drift, one authority for "now" is worth having.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # unique=True creates a UNIQUE INDEX, which enforces the constraint AND makes
    # the login lookup fast. Uniqueness must be the database's job: two pods can
    # handle two signups for the same name at the same moment, and a "check then
    # insert" in Python has a race window between the two. The database does not.
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # NOT "password". This column holds a bcrypt/argon2 hash — a one-way digest.
    # You never read it back and compare; you hash the incoming attempt and compare
    # the hashes. 255 chars leaves room for any modern hash format (bcrypt is 60,
    # argon2 ~100), so switching algorithms later needs no migration.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Nullable: a real signup form rarely demands these up front, and a NOT NULL
    # column you have no value for is what forces ugly placeholder data like "".
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))

    # Date, not DateTime — a birthday has no time and no timezone. Storing it as a
    # timestamp means someone in another timezone eventually reads it a day early.
    date_of_birth: Mapped[date | None] = mapped_column(Date)

    # Soft disable. Deleting a user row breaks every foreign key pointing at it;
    # flipping a flag doesn't.
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # onupdate is applied by SQLAlchemy on ORM updates. Note it does NOT fire for a
    # raw `UPDATE users SET ...` issued outside the ORM — only a Postgres trigger
    # would catch that.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )