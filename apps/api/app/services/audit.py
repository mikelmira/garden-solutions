"""
Audit service for logging write operations.

Per Sprint 1 spec:
- ALL write operations must create AuditLog entry
- Explicit logging within same transaction
"""
from typing import Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog, AuditAction


class AuditService:
    """Service for creating audit log entries."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str | UUID | None = None,
        performed_by: UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            action: The action performed (from AuditAction constants)
            entity_type: Type of entity (e.g., 'client', 'order')
            entity_id: ID of the entity
            performed_by: ID of the user performing the action
            payload: JSON dict with details

        Returns:
            The created AuditLog entry
        """
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            action=action,
            performed_by=performed_by,
            payload=payload,
        )
        self.db.add(audit_log)
        # Note: Caller is responsible for commit (same transaction as business operation)
        return audit_log
