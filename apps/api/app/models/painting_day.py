"""
Painting Day Plan models - Daily snapshot for painting team.

Key difference vs ManufacturingDay: painting plan items reference order_items
directly (not SKUs), because painting is tracked against specific orders per
the operations spec ("must be a today's plan against the order").

Flow:
- Order reaches PAINTING status once moulding completes for all its items.
- Admin builds today's painting plan from items that still need painting
  (quantity_painted < quantity_ordered).
- Painters record completion per painting_day_item, which increments
  order_items.quantity_painted.
- When every item in an order has quantity_painted == quantity_ordered the
  order auto-advances to READY_FOR_DELIVERY.
"""
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, DateTime, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PaintingDay(Base):
    """Daily painting plan header - one per day."""
    __tablename__ = "painting_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_date = Column(Date, nullable=False, unique=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    creator = relationship("User", lazy="joined")
    items = relationship(
        "PaintingDayItem",
        back_populates="painting_day",
        lazy="joined",
        cascade="all, delete-orphan",
    )


class PaintingDayItem(Base):
    """Line item in a daily painting plan - tied to a specific order_item."""
    __tablename__ = "painting_day_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    painting_day_id = Column(
        UUID(as_uuid=True),
        ForeignKey("painting_days.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity_planned = Column(Integer, nullable=False)
    quantity_completed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    painting_day = relationship("PaintingDay", back_populates="items", lazy="joined")
    order_item = relationship("OrderItem", lazy="joined")
