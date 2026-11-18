import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.models.refresh_token import RefreshToken
from app.models.user import User
from sqlalchemy.exc import IntegrityError


def test_create_refresh_token_model(db_session):
    """Verify RefreshToken model creation with valid foreign key."""
    user = User(
        email="rt_user@example.com",
        username="rtuser",
        hashed_password="hashed_pw_test",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    jti = str(uuid.uuid4())
    token_hash = "fake_sha256_hash_value_1234567890abcdef"
    expires_at = datetime.now(UTC) + timedelta(days=7)

    token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        jti=jti,
        expires_at=expires_at,
    )
    db_session.add(token)
    db_session.commit()
    db_session.refresh(token)

    assert token.id is not None
    assert isinstance(token.id, uuid.UUID)
    assert token.user_id == user.id
    assert token.token_hash == token_hash
    assert token.jti == jti
    assert token.revoked_at is None
    assert token.created_at is not None
    assert token.user.id == user.id
    assert token in user.refresh_tokens


def test_refresh_token_jti_unique(db_session):
    """Verify jti uniqueness constraint."""
    user = User(
        email="rt_unique@example.com",
        username="rtunique",
        hashed_password="hashed_pw_test",
    )
    db_session.add(user)
    db_session.commit()

    jti = str(uuid.uuid4())
    token1 = RefreshToken(
        user_id=user.id,
        token_hash="hash1",
        jti=jti,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(token1)
    db_session.commit()

    token2 = RefreshToken(
        user_id=user.id,
        token_hash="hash2",
        jti=jti,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(token2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_refresh_token_cascade_delete(db_session):
    """Verify deleting User cascades to RefreshToken records."""
    user = User(
        email="rt_cascade@example.com",
        username="rtcascade",
        hashed_password="hashed_pw_test",
    )
    db_session.add(user)
    db_session.commit()

    token = RefreshToken(
        user_id=user.id,
        token_hash="hash_cascade",
        jti=str(uuid.uuid4()),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(token)
    db_session.commit()
    token_id = token.id

    db_session.delete(user)
    db_session.commit()

    deleted_token = db_session.query(RefreshToken).filter_by(id=token_id).first()
    assert deleted_token is None
