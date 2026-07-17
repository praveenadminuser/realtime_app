"""Password hashing. The only module that knows how a password is stored.

Login will reuse verify_password() unchanged — which is the point of putting it here
rather than in the user service. If we ever move off bcrypt, this file is the only edit.
"""
import bcrypt


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