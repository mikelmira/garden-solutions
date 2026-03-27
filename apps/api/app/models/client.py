"""
Client model - B2B customer.

Per Sprint 1 spec:
- id
- name
- tier_id (FK -> PriceTier)
- created_by (user_id) - who created this client
- address (optional) - Sprint 2.1 addition
- timestamps
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=True)  # Sprint 2.1: Optional address field
    tier_id = Column(UUID(as_uuid=True), ForeignKey("price_tiers.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    price_tier = relationship("PriceTier", back_populates="clients", lazy="joined")
    creator = relationship("User", backref="created_clients", lazy="joined")
    orders = relationship("Order", back_populates="client", lazy="select")
