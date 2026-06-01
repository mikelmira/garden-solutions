"""Email automation endpoints (admin only)."""
from datetime import date as date_cls
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.email_automation import (
    EmailAutomationCreate,
    EmailAutomationUpdate,
    EmailAutomationResponse,
    OnceOffSendRequest,
    OnceOffSendResponse,
)
from app.services.email_automation import EmailAutomationService
from app.services.plan_emails import send_ad_hoc_email
from app.core.config import get_settings

router = APIRouter()


@router.get("", response_model=ListResponse[EmailAutomationResponse])
def list_automations(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False),
):
    service = EmailAutomationService(db)
    rows = service.list(include_inactive=include_inactive)
    return ListResponse(
        data=[EmailAutomationResponse.model_validate(r) for r in rows],
        pagination=PaginationMeta(total=len(rows), page=1, size=len(rows)),
    )


@router.post("", response_model=DataResponse[EmailAutomationResponse], status_code=201)
def create_automation(
    data: EmailAutomationCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = EmailAutomationService(db)
    row = service.create(
        name=data.name,
        plan_type=data.plan_type,
        frequency=data.frequency,
        send_time=data.send_time,
        day_of_week=data.day_of_week,
        send_at=data.send_at,
        recipients=[str(r) for r in data.recipients],
        created_by=current_user.id,
    )
    return DataResponse(data=EmailAutomationResponse.model_validate(row))


@router.patch("/{automation_id}", response_model=DataResponse[EmailAutomationResponse])
def update_automation(
    automation_id: UUID,
    data: EmailAutomationUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = EmailAutomationService(db)
    row = service.update(
        automation_id,
        name=data.name,
        plan_type=data.plan_type,
        frequency=data.frequency,
        send_time=data.send_time,
        day_of_week=data.day_of_week,
        send_at=data.send_at,
        recipients=[str(r) for r in data.recipients] if data.recipients is not None else None,
        is_active=data.is_active,
        performed_by=current_user.id,
    )
    return DataResponse(data=EmailAutomationResponse.model_validate(row))


@router.delete("/{automation_id}", response_model=DataResponse[dict])
def delete_automation(
    automation_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = EmailAutomationService(db)
    service.delete(automation_id, performed_by=current_user.id)
    return DataResponse(data={"deleted": True})


@router.post("/{automation_id}/run", response_model=DataResponse[EmailAutomationResponse])
def run_automation_now(
    automation_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Trigger an automation immediately without altering its schedule."""
    service = EmailAutomationService(db)
    row = service.manual_run(automation_id)
    return DataResponse(data=EmailAutomationResponse.model_validate(row))


@router.post("/send-once-off", response_model=DataResponse[OnceOffSendResponse])
def send_once_off(
    data: OnceOffSendRequest,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Send a one-off email immediately for the given plan_type.

    Reports `sent=True` only when the email was actually dispatched to Resend.
    If RESEND_API_KEY is missing, we still render the email (so the UI confirms
    the content was prepared) but report `sent=False` with a clear note.
    """
    target_date = data.for_date or date_cls.today()
    recipients = [str(r) for r in data.recipients]
    api_key_set = bool(get_settings().RESEND_API_KEY)

    dispatched = send_ad_hoc_email(
        db,
        plan_type=data.plan_type,
        recipients=recipients,
        for_date=target_date,
    )

    # If dispatched is True but no API key, the background thread will no-op
    # and log a warning. Report this honestly to the user.
    if dispatched and not api_key_set:
        sent = False
        note = "Email rendered but RESEND_API_KEY isn't configured on the server — nothing actually sent. Set it in apps/api/.env and restart the API."
    elif not dispatched:
        sent = False
        note = "Email could not be rendered. Check API logs."
    else:
        sent = True
        note = None

    return DataResponse(data=OnceOffSendResponse(
        sent=sent,
        plan_type=data.plan_type,
        recipients=recipients,
        for_date=target_date,
        note=note,
    ))
