"""
Structured lifecycle logging for platform observability.

Provides a lifecycle logger that emits structured JSON-style logs for key
operational events: order creation, approval, manufacturing, inventory,
delivery. These logs make the full product lifecycle traceable via log
aggregation without relying solely on the audit_logs database table.
"""
import logging
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


class _UUIDEncoder(json.JSONEncoder):
    """JSON encoder that handles UUID serialization."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Create the lifecycle logger - separate from request logger
lifecycle_logger = logging.getLogger("app.lifecycle")


def _log_event(event: str, **kwargs: Any) -> None:
    """Emit a structured lifecycle log entry."""
    payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }
    lifecycle_logger.info(json.dumps(payload, cls=_UUIDEncoder))


# ── Order events ──────────────────────────────────────────────

def log_order_created(
    order_id: UUID,
    client_name: str | None,
    total_price: Any,
    item_count: int,
    created_by: UUID | None = None,
) -> None:
    _log_event(
        "order.created",
        order_id=order_id,
        client_name=client_name,
        total_price=str(total_price),
        item_count=item_count,
        created_by=created_by,
    )


def log_order_approved(
    order_id: UUID,
    approved_by: UUID | None = None,
) -> None:
    _log_event(
        "order.approved",
        order_id=order_id,
        approved_by=approved_by,
    )


def log_order_cancelled(
    order_id: UUID,
    reason: str | None = None,
    cancelled_by: UUID | None = None,
    inventory_returned: int = 0,
) -> None:
    _log_event(
        "order.cancelled",
        order_id=order_id,
        reason=reason,
        cancelled_by=cancelled_by,
        inventory_returned=inventory_returned,
    )


# ── Manufacturing events ──────────────────────────────────────

def log_manufacturing_plan_created(
    plan_id: UUID,
    plan_date: Any,
    items_count: int,
    created_by: UUID | None = None,
) -> None:
    _log_event(
        "manufacturing.plan_created",
        plan_id=plan_id,
        plan_date=str(plan_date),
        items_count=items_count,
        created_by=created_by,
    )


def log_manufacturing_completion(
    plan_item_id: UUID,
    sku_id: UUID,
    old_completed: int,
    new_completed: int,
    delta: int,
) -> None:
    _log_event(
        "manufacturing.completion_recorded",
        plan_item_id=plan_item_id,
        sku_id=sku_id,
        old_completed=old_completed,
        new_completed=new_completed,
        delta=delta,
    )


def log_manufacturing_demand_generated(
    total_skus: int,
    total_units: int,
) -> None:
    _log_event(
        "manufacturing.demand_generated",
        total_skus=total_skus,
        total_units=total_units,
    )


# ── Inventory events ──────────────────────────────────────────

def log_inventory_updated(
    sku_id: UUID,
    old_quantity: int,
    new_quantity: int,
    reason: str = "manufacturing",
) -> None:
    _log_event(
        "inventory.updated",
        sku_id=sku_id,
        old_quantity=old_quantity,
        new_quantity=new_quantity,
        reason=reason,
    )


def log_inventory_allocation(
    total_allocated: int,
    orders_updated: int,
) -> None:
    _log_event(
        "inventory.allocation_updated",
        total_allocated=total_allocated,
        orders_updated=orders_updated,
    )


# ── Delivery events ──────────────────────────────────────────

def log_delivery_assigned(
    order_id: UUID,
    team_id: UUID,
    assigned_by: UUID | None = None,
) -> None:
    _log_event(
        "delivery.assigned",
        order_id=order_id,
        team_id=team_id,
        assigned_by=assigned_by,
    )


def log_delivery_completed(
    order_id: UUID,
    receiver_name: str | None = None,
    outcome: str = "delivered",
) -> None:
    _log_event(
        "delivery.completed",
        order_id=order_id,
        receiver_name=receiver_name,
        outcome=outcome,
    )


def log_delivery_partial(
    order_id: UUID,
    reason: str | None = None,
    items_delivered: int = 0,
) -> None:
    _log_event(
        "delivery.partial",
        order_id=order_id,
        reason=reason,
        items_delivered=items_delivered,
    )
