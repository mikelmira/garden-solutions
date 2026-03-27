"""
Order and OrderItem schemas.
Per docs: reject unknown fields (extra="forbid"), use specific types.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.order import OrderStatus
from app.schemas.product import SKUResponse


class OrderItemCreate(BaseModel):
    """Schema for creating an order item."""
    model_config = ConfigDict(extra="forbid")

    sku_id: UUID
    quantity_ordered: int = Field(gt=0)


class OrderItemResponse(BaseModel):
    """Order item response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    sku_id: UUID
    quantity_ordered: int
    quantity_manufactured: int
    quantity_allocated: int = 0  # Inventory allocated to this item
    quantity_delivered: int
    unit_price_rands: Decimal
    line_total_rands: Decimal  # Computed property


class OrderItemDetailResponse(OrderItemResponse):
    """Order item with SKU details."""
    sku: SKUResponse
    product_name: str | None = None
    product_image: str | None = None
    sku_code: str | None = None


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    model_config = ConfigDict(extra="forbid")

    client_id: UUID | None = None
    sales_agent_id: UUID | None = None
    sales_agent_code: str | None = None
    store_id: UUID | None = None
    store_code: str | None = None
    order_source: str | None = None
    items: list[OrderItemCreate] = Field(min_length=1)
    delivery_date: date | None = None  # Default: +14 days
    notes: str | None = None


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status (admin only)."""
    model_config = ConfigDict(extra="forbid")

    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        # Admin can only set APPROVED or CANCELLED per docs
        if v not in OrderStatus.ADMIN_ALLOWED_TARGETS:
            raise ValueError(f"Status must be one of: {OrderStatus.ADMIN_ALLOWED_TARGETS}")
        return v


class DeliveryTeamAssign(BaseModel):
    """Assign a delivery team to an order."""
    model_config = ConfigDict(extra="forbid")

    delivery_team_id: UUID


class DeliveryAssignmentUpdate(BaseModel):
    """Update delivery assignment or schedule."""
    model_config = ConfigDict(extra="forbid")

    delivery_team_id: UUID | None = None
    delivery_date: date | None = None
    paused: bool | None = None


class OrderResponse(BaseModel):
    """Order response schema (list view)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID | None = None
    created_by: UUID
    sales_agent_id: UUID | None = None
    store_id: UUID | None = None
    order_source: str | None = None
    delivery_team_id: UUID | None = None
    delivery_status: str | None = None
    delivery_status_reason: str | None = None
    delivery_receiver_name: str | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    delivery_date: date
    status: str
    total_price_rands: Decimal
    notes: str | None
    is_ready_for_delivery: bool = False  # Computed: all items fully allocated
    delivery_paused: bool | None = None


class OrderDetailResponse(OrderResponse):
    """Order detail response with items."""
    items: list[OrderItemDetailResponse] = []
    delivery_state: str | None = None
    delivery_receiver_name: str | None = None


class OrderWithClientResponse(OrderResponse):
    """Order response with client name for list views."""
    client_name: str | None = None
