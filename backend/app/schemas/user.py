import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def validate_password_complexity(v: str) -> str:
    """Enforce password length and complexity rules."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(v) > 128:
        raise ValueError("Password must not exceed 128 characters")
    if v.isspace() or not v.strip():
        raise ValueError("Password must not consist only of whitespace")
    if not re.search(r"[\d\W_]", v):
        raise ValueError("Password must contain at least one digit or special character")
    return v


class UserRegister(BaseModel):
    """Payload for user registration."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_complexity(v)


class UserResponse(BaseModel):
    """Public user profile response (strictly excludes password hashes)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Payload for updating user profile."""

    email: EmailStr | None = None
    username: str | None = Field(
        default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$"
    )


class LoginRequest(BaseModel):
    """JSON payload for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response containing access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing an access token."""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Payload for changing current user's password."""

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return validate_password_complexity(v)
