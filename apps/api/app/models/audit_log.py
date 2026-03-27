"""
AuditLog model for immutable audit trail.

Per Sprint 1 spec:
- id
- entity_type
- entity_id
- action
- performed_by (user_id)
- payload (JSON)
- timestamp
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class AuditAction:
    """Audit action types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"


class AuditLog(Base):
    """
    Immutable audit trail for all write operations.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), nullable=True)  # UUID as string
    action = Column(String(50), nullable=False, index=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    payload = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationship
    user = relationship("User", backref="audit_logs", lazy="select")
