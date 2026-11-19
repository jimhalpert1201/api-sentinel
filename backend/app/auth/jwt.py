"""
JWT token utilities for access and refresh tokens.
Uses PyJWT with HS256 signing.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import settings


def create_access_token(
    user_id: uuid.UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed JWT access token (default TTL: 15 minutes)."""
    now = datetime.now(UTC)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    user_id: uuid.UUID,
    expires_delta: timedelta | None = None,
) -> tuple[str, str, datetime]:
    """
    Generate a signed JWT refresh token with unique jti (default TTL: 7 days).
    Returns (raw_token, jti, expires_at).
    """
    now = datetime.now(UTC)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.refresh_token_expire_days)
    )
    jti = str(uuid.uuid4())

    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "iat": now,
        "exp": expires_at,
    }
    raw_token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return raw_token, jti, expires_at


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token's signature and expiration.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
