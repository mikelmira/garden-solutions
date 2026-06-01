"""
EmailAutomation model — scheduled recurring (or one-off) plan emails.

The existing EmailRecipient table handles the "fire this email immediately
when admin creates today's plan" flow. EmailAutomation adds independent,
scheduled or one-off sends, e.g. "every weekday at 06:00, email the
moulding plan to these recipients".
"""
import uuid
from datetime import datetime, time, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Time, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EmailAutomationPlanType:
    """What content the automation emails."""
    MOULDING = "moulding"
    PAINTING = "painting"
    ORDERS = "orders"
    DELIVERIES = "deliveries"

    ALL = [MOULDING, PAINTING, ORDERS, DELIVERIES]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class EmailAutomationFrequency:
    ONCE = "once"          # send once at send_at datetime
    DAILY = "daily"        # every day at send_time
    WEEKDAYS = "weekdays"  # Mon-Fri at send_time
    WEEKLY = "weekly"      # day_of_week at send_time

    ALL = [ONCE, DAILY, WEEKDAYS, WEEKLY]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class EmailAutomation(Base):
    __tablename__ = "email_automations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    plan_type = Column(String(20), nullable=False, index=True)
    frequency = Column(String(20), nullable=False)

    # For recurring: time of day (UTC). For "once": ignored if send_at is set.
    send_time = Column(Time, nullable=True)
    # For weekly only: 0=Monday ... 6=Sunday
    day_of_week = Column(Integer, nullable=True)
    # For "once" frequency: the specific moment to fire.
    send_at = Column(DateTime, nullable=True)

    # Recipients are inline — list of email strings (validated app-side).
    recipients = Column(JSONB, nullable=False, default=list)

    is_active = Column(Boolean, nullable=False, default=True)
    last_sent_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
