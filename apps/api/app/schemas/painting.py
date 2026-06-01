"""Painting day plan schemas."""
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PaintingPlanItemCreate(BaseModel):
    """One line in a painting day plan create payload."""
    model_config = ConfigDict(extra="forbid")
    order_item_id: UUID
    quantity_planned: int = Field(gt=0)


class PaintingPlanCreate(BaseModel):
    """Create today's painting plan."""
    model_config = ConfigDict(extra="forbid")
    plan_date: date | None = None  # Defaults to today
    items: list[PaintingPlanItemCreate]


class PaintingPlanAddItems(BaseModel):
    """Add additional items to an existing plan."""
    model_config = ConfigDict(extra="forbid")
    items: list[PaintingPlanItemCreate]


class PaintingPlanItemComplete(BaseModel):
    """Update completion against a painting day item."""
    model_config = ConfigDict(extra="forbid")
    quantity_completed: int = Field(ge=0)


class PaintingPlanItemResponse(BaseModel):
    """One line in a painting day plan response."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_item_id: UUID
    quantity_planned: int
    quantity_completed: int
    # Enrichment for the UI:
    order_id: UUID | None = None
    client_or_store_label: str | None = None
    customer_name: str | None = None
    sku_code: str | None = None
    product_name: str | None = None
    size: str | None = None
    color: str | None = None
    display_string: str | None = None
    remaining: int = 0


class PaintingPlanResponse(BaseModel):
    """Today's painting plan."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    plan_date: date
    created_by: UUID
    created_at: datetime
    items: list[PaintingPlanItemResponse] = []
    total_planned: int = 0
    total_completed: int = 0


class PaintingDemandItem(BaseModel):
    """One line in the outstanding paint demand list."""
    order_item_id: UUID
    order_id: UUID
    order_created_at: datetime
    client_or_store_label: str
    customer_name: str | None = None
    sku_code: str
    product_name: str
    size: str | None = None
    color: str | None = None
    display_string: str
    quantity_outstanding: int


class PaintingDemandResponse(BaseModel):
    items: list[PaintingDemandItem]
    total_items: int
    total_units: int
