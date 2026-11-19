from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UserUpdate


def update_user_profile(db: Session, user: User, data: UserUpdate) -> User:
    """Update profile fields with uniqueness validation."""
    if data.email is not None and data.email != user.email:
        existing_email = db.query(User).filter(User.email == data.email, User.id != user.id).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )
        user.email = data.email

    if data.username is not None and data.username != user.username:
        existing_username = (
            db.query(User).filter(User.username == data.username, User.id != user.id).first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already in use",
            )
        user.username = data.username

    db.commit()
    db.refresh(user)
    return user


def change_user_password(
    db: Session,
    user: User,
    data: ChangePasswordRequest,
) -> None:
    """
    Change user password after verifying current password.
    Revokes all active refresh tokens for the user upon password change.
    """
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    user.hashed_password = hash_password(data.new_password)

    # Invalidate all existing refresh tokens to force re-authentication
    db.query(RefreshToken).filter_by(user_id=user.id, revoked_at=None).update(
        {"revoked_at": datetime.now(UTC)}
    )
    db.commit()
