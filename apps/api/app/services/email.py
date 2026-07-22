"""
Email sending service backed by Resend (https://resend.com).

Uses stdlib urllib so no new dependency is required. Sends are best-effort:
if RESEND_API_KEY is unset or the POST fails, we log and return False so the
caller can proceed with their work (plan creation must not fail because of an
email outage).

To enable:
  1. Sign up at https://resend.com (free tier: 3,000 emails/month).
  2. Verify a sending domain (e.g. gsoperations.co.za).
  3. Set RESEND_API_KEY=<your key> in apps/api/.env on the server.
  4. Optionally override RESEND_FROM_EMAIL and RESEND_FROM_NAME.
"""
from __future__ import annotations

import json
import logging
import threading
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Iterable

from app.core.config import get_settings

logger = logging.getLogger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"


def business_now() -> datetime:
    """Current wall-clock time in the business timezone, as a naive datetime.

    All email-automation times (send_time / send_at / next_run_at /
    last_sent_at) are stored in business-local time so what admins type in
    the UI is what they get. Offset configured via SCHEDULER_UTC_OFFSET_MINUTES
    (South Africa is UTC+2 year-round, no DST, so a fixed offset is safe).
    """
    offset = timedelta(minutes=get_settings().SCHEDULER_UTC_OFFSET_MINUTES)
    return (datetime.utcnow() + offset).replace(microsecond=0)


def send_email_async(
    to: Iterable[str],
    subject: str,
    html: str,
    *,
    reply_to: str | None = None,
) -> None:
    """Fire-and-forget wrapper: schedules send_email on a daemon thread.

    Email is best-effort; this never blocks the request thread and never raises.
    """
    # Snapshot the iterable now so a generator can't be exhausted by the caller.
    recipients = list(to)
    if not recipients:
        return
    t = threading.Thread(
        target=send_email,
        args=(recipients, subject, html),
        kwargs={"reply_to": reply_to},
        daemon=True,
        name="resend-send",
    )
    t.start()


def send_email(
    to: Iterable[str],
    subject: str,
    html: str,
    *,
    reply_to: str | None = None,
) -> bool:
    """Send a single email via Resend. Returns True on success, False on any error.

    Synchronous. Prefer send_email_async for inside-request use.
    """
    settings = get_settings()
    api_key = settings.RESEND_API_KEY
    recipients = [addr for addr in to if addr]
    if not recipients:
        logger.info("send_email skipped: no recipients")
        return False
    if not api_key:
        logger.warning(
            "send_email skipped: RESEND_API_KEY is not set. "
            "Set it in apps/api/.env to enable sending."
        )
        return False

    payload: dict = {
        "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
        "to": recipients,
        "subject": subject,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    req = urllib.request.Request(
        RESEND_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            logger.info(
                "Resend send ok subject=%r recipients=%d status=%d",
                subject,
                len(recipients),
                resp.status,
            )
            return True
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        logger.error(
            "Resend HTTPError status=%s body=%s", e.code, err_body[:500]
        )
        return False
    except Exception as e:  # noqa: BLE001
        logger.error("Resend send failed: %s", e)
        return False
