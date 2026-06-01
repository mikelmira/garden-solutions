"""Email recipient management endpoints (admin only)."""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.core.exceptions import NotFoundException
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.email_recipient import (
    EmailRecipientCreate,
    EmailRecipientUpdate,
    EmailRecipientResponse,
)
from app.models.email_recipient import EmailRecipient
from app.services.audit import AuditService
from app.models.audit_log import AuditAction

router = APIRouter()


@router.get("", response_model=ListResponse[EmailRecipientResponse])
def list_recipients(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    category: str | None = Query(None),
    include_inactive: bool = Query(False),
):
    q = db.query(EmailRecipient)
    if category:
        q = q.filter(EmailRecipient.category == category)
    if not include_inactive:
        q = q.filter(EmailRecipient.is_active.is_(True))
    rows = q.order_by(EmailRecipient.email.asc()).all()
    return ListResponse(
        data=[EmailRecipientResponse.model_validate(r) for r in rows],
        pagination=PaginationMeta(total=len(rows), page=1, size=len(rows)),
    )


@router.post("", response_model=DataResponse[EmailRecipientResponse], status_code=201)
def create_recipient(
    data: EmailRecipientCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    audit = AuditService(db)
    row = EmailRecipient(
        email=str(data.email),
        name=data.name,
        category=data.category,
    )
    db.add(row)
    db.flush()
    audit.log(
        action=AuditAction.CREATE,
        entity_type="email_recipient",
        entity_id=row.id,
        performed_by=current_user.id,
        payload={"email": row.email, "category": row.category, "name": row.name},
    )
    db.commit()
    db.refresh(row)
    return DataResponse(data=EmailRecipientResponse.model_validate(row))


@router.patch("/{recipient_id}", response_model=DataResponse[EmailRecipientResponse])
def update_recipient(
    recipient_id: UUID,
    data: EmailRecipientUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    row = db.query(EmailRecipient).filter(EmailRecipient.id == recipient_id).first()
    if not row:
        raise NotFoundException("Email recipient not found")
    if data.email is not None:
        row.email = str(data.email)
    if data.name is not None:
        row.name = data.name
    if data.category is not None:
        row.category = data.category
    if data.is_active is not None:
        row.is_active = data.is_active
    AuditService(db).log(
        action=AuditAction.UPDATE,
        entity_type="email_recipient",
        entity_id=row.id,
        performed_by=current_user.id,
        payload={
            "email": row.email,
            "name": row.name,
            "category": row.category,
            "is_active": row.is_active,
        },
    )
    db.commit()
    db.refresh(row)
    return DataResponse(data=EmailRecipientResponse.model_validate(row))


@router.delete("/{recipient_id}", response_model=DataResponse[EmailRecipientResponse])
def delete_recipient(
    recipient_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Soft-delete: set is_active=False."""
    row = db.query(EmailRecipient).filter(EmailRecipient.id == recipient_id).first()
    if not row:
        raise NotFoundException("Email recipient not found")
    row.is_active = False
    AuditService(db).log(
        action=AuditAction.DELETE,
        entity_type="email_recipient",
        entity_id=row.id,
        performed_by=current_user.id,
        payload={"email": row.email},
    )
    db.commit()
    db.refresh(row)
    return DataResponse(data=EmailRecipientResponse.model_validate(row))
