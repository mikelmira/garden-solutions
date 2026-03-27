"""
SKU model - Specific sellable unit (variant).

Per docs:
- product_id: FK -> Product.id (Required)
- code: String (Unique, Required) - e.g., "CP-L-TC"
- size: String (Required)
- color: String (Required)
- base_price_rands: Decimal (Required) - Standard price before discount
- stock_quantity: Integer (Required) - Current physical stock
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class SKU(Base):
    __tablename__ = "skus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    size = Column(String(50), nullable=False)
    color = Column(String(50), nullable=False)
    base_price_rands = Column(Numeric(12, 2), nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="skus", lazy="joined")
    order_items = relationship("OrderItem", back_populates="sku", lazy="select")
