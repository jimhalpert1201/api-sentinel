from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limiter import auth_rate_limiter
from app.schemas.user import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserRegister,
    UserResponse,
)
from app.services import auth_service

router = APIRouter()


def check_auth_rate_limit(request: Request) -> None:
    """Enforce brute-force protection rate limit per client IP (5 requests / 60 seconds)."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not auth_rate_limiter.is_allowed(client_ip, max_requests=5, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    """Create a new user account with validated email, username, and password."""
    return auth_service.register_user(db=db, data=data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and issue access and refresh tokens.
    Supports both JSON bodies (LoginRequest) and OAuth2 form-data for Swagger /docs integration.
    """
    check_auth_rate_limit(request)

    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username and password are required in form data",
            )
        identifier = str(username)
        pwd = str(password)
    else:
        try:
            body = await request.json()
            login_data = LoginRequest(**body)
            identifier = str(login_data.email)
            pwd = login_data.password
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors(),
            ) from e
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid JSON payload",
            ) from None

    user = auth_service.authenticate_user(db=db, identifier=identifier, password=pwd)
    return auth_service.create_session_tokens(db=db, user=user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new session tokens",
)
def refresh(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Rotate the provided refresh token. Revokes previous token and guards against reuse."""
    return auth_service.refresh_session(db=db, raw_refresh_token=data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user and invalidate session",
)
def logout(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Revoke the refresh token on logout."""
    auth_service.revoke_refresh_token(db=db, raw_refresh_token=data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
