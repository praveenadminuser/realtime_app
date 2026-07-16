"""Message request/response contracts."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=500)


class MessageRead(BaseModel):
    # from_attributes lets FastAPI serialise the SQLAlchemy object directly.
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    created_at: datetime