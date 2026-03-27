"""
Manufacturing Day Plan models - Daily snapshot for production planning.

Per manufacturing flow requirements:
- Admin creates one plan per day (snapshot)
- Plan does not auto-update during the day
- Factory team records completion against plan items
- Completion updates inventory
"""
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, DateTime, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class ManufacturingDay(Base):
    """Daily manufacturing plan header - one per day."""
    __tablename__ = "manufacturing_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_date = Column(Date, nullable=False, unique=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    creator = relationship("User", lazy="joined")
    items = relationship("ManufacturingDayItem", back_populates="manufacturing_day", lazy="joined", cascade="all, delete-orphan")


class ManufacturingDayItem(Base):
    """Line item in a daily manufacturing plan - one per SKU per day."""
    __tablename__ = "manufacturing_day_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturing_day_id = Column(UUID(as_uuid=True), ForeignKey("manufacturing_days.id", ondelete="CASCADE"), nullable=False)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    quantity_planned = Column(Integer, nullable=False)
    quantity_completed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    manufacturing_day = relationship("ManufacturingDay", back_populates="items", lazy="joined")
    sku = relationship("SKU", lazy="joined")
