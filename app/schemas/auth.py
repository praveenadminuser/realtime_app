"""Auth contracts."""
from pydantic import BaseModel


class Token(BaseModel):
    """The login response. `token_type: "bearer"` is what the OAuth2 spec expects, and
    what tells a client to send `Authorization: Bearer <access_token>` on later calls."""

    access_token: str
    token_type: str = "bearer"