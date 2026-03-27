"""
Order model - Header record for B2B sale.

Per docs:
- client_id: FK -> Client.id (Required)
- created_by: FK -> User.id (Required) - Who created the order
- created_at: Timestamp (Required)
- delivery_date: Date (Required) - Default: created_at + 14 days
- status: String (Use OrderStatus) (Required)
- total_price_rands: Decimal (Required) - Snapshot at order time
- notes: Text (Optional)

Status Transitions per docs:
- Draft → Pending Approval
- Pending Approval → Approved OR Cancelled
- Approved → In Production (automatic when mfg starts)
- In Production → Ready for Delivery (automatic when all items mfg complete)
- Ready for Delivery → Out for Delivery
- Out for Delivery → Partially Delivered OR Completed
- Partially Delivered → Completed
"""
import uuid
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class OrderStatus:
    """Order status constants - using VARCHAR with app-level validation per docs."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PRODUCTION = "in_production"
    READY_FOR_DELIVERY = "ready_for_delivery"
    OUT_FOR_DELIVERY = "out_for_delivery"
    PARTIALLY_DELIVERED = "partially_delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    ALL_STATUSES = [
        DRAFT, PENDING_APPROVAL, APPROVED, IN_PRODUCTION,
        READY_FOR_DELIVERY, OUT_FOR_DELIVERY, PARTIALLY_DELIVERED,
        COMPLETED, CANCELLED
    ]

    # Valid transitions: current_status -> list of allowed next statuses
    VALID_TRANSITIONS = {
        DRAFT: [PENDING_APPROVAL],
        PENDING_APPROVAL: [APPROVED, CANCELLED],
        APPROVED: [IN_PRODUCTION, CANCELLED],
        IN_PRODUCTION: [READY_FOR_DELIVERY],
        READY_FOR_DELIVERY: [OUT_FOR_DELIVERY],
        OUT_FOR_DELIVERY: [PARTIALLY_DELIVERED, COMPLETED],
        PARTIALLY_DELIVERED: [COMPLETED],
        COMPLETED: [],  # Terminal state
        CANCELLED: [],  # Terminal state
    }

    # Admin-only manual transitions (Approved, Cancelled only per docs)
    ADMIN_ALLOWED_TARGETS = [APPROVED, CANCELLED]

    @classmethod
    def is_valid(cls, status: str) -> bool:
        return status in cls.ALL_STATUSES

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        """Check if transition from current to target is valid."""
        if current not in cls.VALID_TRANSITIONS:
            return False
        return target in cls.VALID_TRANSITIONS[current]

    @classmethod
    def is_admin_transition(cls, target: str) -> bool:
        """Check if target status requires admin privileges."""
        return target in cls.ADMIN_ALLOWED_TARGETS


class DeliveryStatus:
    """Delivery status constants for assigned orders."""
    OUTSTANDING = "outstanding"
    DELIVERED = "delivered"
    PARTIAL = "partial"
    NOT_DELIVERED = "not_delivered"

    ALL_STATUSES = [OUTSTANDING, DELIVERED, PARTIAL, NOT_DELIVERED]


class OrderSource:
    """Order source constants."""
    CLIENT = "client"
    STORE = "store"
    SHOPIFY = "shopify"

    ALL_SOURCES = [CLIENT, STORE, SHOPIFY]


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sales_agent_id = Column(UUID(as_uuid=True), ForeignKey("sales_agents.id"), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    order_source = Column(String(50), nullable=True, index=True)
    delivery_team_id = Column(UUID(as_uuid=True), ForeignKey("delivery_teams.id"), nullable=True)
    delivery_status = Column(String(50), nullable=True)
    delivery_paused = Column(Boolean, nullable=False, default=False)
    delivery_status_reason = Column(Text, nullable=True)
    delivery_receiver_name = Column(String(255), nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    delivery_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default=OrderStatus.PENDING_APPROVAL, index=True)
    total_price_rands = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="orders", lazy="joined")
    creator = relationship("User", backref="created_orders", lazy="joined")
    sales_agent = relationship("SalesAgent", lazy="joined")
    store = relationship("Store", lazy="joined")
    delivery_team = relationship("DeliveryTeam", lazy="joined")
    items = relationship("OrderItem", back_populates="order", lazy="joined", cascade="all, delete-orphan")

    @staticmethod
    def default_delivery_date() -> date:
        """Return default delivery date (14 days from now)."""
        return date.today() + timedelta(days=14)
