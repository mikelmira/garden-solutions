"""
PriceTier model - Global discount structures.

Per docs:
- name: String (Unique, Required) - e.g., "Tier A", "Tier B", "Tier C"
- discount_percentage: Decimal (Required) - 0.10 = 10% discount
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class PriceTier(Base):
    __tablename__ = "price_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    discount_percentage = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    clients = relationship("Client", back_populates="price_tier", lazy="select")
    stores = relationship("Store", back_populates="price_tier", lazy="select")
