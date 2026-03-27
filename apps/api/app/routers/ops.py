"""
Operational metrics endpoint for the dashboard.

Returns real-time platform health metrics:
- Order counts by status
- Manufacturing progress (outstanding demand, completed today, remaining)
- Delivery stats (today's deliveries, completed, delayed)
- Recent audit log entries
"""
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.manufacturing_day import ManufacturingDay, ManufacturingDayItem
from app.models.audit_log import AuditLog
from app.models.inventory import InventoryItem
from app.services.delivery import DeliveryService

router = APIRouter()


@router.get("/metrics")
def get_operational_metrics(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Return operational metrics for the admin dashboard.

    Covers:
    - Order pipeline counts
    - Manufacturing progress
    - Delivery status
    - Inventory summary
    """

    # ── Order metrics ────────────────────────────────────
    order_counts = {}
    status_counts = (
        db.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    for status, count in status_counts:
        order_counts[status] = count

    pending = order_counts.get(OrderStatus.PENDING_APPROVAL, 0)
    approved = order_counts.get(OrderStatus.APPROVED, 0)
    completed = order_counts.get(OrderStatus.COMPLETED, 0)
    cancelled = order_counts.get(OrderStatus.CANCELLED, 0)
    partially_delivered = order_counts.get(OrderStatus.PARTIALLY_DELIVERED, 0)

    # Count orders that are approved and ready for delivery
    approved_orders = db.query(Order).filter(Order.status == OrderStatus.APPROVED).all()
    ready_for_delivery = 0
    waiting_manufacturing = 0
    for order in approved_orders:
        all_manufactured = all(
            item.quantity_manufactured >= item.quantity_ordered
            and item.quantity_allocated >= item.quantity_ordered
            for item in order.items
        )
        if all_manufactured:
            ready_for_delivery += 1
        else:
            waiting_manufacturing += 1

    orders_metrics = {
        "pending": pending,
        "approved": approved,
        "waiting_manufacturing": waiting_manufacturing,
        "ready_for_delivery": ready_for_delivery,
        "partially_delivered": partially_delivered,
        "completed": completed,
        "cancelled": cancelled,
        "total": sum(order_counts.values()),
    }

    # ── Manufacturing metrics ────────────────────────────
    today = date.today()
    today_plan = (
        db.query(ManufacturingDay)
        .filter(ManufacturingDay.plan_date == today)
        .first()
    )

    # Outstanding demand: approved orders with unallocated items
    outstanding_items = (
        db.query(
            func.sum(OrderItem.quantity_ordered - OrderItem.quantity_allocated)
        )
        .join(Order)
        .filter(
            Order.status == OrderStatus.APPROVED,
            OrderItem.quantity_allocated < OrderItem.quantity_ordered,
        )
        .scalar()
    ) or 0

    mfg_total_planned = 0
    mfg_total_completed = 0
    if today_plan:
        for item in today_plan.items:
            mfg_total_planned += item.quantity_planned
            mfg_total_completed += item.quantity_completed

    manufacturing_metrics = {
        "outstanding_demand": outstanding_items,
        "completed_today": mfg_total_completed,
        "planned_today": mfg_total_planned,
        "remaining_today": mfg_total_planned - mfg_total_completed,
        "has_plan_today": today_plan is not None,
    }

    # ── Delivery metrics ─────────────────────────────────
    # Deliveries assigned for today
    deliveries_today = (
        db.query(func.count(Order.id))
        .filter(Order.delivery_date == today)
        .filter(Order.delivery_team_id.isnot(None))
        .scalar()
    ) or 0

    completed_deliveries = (
        db.query(func.count(Order.id))
        .filter(Order.delivery_date == today)
        .filter(Order.status == OrderStatus.COMPLETED)
        .scalar()
    ) or 0

    # Delayed = past delivery_date, not completed, not cancelled
    delayed_deliveries = (
        db.query(func.count(Order.id))
        .filter(Order.delivery_date < today)
        .filter(Order.status.in_([
            OrderStatus.APPROVED,
            OrderStatus.PARTIALLY_DELIVERED,
        ]))
        .scalar()
    ) or 0

    delivery_metrics = {
        "deliveries_today": deliveries_today,
        "completed_today": completed_deliveries,
        "delayed": delayed_deliveries,
    }

    # ── Inventory summary ────────────────────────────────
    total_inventory = (
        db.query(func.sum(InventoryItem.quantity_on_hand))
        .scalar()
    ) or 0

    sku_count_with_stock = (
        db.query(func.count(InventoryItem.id))
        .filter(InventoryItem.quantity_on_hand > 0)
        .scalar()
    ) or 0

    inventory_metrics = {
        "total_on_hand": total_inventory,
        "skus_with_stock": sku_count_with_stock,
    }

    return DataResponse(data={
        "orders": orders_metrics,
        "manufacturing": manufacturing_metrics,
        "delivery": delivery_metrics,
        "inventory": inventory_metrics,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/audit-log")
def get_audit_log(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    entity_type: str | None = Query(None),
    action: str | None = Query(None),
):
    """
    Return recent audit log entries for operational visibility.
    """
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)

    entries = query.limit(limit).all()

    data = []
    for entry in entries:
        data.append({
            "id": str(entry.id),
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "action": entry.action,
            "performed_by": str(entry.performed_by) if entry.performed_by else None,
            "user_name": entry.user.full_name if entry.user else None,
            "payload": entry.payload,
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        })

    return DataResponse(data=data)
