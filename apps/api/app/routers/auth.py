"""
Auth endpoints per docs:
- POST /api/v1/auth/login (Public) - Returns Access + Refresh Token
- POST /api/v1/auth/refresh (Public) - Returns new Access Token
- GET /api/v1/auth/me (Protected) - Returns current user profile
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    decode_token,
    get_password_hash,
)
from app.core.deps import CurrentUser
from app.core.exceptions import InvalidCredentialsException, UnauthorizedException
from app.models.user import User
from app.schemas.auth import Token, UserResponse, RefreshTokenRequest, ChangePasswordRequest
from app.schemas.common import DataResponse
from app.services.audit import AuditService
from app.models.audit_log import AuditAction

router = APIRouter()


def get_client_info(request: Request) -> tuple[str | None, str | None]:
    """Extract client IP and user agent from request."""
    # Get IP address (handle proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None

    user_agent = request.headers.get("User-Agent")
    return ip_address, user_agent


@router.post("/login", response_model=DataResponse[Token])
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return tokens.

    Accepts OAuth2 password flow (form data with username/password).
    The username field should contain the user's email.
    """
    audit_service = AuditService(db)
    ip_address, user_agent = get_client_info(request)

    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        audit_service.log(
            action=AuditAction.LOGIN_FAILURE,
            entity_type="auth",
            payload={"email": form_data.username, "ip_address": ip_address, "user_agent": user_agent},
        )
        db.commit()
        raise InvalidCredentialsException()

    if not user.is_active:
        # Log failed login for inactive user (do not leak status to client)
        audit_service.log(
            action=AuditAction.LOGIN_FAILURE,
            entity_type="auth",
            payload={"email": form_data.username, "ip_address": ip_address, "user_agent": user_agent, "reason": "inactive"},
        )
        db.commit()
        raise InvalidCredentialsException()

    # Create tokens
    access_token = create_access_token(user_id=user.id, role=user.role)
    refresh_token = create_refresh_token(user_id=user.id)

    # Log successful login
    audit_service.log(
        action=AuditAction.LOGIN_SUCCESS,
        entity_type="auth",
        entity_id=user.id,
        performed_by=user.id,
        payload={"ip_address": ip_address, "user_agent": user_agent},
    )
    db.commit()

    return DataResponse(
        data=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
    )


@router.post("/refresh", response_model=DataResponse[Token])
def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using a valid refresh token.
    """
    audit_service = AuditService(db)
    ip_address, user_agent = get_client_info(request)

    # Decode refresh token
    payload = decode_token(body.refresh_token)
    if payload is None:
        raise UnauthorizedException("Invalid refresh token")

    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")

    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise UnauthorizedException("Invalid refresh token")

    # Get user
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("Invalid refresh token")

    if not user.is_active:
        raise UnauthorizedException("Invalid refresh token")

    # Create new tokens
    access_token = create_access_token(user_id=user.id, role=user.role)
    new_refresh_token = create_refresh_token(user_id=user.id)

    # Log token refresh
    audit_service.log(
        action="token_refresh",
        entity_type="auth",
        entity_id=user.id,
        performed_by=user.id,
        payload={"ip_address": ip_address, "user_agent": user_agent},
    )
    db.commit()

    return DataResponse(
        data=Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
    )


@router.get("/me", response_model=DataResponse[UserResponse])
def get_current_user_profile(current_user: CurrentUser):
    """
    Get current authenticated user's profile.
    """
    return DataResponse(data=UserResponse.model_validate(current_user))


@router.post("/change-password", response_model=DataResponse[dict])
def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Change password for the current user.
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not verify_password(body.current_password, user.hashed_password):
        raise InvalidCredentialsException()

    user.hashed_password = get_password_hash(body.new_password)

    audit_service = AuditService(db)
    audit_service.log(
        action=AuditAction.UPDATE,
        entity_type="auth",
        entity_id=user.id,
        performed_by=user.id,
        payload={"event": "password_change"},
    )
    db.commit()
    return DataResponse(data={"success": True})
