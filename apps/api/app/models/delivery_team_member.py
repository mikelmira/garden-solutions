"""
Delivery Team Member model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DeliveryTeamMember(Base):
    __tablename__ = "delivery_team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_team_id = Column(UUID(as_uuid=True), ForeignKey("delivery_teams.id"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    team = relationship("DeliveryTeam", back_populates="members", lazy="joined")
