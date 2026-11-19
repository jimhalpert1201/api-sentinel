import uuid
from datetime import UTC, datetime

import pytest
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserRegister,
    UserResponse,
)
from pydantic import ValidationError


def test_user_register_valid():
    """Verify UserRegister accepts valid registration payload."""
    payload = {
        "email": "valid@example.com",
        "username": "valid_user123",
        "password": "StrongPassword123!",
    }
    schema = UserRegister(**payload)
    assert schema.email == "valid@example.com"
    assert schema.username == "valid_user123"
    assert schema.password == "StrongPassword123!"


def test_user_register_invalid_email():
    """Verify UserRegister rejects malformed email."""
    with pytest.raises(ValidationError):
        UserRegister(
            email="not-an-email",
            username="valid_user",
            password="StrongPassword123!",
        )


@pytest.mark.parametrize(
    "weak_password",
    [
        "short1!",  # < 8 chars
        "alllowercasepasswordwithoutdigitsorspecials",  # no digits or specials
        "   ",  # whitespace only
        "A" * 129,  # > 128 chars
    ],
)
def test_user_register_weak_passwords(weak_password):
    """Verify password complexity validation rejects weak passwords."""
    with pytest.raises(ValidationError):
        UserRegister(
            email="test@example.com",
            username="valid_user",
            password=weak_password,
        )


def test_user_response_excludes_password():
    """Verify UserResponse includes public fields and never exposes hashed_password."""
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    data = {
        "id": user_id,
        "email": "user@example.com",
        "username": "user123",
        "role": "user",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "hashed_password": "secret_bcrypt_hash",
    }
    response = UserResponse.model_validate(data)
    dump = response.model_dump()

    assert dump["id"] == user_id
    assert dump["email"] == "user@example.com"
    assert dump["username"] == "user123"
    assert dump["role"] == "user"
    assert dump["is_active"] is True
    assert "hashed_password" not in dump
    assert "password" not in dump


def test_login_request():
    """Verify LoginRequest validation."""
    login = LoginRequest(email="login@example.com", password="Password123!")
    assert login.email == "login@example.com"
    assert login.password == "Password123!"


def test_token_response():
    """Verify TokenResponse fields."""
    token = TokenResponse(
        access_token="acc_token_123",
        refresh_token="ref_token_123",
    )
    assert token.access_token == "acc_token_123"
    assert token.refresh_token == "ref_token_123"
    assert token.token_type == "bearer"


def test_refresh_token_request():
    """Verify RefreshTokenRequest schema."""
    req = RefreshTokenRequest(refresh_token="valid_ref_token")
    assert req.refresh_token == "valid_ref_token"


def test_change_password_request():
    """Verify ChangePasswordRequest schema validates new password complexity."""
    valid = ChangePasswordRequest(
        current_password="OldPassword123!",
        new_password="NewStrongPassword456@",
    )
    assert valid.current_password == "OldPassword123!"
    assert valid.new_password == "NewStrongPassword456@"

    # Rejects weak new password
    with pytest.raises(ValidationError):
        ChangePasswordRequest(
            current_password="OldPassword123!",
            new_password="short",
        )
