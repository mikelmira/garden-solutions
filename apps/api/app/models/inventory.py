"""
Inventory model - Global SKU-level stock on hand.

Per manufacturing flow requirements:
- Single global inventory pool for GS
- Tracks quantity_on_hand per SKU
- Updated when manufacturing completes
- Decremented when allocated to orders
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class InventoryItem(Base):
    """Global inventory tracking per SKU."""
    __tablename__ = "inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False, unique=True, index=True)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    sku = relationship("SKU", lazy="joined")
