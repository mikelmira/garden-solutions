"""
Manufacturing schemas for queue, daily plans, and updates.
"""
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import SKUResponse


# ==== SKU Display Helpers ====

class SKUDisplayInfo(BaseModel):
    """SKU info for display in UI."""
    model_config = ConfigDict(from_attributes=True)

    sku_id: UUID
    sku_code: str
    product_name: str
    size: str
    color: str
    display_string: str  # e.g., "5x Egg Pot - Small Green"


# ==== Outstanding Demand (for admin manufacturing page) ====

class OutstandingOrderBreakdown(BaseModel):
    """Shows which order contributes to outstanding demand for a SKU."""
    model_config = ConfigDict(from_attributes=True)

    item_id: UUID  # Added for frontend updates
    order_id: UUID
    order_created_at: datetime
    client_or_store_label: str  # e.g., "Greenfields Nursery" or "Store: Main St"
    client_or_store_type: str  # "client" or "store"
    quantity_outstanding: int


class OutstandingSKUDemand(BaseModel):
    """Aggregated outstanding demand for a single SKU."""
    model_config = ConfigDict(from_attributes=True)

    sku_id: UUID
    sku_code: str
    product_name: str
    size: str
    color: str
    total_outstanding: int
    display_string: str  # e.g., "15x Egg Pot - Small Green"
    breakdown: list[OutstandingOrderBreakdown] = []


class OutstandingDemandResponse(BaseModel):
    """Full response for outstanding manufacturing demand."""
    model_config = ConfigDict(from_attributes=True)

    skus: list[OutstandingSKUDemand] = []
    total_skus: int
    total_units: int


# ==== Manufacturing Day Plan ====

class ManufacturingDayItemCreate(BaseModel):
    """Item to include in a new manufacturing day plan."""
    model_config = ConfigDict(extra="forbid")

    sku_id: UUID
    quantity_planned: int = Field(gt=0)


class ManufacturingDayCreate(BaseModel):
    """Create a new manufacturing day plan."""
    model_config = ConfigDict(extra="forbid")

    plan_date: date | None = None  # Defaults to today
    items: list[ManufacturingDayItemCreate] = Field(min_length=1)


class ManufacturingDayAddItems(BaseModel):
    """Add items to an existing manufacturing day plan."""
    model_config = ConfigDict(extra="forbid")

    items: list[ManufacturingDayItemCreate] = Field(min_length=1)


class ManufacturingDayItemResponse(BaseModel):
    """Response for a single manufacturing day item."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku_id: UUID
    sku_code: str
    product_name: str
    size: str
    color: str
    quantity_planned: int
    quantity_completed: int
    display_string: str  # e.g., "10x Egg Pot - Small Green"
    remaining: int  # planned - completed


class ManufacturingDayResponse(BaseModel):
    """Response for a manufacturing day plan."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_date: date
    created_by: UUID
    created_at: datetime
    items: list[ManufacturingDayItemResponse] = []
    total_planned: int
    total_completed: int


# ==== Moulding Updates ====

class MouldingItemUpdate(BaseModel):
    """Update completed quantity for a manufacturing day item."""
    model_config = ConfigDict(extra="forbid")

    quantity_completed: int = Field(ge=0)


# ==== Legacy Queue Schemas (keep for compatibility) ====

class ManufacturingQueueItemResponse(BaseModel):
    """Order item view for manufacturing queue."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    sku_id: UUID
    quantity_ordered: int
    quantity_manufactured: int
    remaining_to_manufacture: int
    sku: SKUResponse


class ManufacturingQueueOrderResponse(BaseModel):
    """Order view for manufacturing queue."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID | None = None
    client_name: str | None = None
    delivery_date: date
    status: str
    items: list[ManufacturingQueueItemResponse] = []


class OrderItemManufacturedUpdate(BaseModel):
    """Update manufacturing quantity for an order item."""
    model_config = ConfigDict(extra="forbid")

    quantity_manufactured: int = Field(ge=0)
