"""
Auth-related Pydantic schemas.
Per docs: reject unknown fields (extra="forbid"), use specific types.
"""
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict
import uuid

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Login request body for JSON-based login."""
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1)


class Token(BaseModel):
    """Token response for login/refresh."""
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenData(BaseModel):
    """Decoded token data."""
    user_id: str
    role: str
    schema_version: int


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Request body for changing password."""
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class UserBase(BaseModel):
    """Base user fields."""
    email: EmailStr
    full_name: str
    role: str  # VARCHAR-backed, validated at app level
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user (admin only in future)."""
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    """User response schema (safe fields only)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool


class UserInDB(UserBase):
    """User as stored in database (internal use)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hashed_password: str
