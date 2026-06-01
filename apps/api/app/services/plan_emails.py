"""
Render and dispatch the daily plan emails.

Two entry points:
- send_moulding_plan_email(db, plan) — call after admin creates today's
  manufacturing plan.
- send_painting_plan_email(db, plan) — call after admin creates today's
  painting plan.

Both are best-effort and never raise; failures are logged and the caller
continues unaffected.
"""
from __future__ import annotations

import logging
from datetime import date as date_cls, datetime, timezone
from html import escape

from sqlalchemy.orm import Session

from app.models.email_recipient import EmailRecipient, EmailRecipientCategory
from app.models.manufacturing_day import ManufacturingDay
from app.models.painting_day import PaintingDay
from app.models.order import Order, OrderStatus
from app.models.shopify import ShopifyOrder
from app.services.email import send_email_async

logger = logging.getLogger(__name__)


def _fmt_date_for_humans(value) -> str:
    if isinstance(value, date_cls):
        return value.strftime("%A, %d %B %Y")
    return str(value)


def _client_or_store_label(order: Order) -> str:
    if order.client:
        return order.client.name
    if order.store:
        return f"Store: {order.store.name}"
    return ""


# ----------------------------------------------------------------------
# Common HTML chrome
# ----------------------------------------------------------------------
def _wrap(title: str, intro: str, table_html: str, footer: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<body style="margin:0;padding:0;background:#f5f5f4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#1f2937;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f4;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
        <tr><td style="padding:24px 28px;background:#0f172a;color:#ffffff;">
          <div style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;opacity:.8;">Garden Solutions</div>
          <div style="font-size:22px;font-weight:600;margin-top:4px;">{escape(title)}</div>
        </td></tr>
        <tr><td style="padding:24px 28px;font-size:15px;line-height:1.5;color:#374151;">
          {intro}
          <div style="margin:20px 0 8px 0;">
            {table_html}
          </div>
          <div style="margin-top:24px;font-size:13px;color:#6b7280;">{footer}</div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _table_row(cells: list[str], head: bool = False) -> str:
    cell_style = (
        "padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;"
        + ("font-weight:600;color:#111827;background:#f9fafb;text-align:left;" if head else "color:#1f2937;")
    )
    return "<tr>" + "".join(f"<td style=\"{cell_style}\">{c}</td>" for c in cells) + "</tr>"


# ----------------------------------------------------------------------
# Moulding email
# ----------------------------------------------------------------------
def _render_moulding_plan(plan: ManufacturingDay) -> tuple[str, str]:
    plan_date_str = plan.plan_date.strftime("%A, %d %B %Y") if isinstance(plan.plan_date, date_cls) else str(plan.plan_date)
    total_planned = sum(item.quantity_planned for item in plan.items)

    body_rows = [_table_row(["SKU", "Product", "Size", "Color", "Qty"], head=True)]
    for item in plan.items:
        sku = item.sku
        product_name = sku.product.name if sku and sku.product else "Unknown"
        body_rows.append(
            _table_row([
                escape(sku.code if sku else ""),
                escape(product_name),
                escape(sku.size if sku else ""),
                escape(sku.color if sku else ""),
                f"<strong>{item.quantity_planned}</strong>",
            ])
        )

    table_html = (
        "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" "
        "style=\"border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;border-collapse:separate;border-spacing:0;\">"
        + "".join(body_rows)
        + "</table>"
    )

    intro = (
        f"<p style=\"margin:0 0 8px 0;\"><strong>{escape(plan_date_str)}</strong></p>"
        f"<p style=\"margin:0;\">Today's plan: <strong>{total_planned}</strong> units across <strong>{len(plan.items)}</strong> SKU{'s' if len(plan.items) != 1 else ''}.</p>"
    )
    footer = "This is an automated message from Garden Solutions Operations."

    subject = f"Today's Moulding Plan — {plan_date_str} ({total_planned} units)"
    html = _wrap("Today's Moulding Plan", intro, table_html, footer)
    return subject, html


# ----------------------------------------------------------------------
# Painting email
# ----------------------------------------------------------------------
def _render_painting_plan(db: Session, plan: PaintingDay) -> tuple[str, str]:
    plan_date_str = plan.plan_date.strftime("%A, %d %B %Y") if isinstance(plan.plan_date, date_cls) else str(plan.plan_date)
    total_planned = sum(item.quantity_planned for item in plan.items)

    # Pull shopify customer names in one query for nicer rows.
    order_ids = {item.order_item.order_id for item in plan.items if item.order_item}
    customer_map: dict = {}
    if order_ids:
        rows = (
            db.query(ShopifyOrder)
            .filter(ShopifyOrder.internal_order_id.in_(list(order_ids)))
            .all()
        )
        customer_map = {r.internal_order_id: r.customer_name for r in rows if r.internal_order_id}

    body_rows = [_table_row(["Order", "Client", "Customer", "SKU", "Product", "Qty"], head=True)]
    for item in plan.items:
        oi = item.order_item
        order = oi.order if oi else None
        sku = oi.sku if oi else None
        product_name = sku.product.name if sku and sku.product else "Unknown"
        if order and order.client:
            label = order.client.name
        elif order and order.store:
            label = f"Store: {order.store.name}"
        else:
            label = ""
        order_short = f"#{str(order.id)[:6]}" if order else ""
        customer = customer_map.get(order.id) if order else None
        body_rows.append(
            _table_row([
                f"<code>{escape(order_short)}</code>",
                escape(label),
                escape(customer or ""),
                escape(sku.code if sku else ""),
                escape(f"{product_name} — {sku.size or ''} {sku.color or ''}".strip(" -")),
                f"<strong>{item.quantity_planned}</strong>",
            ])
        )

    table_html = (
        "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" "
        "style=\"border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;border-collapse:separate;border-spacing:0;\">"
        + "".join(body_rows)
        + "</table>"
    )

    intro = (
        f"<p style=\"margin:0 0 8px 0;\"><strong>{escape(plan_date_str)}</strong></p>"
        f"<p style=\"margin:0;\">Today's plan: <strong>{total_planned}</strong> units across <strong>{len(plan.items)}</strong> order item{'s' if len(plan.items) != 1 else ''}.</p>"
    )
    footer = "This is an automated message from Garden Solutions Operations."

    subject = f"Today's Painting Plan — {plan_date_str} ({total_planned} units)"
    html = _wrap("Today's Painting Plan", intro, table_html, footer)
    return subject, html


# ----------------------------------------------------------------------
# Recipient lookup
# ----------------------------------------------------------------------
def _recipients_for(db: Session, primary_category: str) -> list[str]:
    rows = (
        db.query(EmailRecipient)
        .filter(
            EmailRecipient.is_active.is_(True),
            EmailRecipient.category.in_([primary_category, EmailRecipientCategory.BOTH]),
        )
        .all()
    )
    return [r.email for r in rows if r.email]


# ----------------------------------------------------------------------
# Public entry points (never raise)
# ----------------------------------------------------------------------
def send_moulding_plan_email(db: Session, plan: ManufacturingDay) -> bool:
    """Render the email synchronously (DB read) then dispatch send on a thread."""
    try:
        to = _recipients_for(db, EmailRecipientCategory.MOULDING)
        if not to:
            logger.info("No moulding email recipients configured — skipping send")
            return False
        subject, html = _render_moulding_plan(plan)
        send_email_async(to=to, subject=subject, html=html)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("send_moulding_plan_email failed: %s", e)
        return False


def send_painting_plan_email(db: Session, plan: PaintingDay) -> bool:
    """Render the email synchronously (DB read) then dispatch send on a thread."""
    try:
        to = _recipients_for(db, EmailRecipientCategory.PAINTING)
        if not to:
            logger.info("No painting email recipients configured — skipping send")
            return False
        subject, html = _render_painting_plan(db, plan)
        send_email_async(to=to, subject=subject, html=html)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("send_painting_plan_email failed: %s", e)
        return False


# ----------------------------------------------------------------------
# Orders summary email — current open (non-terminal) orders
# ----------------------------------------------------------------------
def _render_orders_summary(db: Session, for_date: date_cls | None = None) -> tuple[str, str]:
    target_date = for_date or date_cls.today()
    open_statuses = [
        OrderStatus.APPROVED,
        OrderStatus.IN_PRODUCTION,
        OrderStatus.PAINTING,
        OrderStatus.READY_FOR_DELIVERY,
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.PARTIALLY_DELIVERED,
    ]
    orders = (
        db.query(Order)
        .filter(Order.status.in_(open_statuses))
        .order_by(Order.delivery_date.asc(), Order.created_at.asc())
        .all()
    )

    # Surface Shopify customer names where present.
    shopify_map = {}
    if orders:
        ids = [o.id for o in orders]
        rows = (
            db.query(ShopifyOrder)
            .filter(ShopifyOrder.internal_order_id.in_(ids))
            .all()
        )
        shopify_map = {r.internal_order_id: r.customer_name for r in rows if r.internal_order_id}

    rows_html = [_table_row(["Order", "Status", "Client", "Customer", "Delivery", "Items"], head=True)]
    total_units = 0
    for o in orders:
        item_count = sum(it.quantity_ordered for it in o.items)
        total_units += item_count
        rows_html.append(_table_row([
            f"<code>#{str(o.id)[:6]}</code>",
            escape(o.status.replace("_", " ").title()),
            escape(_client_or_store_label(o)),
            escape(shopify_map.get(o.id) or ""),
            o.delivery_date.strftime("%d %b") if o.delivery_date else "",
            f"<strong>{item_count}</strong>",
        ]))

    if len(orders) == 0:
        table_html = _empty_state("No open orders right now.")
    else:
        table_html = (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;border-collapse:separate;border-spacing:0;">'
            + "".join(rows_html)
            + "</table>"
        )

    intro = (
        f"<p style=\"margin:0 0 8px 0;\"><strong>{escape(_fmt_date_for_humans(target_date))}</strong></p>"
        f"<p style=\"margin:0;\"><strong>{len(orders)}</strong> open order{'s' if len(orders) != 1 else ''} · <strong>{total_units}</strong> total units to fulfil.</p>"
    )
    footer = "This is an automated message from Garden Solutions Operations."
    subject = f"Open Orders — {_fmt_date_for_humans(target_date)} ({len(orders)} orders)"
    html = _wrap("Open Orders Summary", intro, table_html, footer)
    return subject, html


# ----------------------------------------------------------------------
# Delivery roster email — orders out for delivery today
# ----------------------------------------------------------------------
def _render_deliveries_summary(db: Session, for_date: date_cls | None = None) -> tuple[str, str]:
    target_date = for_date or date_cls.today()

    # "Today's deliveries" = orders with delivery_date == target_date that are
    # plausibly deliverable (allocated/painted/ready/out/partial).
    candidates = [
        OrderStatus.APPROVED,
        OrderStatus.PAINTING,
        OrderStatus.READY_FOR_DELIVERY,
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.PARTIALLY_DELIVERED,
    ]
    orders = (
        db.query(Order)
        .filter(
            Order.delivery_date == target_date,
            Order.status.in_(candidates),
            Order.delivery_paused.is_(False),
        )
        .order_by(Order.created_at.asc())
        .all()
    )

    shopify_map = {}
    if orders:
        ids = [o.id for o in orders]
        rows = (
            db.query(ShopifyOrder)
            .filter(ShopifyOrder.internal_order_id.in_(ids))
            .all()
        )
        shopify_map = {r.internal_order_id: r.customer_name for r in rows if r.internal_order_id}

    rows_html = [_table_row(["Order", "Client", "Customer", "Team", "Items", "Status"], head=True)]
    total_units = 0
    for o in orders:
        units = sum(max(0, it.quantity_ordered - it.quantity_delivered) for it in o.items)
        total_units += units
        team = o.delivery_team.name if o.delivery_team else "Unassigned"
        rows_html.append(_table_row([
            f"<code>#{str(o.id)[:6]}</code>",
            escape(_client_or_store_label(o)),
            escape(shopify_map.get(o.id) or ""),
            escape(team),
            f"<strong>{units}</strong>",
            escape(o.status.replace("_", " ").title()),
        ]))

    if len(orders) == 0:
        table_html = _empty_state(f"No deliveries scheduled for {_fmt_date_for_humans(target_date)}.")
    else:
        table_html = (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;border-collapse:separate;border-spacing:0;">'
            + "".join(rows_html)
            + "</table>"
        )

    intro = (
        f"<p style=\"margin:0 0 8px 0;\"><strong>{escape(_fmt_date_for_humans(target_date))}</strong></p>"
        f"<p style=\"margin:0;\"><strong>{len(orders)}</strong> delivery stop{'s' if len(orders) != 1 else ''} · <strong>{total_units}</strong> units outstanding.</p>"
    )
    footer = "This is an automated message from Garden Solutions Operations."
    subject = f"Delivery Roster — {_fmt_date_for_humans(target_date)} ({len(orders)} stops)"
    html = _wrap("Today's Delivery Roster", intro, table_html, footer)
    return subject, html


def _empty_state(message: str) -> str:
    return (
        '<div style="padding:24px;text-align:center;border:1px dashed #e5e7eb;border-radius:8px;color:#6b7280;font-size:14px;">'
        + escape(message)
        + "</div>"
    )


# ----------------------------------------------------------------------
# Today-relative wrappers — used by automations and the once-off endpoint
# ----------------------------------------------------------------------
def render_for_today(db: Session, plan_type: str, for_date: date_cls | None = None) -> tuple[str, str] | None:
    """
    Render an email payload (subject, html) for a given plan_type, looking
    up the relevant plan/data for `for_date` (default today).

    Returns None if there's no plan for that date (caller decides whether to
    send an empty-state email or skip entirely).
    """
    target_date = for_date or date_cls.today()
    if plan_type == "moulding":
        plan = (
            db.query(ManufacturingDay)
            .filter(ManufacturingDay.plan_date == target_date)
            .first()
        )
        if not plan:
            # Send a graceful empty-state email rather than nothing.
            intro = (
                f"<p style=\"margin:0;\"><strong>{escape(_fmt_date_for_humans(target_date))}</strong></p>"
                "<p style=\"margin:8px 0 0 0;\">No moulding plan has been created yet for this date.</p>"
            )
            return (
                f"Today's Moulding Plan — {_fmt_date_for_humans(target_date)} (no plan)",
                _wrap("Today's Moulding Plan", intro, _empty_state("No moulding plan for this date."), "Automated message."),
            )
        return _render_moulding_plan(plan)
    if plan_type == "painting":
        plan = (
            db.query(PaintingDay)
            .filter(PaintingDay.plan_date == target_date)
            .first()
        )
        if not plan:
            intro = (
                f"<p style=\"margin:0;\"><strong>{escape(_fmt_date_for_humans(target_date))}</strong></p>"
                "<p style=\"margin:8px 0 0 0;\">No painting plan has been created yet for this date.</p>"
            )
            return (
                f"Today's Painting Plan — {_fmt_date_for_humans(target_date)} (no plan)",
                _wrap("Today's Painting Plan", intro, _empty_state("No painting plan for this date."), "Automated message."),
            )
        return _render_painting_plan(db, plan)
    if plan_type == "orders":
        return _render_orders_summary(db, for_date=target_date)
    if plan_type == "deliveries":
        return _render_deliveries_summary(db, for_date=target_date)
    return None


def send_ad_hoc_email(
    db: Session,
    plan_type: str,
    recipients: list[str],
    for_date: date_cls | None = None,
) -> bool:
    """Render and dispatch an ad-hoc email. Best-effort; never raises."""
    try:
        if not recipients:
            return False
        rendered = render_for_today(db, plan_type, for_date=for_date)
        if not rendered:
            return False
        subject, html = rendered
        send_email_async(to=recipients, subject=subject, html=html)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("send_ad_hoc_email failed (plan_type=%s): %s", plan_type, e)
        return False
