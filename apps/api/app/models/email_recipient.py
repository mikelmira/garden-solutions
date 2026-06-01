"""
EmailRecipient model.

A simple list of who should receive automated plan emails:
- category = "moulding"  -> gets Today's Moulding Plan when the admin creates it
- category = "painting"  -> gets Today's Painting Plan when the admin creates it
- category = "both"      -> gets both
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EmailRecipientCategory:
    MOULDING = "moulding"
    PAINTING = "painting"
    BOTH = "both"
    ALL = [MOULDING, PAINTING, BOTH]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class EmailRecipient(Base):
    __tablename__ = "email_recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    category = Column(String(20), nullable=False, default=EmailRecipientCategory.MOULDING)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
