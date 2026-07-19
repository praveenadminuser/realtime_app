"""Password hashing and JWT tokens — the two crypto primitives, in one place.

Everything above this layer (services, routers, dependencies) uses these functions and
never touches bcrypt or PyJWT directly. Swap the hash algorithm or the token library and
this is the only file that changes.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import settings


def hash_password(plain: str) -> str:
    """Hash a plaintext password for storage. Never store the plaintext itself."""
    # bcrypt operates on bytes and silently truncates anything past 72 BYTES (not
    # chars — a multibyte password hits the limit sooner). We cap explicitly so the
    # truncation is visible in the code rather than a surprise. For passwords longer
    # than this you would pre-hash with SHA-256; not worth it for a signup form.
    pw = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    """Check a login attempt against the stored hash. Constant-time (bcrypt's checkpw)."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], password_hash.encode("utf-8"))
    except ValueError:
        # A malformed hash in the DB (e.g. hand-edited) — treat as no match, don't 500.
        return False


# A real bcrypt hash of a throwaway string. authenticate_user() verifies against this
# when the username doesn't exist, so a login for an unknown user takes the SAME time
# as one for a known user with a wrong password. Without it, "user not found" returns
# instantly and "wrong password" takes ~100ms — a timing oracle that lets an attacker
# enumerate valid usernames.
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Mint a signed JWT whose `sub` (subject) identifies the user. Stateless: nothing
    is stored server-side, so the signature is the ONLY thing that makes it trustworthy."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,   # who the token is about — we put the user id here
        "iat": now,       # issued-at
        "exp": expire,    # PyJWT rejects the token automatically once this passes
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """Verify signature AND expiry, returning the claims — or None if the token is
    forged, tampered, expired, or otherwise invalid. Callers treat None as 401."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],  # pin the algorithm — see the note below
        )
    except jwt.PyJWTError:
        # One catch-all on purpose: never leak WHY a token failed (expired vs bad
        # signature vs malformed). The client gets a flat 401 either way.
        return None
    # Pinning `algorithms` matters: if you accepted whatever the token's header claims,
    # an attacker could send alg:"none" (unsigned) or downgrade RS256->HS256 and forge
    # tokens. Always dictate the algorithm on the verify side.