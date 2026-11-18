import time
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.passwords import hash_password, verify_password
from app.core.config import settings


def test_hash_password_and_verify():
    """Verify password hashing produces bcrypt hash and verifies correctly."""
    plain = "SuperSecretPassword123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_create_access_token():
    """Verify access token contains expected claims (sub, exp, type=access)."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert "exp" in payload
    assert payload["exp"] > time.time()


def test_create_refresh_token():
    """Verify refresh token returns raw token, jti string, and expiration datetime."""
    user_id = uuid.uuid4()
    raw_token, jti, expires_at = create_refresh_token(user_id)

    assert isinstance(jti, str)
    assert len(jti) > 0
    assert expires_at > datetime.now(UTC)

    payload = jwt.decode(
        raw_token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == str(user_id)
    assert payload["jti"] == jti
    assert payload["type"] == "refresh"


def test_decode_token_valid():
    """Verify decode_token successfully decodes valid token."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_decode_token_expired():
    """Verify decode_token raises for expired token."""
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    expired_payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": now - timedelta(minutes=5),
        "iat": now - timedelta(minutes=20),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired_token)


def test_decode_token_invalid_signature():
    """Verify decode_token raises for invalid signature."""
    user_id = uuid.uuid4()
    token = jwt.encode(
        {"sub": str(user_id), "type": "access"},
        "wrong_secret_key_at_least_32_bytes_long",
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token)
