"""
Store schemas.
"""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class StoreCreate(BaseModel):
    """Schema for creating a store (admin only)."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    store_type: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    price_tier_id: UUID | None = None


class StoreUpdate(BaseModel):
    """Schema for updating a store (admin only)."""
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    store_type: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    price_tier_id: UUID | None = None
    is_active: bool | None = None


class StoreResponse(BaseModel):
    """Store response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    store_type: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    price_tier_id: UUID | None = None
    is_active: bool


class StoreResolveRequest(BaseModel):
    """Resolve store by code (public)."""
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=50)


class StoreResolveResponse(BaseModel):
    """Resolve response for public store lookup."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    store_type: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
