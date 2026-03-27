"""
Standardized error handling per docs (RFC 7807 style).

Error envelope format:
{
    "code": "STOCK_ERROR",
    "detail": "Product X is discontinued.",
    "trace_id": "abc-123"
}
"""
import uuid
from typing import Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode:
    """Standard error codes."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INACTIVE_USER = "INACTIVE_USER"
    INVALID_TOKEN = "INVALID_TOKEN"


class ErrorResponse(BaseModel):
    """RFC 7807 style error response."""
    code: str
    detail: str
    trace_id: str


class AppException(HTTPException):
    """Base application exception with standardized error format."""

    def __init__(
        self,
        status_code: int,
        code: str,
        detail: str,
        headers: dict[str, str] | None = None
    ):
        self.code = code
        self.trace_id = str(uuid.uuid4())
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class UnauthorizedException(AppException):
    """401 Unauthorized - Missing/invalid token."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidCredentialsException(AppException):
    """401 Unauthorized - Invalid username/password."""

    def __init__(self, detail: str = "Incorrect username or password"):
        super().__init__(
            status_code=401,
            code=ErrorCode.INVALID_CREDENTIALS,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(AppException):
    """403 Forbidden - Valid token but role not allowed."""

    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=403,
            code=ErrorCode.FORBIDDEN,
            detail=detail
        )


class NotFoundException(AppException):
    """404 Not Found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=404,
            code=ErrorCode.NOT_FOUND,
            detail=detail
        )


class ConflictException(AppException):
    """409 Conflict - Optimistic lock failure / state mismatch."""

    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=409,
            code=ErrorCode.CONFLICT,
            detail=detail
        )


class InactiveUserException(AppException):
    """400 Bad Request - User account is inactive."""

    def __init__(self, detail: str = "User account is inactive"):
        super().__init__(
            status_code=400,
            code=ErrorCode.INACTIVE_USER,
            detail=detail
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle AppException and return standardized error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "detail": exc.detail,
            "trace_id": exc.trace_id
        },
        headers=exc.headers
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with standardized error response."""
    trace_id = str(uuid.uuid4())
    return JSONResponse(
        status_code=500,
        content={
            "code": ErrorCode.INTERNAL_ERROR,
            "detail": "An unexpected error occurred",
            "trace_id": trace_id
        }
    )
