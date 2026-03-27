"""
Client schemas per Sprint 1 spec.
Per docs: reject unknown fields (extra="forbid"), use specific types.
"""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.price_tier import PriceTierResponse


class ClientCreate(BaseModel):
    """Schema for creating a client (admin only)."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    tier_id: UUID
    address: str | None = Field(default=None, max_length=500)


class ClientUpdate(BaseModel):
    """Schema for updating a client (admin only)."""
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    tier_id: UUID | None = None
    address: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ClientResponse(BaseModel):
    """Client response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address: str | None = None  # Sprint 2.1: Optional address field
    tier_id: UUID
    created_by: UUID
    is_active: bool


class ClientDetailResponse(ClientResponse):
    """Client detail response with nested price tier."""
    price_tier: PriceTierResponse


class PublicClientResponse(BaseModel):
    """Public client response schema for ordering flow."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address: str | None = None
