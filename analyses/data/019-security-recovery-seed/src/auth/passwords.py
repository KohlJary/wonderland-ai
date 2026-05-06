"""Password hashing primitives — bcrypt with a sane work factor."""

from __future__ import annotations

import bcrypt

# 12 rounds: ~250ms per hash on modern hardware. Adjust if hash latency
# becomes a bottleneck (it isn't yet — login is bounded by DB lookup
# more than by bcrypt).
WORK_FACTOR = 12


def hash_password(plaintext: str) -> str:
    """Hash plaintext with bcrypt; returns the encoded string ready
    for storage in User.password_hash."""
    salt = bcrypt.gensalt(rounds=WORK_FACTOR)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Constant-time bcrypt comparison."""
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # malformed hash — treat as non-match rather than raising up
        # the call stack into an unrelated 500
        return False
