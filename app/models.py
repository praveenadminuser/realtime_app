"""ORM models. Alembic autogenerate compares these against the live schema."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
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