"""
OrderItem model - Line items within an order.

Per docs:
- order_id: FK -> Order.id (Required)
- sku_id: FK -> SKU.id (Required)
- quantity_ordered: Integer (Required)
- quantity_manufactured: Integer (Default: 0)
- quantity_delivered: Integer (Default: 0)
- unit_price_rands: Decimal (Required) - Snapshot price after tier discount

OrderItem Status (Derived from Quantities per docs):
- Pending: quantity_manufactured = 0
- Manufacturing: quantity_manufactured > 0 AND < quantity_ordered
- Manufactured: quantity_manufactured == quantity_ordered
- Delivered: quantity_delivered == quantity_ordered
- Outstanding: quantity_ordered > quantity_delivered
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class OrderItemStatus:
    """Derived status based on quantity fields."""
    PENDING = "pending"
    MANUFACTURING = "manufacturing"
    MANUFACTURED = "manufactured"
    PARTIALLY_DELIVERED = "partially_delivered"
    DELIVERED = "delivered"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_manufactured = Column(Integer, nullable=False, default=0)
    quantity_allocated = Column(Integer, nullable=False, default=0)  # Inventory allocated to this item
    quantity_delivered = Column(Integer, nullable=False, default=0)
    unit_price_rands = Column(Numeric(12, 2), nullable=False)  # Snapshot at order creation
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items", lazy="joined")
    sku = relationship("SKU", back_populates="order_items", lazy="joined")

    @property
    def derived_status(self) -> str:
        """Calculate status based on quantities."""
        if self.quantity_delivered == self.quantity_ordered:
            return OrderItemStatus.DELIVERED
        if self.quantity_delivered > 0:
            return OrderItemStatus.PARTIALLY_DELIVERED
        if self.quantity_manufactured == self.quantity_ordered:
            return OrderItemStatus.MANUFACTURED
        if self.quantity_manufactured > 0:
            return OrderItemStatus.MANUFACTURING
        return OrderItemStatus.PENDING

    @property
    def quantity_outstanding(self) -> int:
        """Calculate remaining quantity to be delivered."""
        return self.quantity_ordered - self.quantity_delivered

    @property
    def line_total_rands(self) -> Decimal:
        """Calculate line total (quantity * unit price)."""
        return Decimal(self.quantity_ordered) * self.unit_price_rands

    @property
    def product_name(self) -> str | None:
        """Get product name from SKU relationship."""
        if self.sku and self.sku.product:
            return self.sku.product.name
        return None

    @property
    def product_image(self) -> str | None:
        """Get product image URL from SKU relationship."""
        if self.sku and self.sku.product:
            return self.sku.product.image_url
        return None

    @property
    def sku_code(self) -> str | None:
        """Get SKU code from SKU relationship."""
        if self.sku:
            return self.sku.code
        return None
