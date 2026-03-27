"""
Delivery schemas for queue and updates.
"""
from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import SKUResponse


class DeliveryQueueItemResponse(BaseModel):
    """Order item view for delivery queue."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    sku_id: UUID
    quantity_ordered: int
    quantity_manufactured: int
    quantity_delivered: int
    remaining_to_deliver: int
    sku: SKUResponse
    product_name: str | None = None
    product_image: str | None = None
    sku_code: str | None = None


class DeliveryQueueOrderResponse(BaseModel):
    """Order view for delivery queue."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID | None = None
    client_name: str | None = None
    client_address: str | None = None
    delivery_date: date
    status: str
    delivery_state: str
    delivery_receiver_name: str | None = None
    items: list[DeliveryQueueItemResponse] = []


class DeliveryItemUpdate(BaseModel):
    """Delivered quantity for a specific order item."""
    model_config = ConfigDict(extra="forbid")

    order_item_id: UUID
    quantity_delivered: int = Field(ge=0)


class DeliveryComplete(BaseModel):
    """Complete delivery payload."""
    model_config = ConfigDict(extra="forbid")

    receiver_name: str = Field(min_length=1)


class DeliveryPartial(BaseModel):
    """Partial delivery payload with per-item delivered quantities."""
    model_config = ConfigDict(extra="forbid")

    receiver_name: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    items: list[DeliveryItemUpdate] = Field(min_length=1)


class OrderItemDeliveredUpdate(BaseModel):
    """Update delivered quantity for an order item (absolute)."""
    model_config = ConfigDict(extra="forbid")

    quantity_delivered: int = Field(ge=0)


class PublicDeliveryQueueRequest(BaseModel):
    """Query parameters for public delivery queue."""
    model_config = ConfigDict(extra="forbid")

    team_code: str = Field(min_length=1, max_length=50)
    date: str | None = None


class DeliveryOutcomeItem(BaseModel):
    """Item delivered quantities for public delivery outcome."""
    model_config = ConfigDict(extra="forbid")

    order_item_id: UUID
    quantity_delivered: int = Field(ge=0)


class DeliveryOutcomeRequest(BaseModel):
    """Public delivery outcome payload."""
    model_config = ConfigDict(extra="forbid")

    team_code: str = Field(min_length=1, max_length=50)
    outcome: str = Field(min_length=1, max_length=20)
    receiver_name: str | None = Field(default=None, min_length=1, max_length=255)
    reason: str | None = Field(default=None, min_length=1, max_length=255)
    items: list[DeliveryOutcomeItem] | None = None
