"""User request/response contracts. The API's public shape, separate from the ORM.

Keeping these distinct from models.User matters: the model has a password_hash column,
and if the API returned the model directly that hash would go out over the wire. The
response schema simply has no field for it, so it cannot leak.
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """What the register endpoint accepts. Note it has `password`, never `password_hash` —
    hashing is the server's job, done in core.security, never the client's."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr  # validated as a real address; needs the email-validator package
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def not_in_future(cls, v: date | None) -> date | None:
        # A birthday in the future is a typo, not data. This is the extension point
        # for per-field rules — add password-strength or username-charset checks here.
        if v is not None and v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return v


class UserRead(BaseModel):
    """What the API returns. Deliberately omits password_hash — the client never sees it.

    from_attributes lets FastAPI build this straight from the SQLAlchemy User object.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    is_active: bool
    created_at: datetime