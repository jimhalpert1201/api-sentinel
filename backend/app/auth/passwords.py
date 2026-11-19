"""
Password hashing and verification utilities using bcrypt.
Enforces NFR-010 (bcrypt cost factor >= 12).
"""

import bcrypt

BCRYPT_ROUNDS = 12


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using salted bcrypt with cost factor 12."""
    pwd_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False
