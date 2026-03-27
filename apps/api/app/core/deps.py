"""
Dependencies for FastAPI routes.
Includes authentication and role-based authorization.
"""
from typing import Annotated
from uuid import UUID
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.core.config import get_settings
from app.core.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    InactiveUserException,
)
from app.models.user import User, UserRole

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """Validate JWT token and return current user."""
    payload = decode_token(token)
    if payload is None:
        raise UnauthorizedException()

    # Check token type
    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    user_id_str: str | None = payload.get("user_id")
    if user_id_str is None:
        raise UnauthorizedException()

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException()

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedException()

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user


class RoleChecker:
    """
    Dependency for role-based access control at API layer.

    Usage:
        @router.get("/admin-only")
        def admin_endpoint(
            current_user: Annotated[User, Depends(RoleChecker([UserRole.ADMIN]))]
        ):
            ...
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException(
                f"Role '{current_user.role}' is not authorized for this action"
            )
        return current_user


# Pre-configured role checkers for convenience
require_admin = RoleChecker([UserRole.ADMIN])
require_sales = RoleChecker([UserRole.SALES, UserRole.ADMIN])
require_manufacturing = RoleChecker([UserRole.MANUFACTURING, UserRole.ADMIN])
require_delivery = RoleChecker([UserRole.DELIVERY, UserRole.ADMIN])
require_any_role = RoleChecker(UserRole.ALL_ROLES)


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
SalesUser = Annotated[User, Depends(require_sales)]
ManufacturingUser = Annotated[User, Depends(require_manufacturing)]
DeliveryUser = Annotated[User, Depends(require_delivery)]
