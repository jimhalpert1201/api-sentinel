from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Retrieve the authenticated user's profile."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile fields (email, username) for current user."""
    return user_service.update_user_profile(db=db, user=current_user, data=data)


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change user password",
)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password and invalidate all existing refresh tokens."""
    user_service.change_user_password(db=db, user=current_user, data=data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
