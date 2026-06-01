"""
EmailAutomation CRUD + scheduling engine.

- Service: create / list / update / delete / manual_run
- Scheduler: a background daemon thread (started in FastAPI lifespan) polls
  every 60s for automations whose next_run_at <= now and fires them.

Single-worker assumption: the polling thread runs in-process. If you scale
uvicorn to >1 worker, multiple processes will race on the same row and may
double-send. For the current single-worker dev/prod setup this is fine; if
you scale, add a SELECT … FOR UPDATE SKIP LOCKED in fire_due_automations().
"""
from __future__ import annotations

import logging
import threading
import time as time_module
from datetime import datetime, date as date_cls, time as time_cls, timedelta, timezone
from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm import attributes as sa_attrs

from app.core.database import SessionLocal
from app.core.exceptions import ConflictException, NotFoundException
from app.models.audit_log import AuditAction
from app.models.email_automation import (
    EmailAutomation,
    EmailAutomationFrequency,
    EmailAutomationPlanType,
)
from app.services.audit import AuditService
from app.services.plan_emails import render_for_today
from app.services.email import send_email_async

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Schedule arithmetic
# ----------------------------------------------------------------------
def compute_next_run_at(
    *,
    frequency: str,
    send_time: time_cls | None,
    day_of_week: int | None,
    send_at: datetime | None,
    last_sent_at: datetime | None = None,
    now: datetime | None = None,
) -> datetime | None:
    """
    Compute the next datetime at which the automation should fire.

    All datetimes are treated as naive-UTC (the existing codebase uses
    datetime.utcnow() naive for stored timestamps; matching that convention).
    """
    now = (now or datetime.utcnow()).replace(microsecond=0)

    if frequency == EmailAutomationFrequency.ONCE:
        if not send_at:
            return None
        # If already fired, no further runs.
        if last_sent_at is not None:
            return None
        return send_at

    if send_time is None:
        return None

    # Helper: combine a date + send_time → naive datetime
    def at(d: date_cls) -> datetime:
        return datetime.combine(d, send_time)

    today = now.date()
    today_at = at(today)

    if frequency == EmailAutomationFrequency.DAILY:
        return today_at if today_at > now else at(today + timedelta(days=1))

    if frequency == EmailAutomationFrequency.WEEKDAYS:
        candidate = today_at if today_at > now else at(today + timedelta(days=1))
        # Advance until weekday < 5 (Mon=0..Fri=4)
        while candidate.weekday() >= 5:
            candidate = at(candidate.date() + timedelta(days=1))
        return candidate

    if frequency == EmailAutomationFrequency.WEEKLY:
        if day_of_week is None or not (0 <= day_of_week <= 6):
            return None
        # Find the next date >= today whose weekday matches.
        delta_days = (day_of_week - today.weekday()) % 7
        candidate = at(today + timedelta(days=delta_days))
        if candidate <= now:
            candidate = at(candidate.date() + timedelta(days=7))
        return candidate

    return None


# ----------------------------------------------------------------------
# Service
# ----------------------------------------------------------------------
class EmailAutomationService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    @staticmethod
    def _validate_payload(
        *,
        plan_type: str,
        frequency: str,
        send_time: time_cls | None,
        day_of_week: int | None,
        send_at: datetime | None,
        recipients: list[str],
    ) -> None:
        if not EmailAutomationPlanType.is_valid(plan_type):
            raise ConflictException(
                f"plan_type must be one of: {', '.join(EmailAutomationPlanType.ALL)}"
            )
        if not EmailAutomationFrequency.is_valid(frequency):
            raise ConflictException(
                f"frequency must be one of: {', '.join(EmailAutomationFrequency.ALL)}"
            )
        if not recipients:
            raise ConflictException("At least one recipient is required.")
        for addr in recipients:
            if not addr or "@" not in addr:
                raise ConflictException(f"Invalid recipient email: {addr!r}")

        if frequency == EmailAutomationFrequency.ONCE:
            if not send_at:
                raise ConflictException("send_at is required for one-off automations.")
        else:
            if not send_time:
                raise ConflictException(
                    f"send_time is required for {frequency} automations."
                )
        if frequency == EmailAutomationFrequency.WEEKLY:
            if day_of_week is None or not (0 <= day_of_week <= 6):
                raise ConflictException("day_of_week (0-6) is required for weekly automations.")

    def list(self, include_inactive: bool = False) -> list[EmailAutomation]:
        q = self.db.query(EmailAutomation)
        if not include_inactive:
            q = q.filter(EmailAutomation.is_active.is_(True))
        return q.order_by(EmailAutomation.created_at.desc()).all()

    def get(self, automation_id: UUID) -> EmailAutomation:
        row = self.db.query(EmailAutomation).filter(EmailAutomation.id == automation_id).first()
        if not row:
            raise NotFoundException("Automation not found")
        return row

    def create(
        self,
        *,
        name: str,
        plan_type: str,
        frequency: str,
        send_time: time_cls | None,
        day_of_week: int | None,
        send_at: datetime | None,
        recipients: list[str],
        created_by: UUID | None,
    ) -> EmailAutomation:
        self._validate_payload(
            plan_type=plan_type,
            frequency=frequency,
            send_time=send_time,
            day_of_week=day_of_week,
            send_at=send_at,
            recipients=recipients,
        )
        row = EmailAutomation(
            name=name.strip() or "(unnamed)",
            plan_type=plan_type,
            frequency=frequency,
            send_time=send_time,
            day_of_week=day_of_week,
            send_at=send_at,
            recipients=list(recipients),
            is_active=True,
            created_by=created_by,
        )
        row.next_run_at = compute_next_run_at(
            frequency=frequency,
            send_time=send_time,
            day_of_week=day_of_week,
            send_at=send_at,
            last_sent_at=None,
        )
        self.db.add(row)
        self.db.flush()
        self.audit.log(
            action=AuditAction.CREATE,
            entity_type="email_automation",
            entity_id=row.id,
            performed_by=created_by,
            payload={"name": row.name, "plan_type": plan_type, "frequency": frequency},
        )
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(
        self,
        automation_id: UUID,
        *,
        name: str | None = None,
        plan_type: str | None = None,
        frequency: str | None = None,
        send_time: time_cls | None = None,
        day_of_week: int | None = None,
        send_at: datetime | None = None,
        recipients: list[str] | None = None,
        is_active: bool | None = None,
        performed_by: UUID | None,
    ) -> EmailAutomation:
        row = self.get(automation_id)

        # Apply patches
        if name is not None:
            row.name = name.strip() or "(unnamed)"
        if plan_type is not None:
            row.plan_type = plan_type
        if frequency is not None:
            row.frequency = frequency
        if send_time is not None or frequency is not None:
            row.send_time = send_time if send_time is not None else row.send_time
        if day_of_week is not None or frequency is not None:
            row.day_of_week = day_of_week if day_of_week is not None else row.day_of_week
        if send_at is not None or frequency is not None:
            row.send_at = send_at if send_at is not None else row.send_at
        if recipients is not None:
            row.recipients = list(recipients)
        if is_active is not None:
            row.is_active = is_active

        self._validate_payload(
            plan_type=row.plan_type,
            frequency=row.frequency,
            send_time=row.send_time,
            day_of_week=row.day_of_week,
            send_at=row.send_at,
            recipients=list(row.recipients or []),
        )

        # Recompute next_run_at — never run a one-off that's already fired.
        row.next_run_at = compute_next_run_at(
            frequency=row.frequency,
            send_time=row.send_time,
            day_of_week=row.day_of_week,
            send_at=row.send_at,
            last_sent_at=row.last_sent_at,
        )

        self.audit.log(
            action=AuditAction.UPDATE,
            entity_type="email_automation",
            entity_id=row.id,
            performed_by=performed_by,
            payload={"name": row.name, "plan_type": row.plan_type, "is_active": row.is_active},
        )
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, automation_id: UUID, performed_by: UUID | None) -> None:
        row = self.get(automation_id)
        self.audit.log(
            action=AuditAction.DELETE,
            entity_type="email_automation",
            entity_id=row.id,
            performed_by=performed_by,
            payload={"name": row.name},
        )
        self.db.delete(row)
        self.db.commit()

    def manual_run(self, automation_id: UUID) -> EmailAutomation:
        """Fire an automation right now without altering its schedule."""
        row = self.get(automation_id)
        _fire_automation_row(self.db, row, advance_schedule=False)
        self.db.commit()
        self.db.refresh(row)
        return row


# ----------------------------------------------------------------------
# Firing logic
# ----------------------------------------------------------------------
def _fire_automation_row(db: Session, row: EmailAutomation, *, advance_schedule: bool) -> None:
    """Render and dispatch one automation. Internal helper used by both the
    manual-run path and the scheduler loop. Caller is responsible for the
    DB commit."""
    try:
        rendered = render_for_today(db, row.plan_type)
        if rendered:
            subject, html = rendered
            send_email_async(to=list(row.recipients or []), subject=subject, html=html)
            row.last_sent_at = datetime.utcnow()
            # JSONB doesn't get marked as dirty on attribute mutation; force it.
            sa_attrs.flag_modified(row, "recipients")
            logger.info(
                "Automation %s (%s) dispatched to %d recipients",
                row.id,
                row.plan_type,
                len(row.recipients or []),
            )
        else:
            logger.warning("Automation %s: render_for_today returned None", row.id)
    except Exception as e:  # noqa: BLE001
        logger.error("Automation %s firing failed: %s", row.id, e)

    if advance_schedule:
        row.next_run_at = compute_next_run_at(
            frequency=row.frequency,
            send_time=row.send_time,
            day_of_week=row.day_of_week,
            send_at=row.send_at,
            last_sent_at=row.last_sent_at,
        )


def fire_due_automations(now: datetime | None = None) -> int:
    """Single tick of the scheduler. Returns the number of automations fired."""
    now = now or datetime.utcnow()
    db = SessionLocal()
    fired = 0
    try:
        due = (
            db.query(EmailAutomation)
            .filter(
                EmailAutomation.is_active.is_(True),
                EmailAutomation.next_run_at.isnot(None),
                EmailAutomation.next_run_at <= now,
            )
            .all()
        )
        for row in due:
            _fire_automation_row(db, row, advance_schedule=True)
            fired += 1
        if fired:
            db.commit()
        return fired
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.error("fire_due_automations error: %s", e)
        return 0
    finally:
        db.close()


# ----------------------------------------------------------------------
# Background scheduler thread
# ----------------------------------------------------------------------
_scheduler_stop = threading.Event()
_scheduler_thread: threading.Thread | None = None
SCHEDULER_TICK_SECONDS = 60


def _scheduler_loop() -> None:
    logger.info("EmailAutomation scheduler started (tick=%ds)", SCHEDULER_TICK_SECONDS)
    # Small initial sleep so the app finishes booting before the first tick.
    if _scheduler_stop.wait(timeout=5):
        return
    while not _scheduler_stop.is_set():
        try:
            fired = fire_due_automations()
            if fired:
                logger.info("Scheduler tick fired %d automation(s)", fired)
        except Exception as e:  # noqa: BLE001
            logger.error("Scheduler tick crashed: %s", e)
        # Wait up to SCHEDULER_TICK_SECONDS, exit early if stop requested.
        if _scheduler_stop.wait(timeout=SCHEDULER_TICK_SECONDS):
            break
    logger.info("EmailAutomation scheduler stopped")


def start_scheduler() -> None:
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _scheduler_stop.clear()
    _scheduler_thread = threading.Thread(
        target=_scheduler_loop, name="email-automation-scheduler", daemon=True
    )
    _scheduler_thread.start()


def stop_scheduler(timeout: float = 5.0) -> None:
    global _scheduler_thread
    _scheduler_stop.set()
    if _scheduler_thread is not None:
        _scheduler_thread.join(timeout=timeout)
        _scheduler_thread = None
