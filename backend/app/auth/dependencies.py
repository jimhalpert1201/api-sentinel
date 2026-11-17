from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    Retrieve current authenticated user.
    In Phase 1, retrieves the first active user or creates a development user.
    Full JWT authentication will be integrated in Phase 2.
    """
    user = db.query(User).filter_by(is_active=True).first()
    if not user:
        user = User(
            email="dev@sentinel.local",
            username="devuser",
            hashed_password="not-a-real-hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
