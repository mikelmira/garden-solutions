"""
PriceTier schemas.
Per docs: reject unknown fields (extra="forbid"), use specific types.
"""
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PriceTierBase(BaseModel):
    """Base price tier fields."""
    name: str = Field(min_length=1, max_length=100)
    discount_percentage: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    is_active: bool = True


class PriceTierCreate(PriceTierBase):
    """Schema for creating a price tier."""
    model_config = ConfigDict(extra="forbid")


class PriceTierUpdate(BaseModel):
    """Schema for updating a price tier."""
    name: str | None = Field(None, min_length=1, max_length=100)
    discount_percentage: Decimal | None = Field(None, ge=Decimal("0"), le=Decimal("1"))
    is_active: bool | None = None
    model_config = ConfigDict(extra="forbid")


class PriceTierAssignments(BaseModel):
    """Counts of assigned entities."""
    client_count: int
    store_count: int


class PriceTierResponse(PriceTierBase):
    """Price tier response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    updated_at: datetime
