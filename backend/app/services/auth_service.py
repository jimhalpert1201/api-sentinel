import hashlib
import uuid
from datetime import UTC, datetime

import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.passwords import hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import TokenResponse, UserRegister


def hash_token_secret(token: str) -> str:
    """Compute SHA-256 hex digest of a token for secure storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def register_user(db: Session, data: UserRegister) -> User:
    """Register a new user after verifying email and username uniqueness."""
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if db.query(User).filter_by(username=data.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User:
    """
    Authenticate user by email or username and verify password.
    Raises 401 Unauthorized on invalid credentials or inactive account.
    """
    user = db.query(User).filter((User.email == identifier) | (User.username == identifier)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def create_session_tokens(db: Session, user: User) -> TokenResponse:
    """Generate new access token and database-persisted refresh token."""
    access_token = create_access_token(user.id)
    raw_refresh, jti, expires_at = create_refresh_token(user.id)
    token_hash = hash_token_secret(raw_refresh)

    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        jti=jti,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
    )


def refresh_session(db: Session, raw_refresh_token: str) -> TokenResponse:
    """
    Rotate refresh token and issue new session tokens.
    Implements reuse detection: if a revoked token is presented, all user sessions are invalidated.
    """
    try:
        payload = decode_token(raw_refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    user_id_str = payload.get("sub")
    if not jti or not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = uuid.UUID(user_id_str)
    token_record = db.query(RefreshToken).filter_by(jti=jti).first()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not recognized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Replay attack prevention: if token was already revoked, revoke ALL user sessions
    if token_record.revoked_at is not None:
        db.query(RefreshToken).filter_by(user_id=user_id, revoked_at=None).update(
            {"revoked_at": datetime.now(UTC)}
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected; all sessions revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter_by(id=user_id, is_active=True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Revoke current token upon successful rotation
    token_record.revoked_at = datetime.now(UTC)
    db.commit()

    return create_session_tokens(db, user)


def revoke_refresh_token(db: Session, raw_refresh_token: str) -> None:
    """Revoke a refresh token on logout."""
    try:
        payload = decode_token(raw_refresh_token)
        jti = payload.get("jti")
        if jti:
            token_record = db.query(RefreshToken).filter_by(jti=jti).first()
            if token_record and token_record.revoked_at is None:
                token_record.revoked_at = datetime.now(UTC)
                db.commit()
                return
    except Exception:
        pass

    # Fallback to hash lookup
    token_hash = hash_token_secret(raw_refresh_token)
    token_record = db.query(RefreshToken).filter_by(token_hash=token_hash).first()
    if token_record and token_record.revoked_at is None:
        token_record.revoked_at = datetime.now(UTC)
        db.commit()
