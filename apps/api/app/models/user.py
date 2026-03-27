import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class UserRole:
    """User role constants - using VARCHAR with app-level validation per docs."""
    ADMIN = "admin"
    SALES = "sales"
    MANUFACTURING = "manufacturing"
    DELIVERY = "delivery"

    ALL_ROLES = [ADMIN, SALES, MANUFACTURING, DELIVERY]

    @classmethod
    def is_valid(cls, role: str) -> bool:
        return role in cls.ALL_ROLES


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # VARCHAR with app-level validation
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
