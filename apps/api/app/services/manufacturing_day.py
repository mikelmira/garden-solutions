"""
Manufacturing Day Plan service.

Handles:
- Computing outstanding demand from approved orders
- Creating daily manufacturing plans (snapshots)
- Recording completion against plan items
- Triggering inventory updates on completion
"""
from datetime import date, datetime, timezone
from uuid import UUID
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.manufacturing_day import ManufacturingDay, ManufacturingDayItem
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.sku import SKU
from app.models.user import User
from app.services.inventory import InventoryService
from app.services.audit import AuditService
from app.models.audit_log import AuditAction
from app.core.exceptions import NotFoundException, ConflictException
from app.core.logging import log_manufacturing_plan_created, log_manufacturing_completion, log_manufacturing_demand_generated


def _build_sku_display_string(qty: int, product_name: str, size: str, color: str) -> str:
    """Build display string like '5x Egg Pot - Small Green'."""
    return f"{qty}x {product_name} - {size} {color}"


class ManufacturingDayService:
    """Service for manufacturing day plan operations."""

    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.audit_service = AuditService(db)

    def get_outstanding_demand(self) -> dict:
        """
        Compute outstanding demand per SKU from approved orders.

        Outstanding for an item = quantity_ordered - quantity_allocated

        Returns aggregated demand with per-order breakdown.
        """
        # Get all approved orders with their items
        orders = (
            self.db.query(Order)
            .filter(Order.status == OrderStatus.APPROVED)
            .order_by(Order.created_at.asc())
            .all()
        )

        # Aggregate by SKU
        sku_demand: dict[UUID, dict] = {}

        for order in orders:
            # Determine client/store label
            if order.client:
                label = order.client.name
                label_type = "client"
            elif order.store:
                label = f"Store: {order.store.name}"
                label_type = "store"
            else:
                label = "Unknown"
                label_type = "unknown"

            for item in order.items:
                outstanding = item.quantity_ordered - item.quantity_allocated
                if outstanding <= 0:
                    continue

                sku = item.sku
                if not sku:
                    continue

                sku_id = item.sku_id

                if sku_id not in sku_demand:
                    sku_demand[sku_id] = {
                        "sku_id": sku_id,
                        "sku_code": sku.code,
                        "product_name": sku.product.name if sku.product else "Unknown",
                        "size": sku.size,
                        "color": sku.color,
                        "total_outstanding": 0,
                        "breakdown": [],
                    }

                sku_demand[sku_id]["total_outstanding"] += outstanding
                sku_demand[sku_id]["breakdown"].append({
                    "item_id": item.id,  # Added for frontend updates
                    "order_id": order.id,
                    "order_created_at": order.created_at,
                    "client_or_store_label": label,
                    "client_or_store_type": label_type,
                    "quantity_outstanding": outstanding,
                })

        # Build final response
        skus = []
        total_units = 0

        for sku_data in sku_demand.values():
            total = sku_data["total_outstanding"]
            total_units += total
            sku_data["display_string"] = _build_sku_display_string(
                total,
                sku_data["product_name"],
                sku_data["size"],
                sku_data["color"],
            )
            skus.append(sku_data)

        # Sort by total_outstanding descending for priority
        skus.sort(key=lambda x: x["total_outstanding"], reverse=True)

        log_manufacturing_demand_generated(total_skus=len(skus), total_units=total_units)

        return {
            "skus": skus,
            "total_skus": len(skus),
            "total_units": total_units,
        }

    def get_outstanding_for_sku(self, sku_id: UUID) -> int:
        """Get total outstanding demand for a specific SKU."""
        demand = self.get_outstanding_demand()
        for sku in demand["skus"]:
            if sku["sku_id"] == sku_id:
                return sku["total_outstanding"]
        return 0

    def get_plan_by_date(self, plan_date: date) -> ManufacturingDay | None:
        """Get manufacturing plan for a specific date."""
        return (
            self.db.query(ManufacturingDay)
            .filter(ManufacturingDay.plan_date == plan_date)
            .first()
        )

    def get_today_plan(self) -> ManufacturingDay | None:
        """Get today's manufacturing plan."""
        today = date.today()
        return self.get_plan_by_date(today)

    def create_plan(
        self,
        plan_date: date | None,
        items: list[dict],  # [{sku_id, quantity_planned}, ...]
        created_by: UUID,
    ) -> ManufacturingDay:
        """
        Create a new manufacturing day plan.

        Validation:
        - Plan date must not already exist
        - Quantities must be > 0
        - Quantities must not exceed outstanding demand
        """
        target_date = plan_date or date.today()

        # Check if plan already exists
        existing = self.get_plan_by_date(target_date)
        if existing:
            raise ConflictException(f"Manufacturing plan for {target_date} already exists")

        # Validate items against outstanding demand
        demand = self.get_outstanding_demand()
        demand_by_sku = {sku["sku_id"]: sku["total_outstanding"] for sku in demand["skus"]}

        for item in items:
            sku_id = item["sku_id"]
            qty_planned = item["quantity_planned"]

            if qty_planned <= 0:
                raise ConflictException(f"Quantity planned must be > 0")

            outstanding = demand_by_sku.get(sku_id, 0)
            if qty_planned > outstanding:
                raise ConflictException(
                    f"Cannot plan {qty_planned} for SKU {sku_id} - only {outstanding} outstanding"
                )

        # Create plan
        plan = ManufacturingDay(
            plan_date=target_date,
            created_by=created_by,
        )
        self.db.add(plan)
        self.db.flush()

        # Create plan items
        for item in items:
            plan_item = ManufacturingDayItem(
                manufacturing_day_id=plan.id,
                sku_id=item["sku_id"],
                quantity_planned=item["quantity_planned"],
                quantity_completed=0,
            )
            self.db.add(plan_item)

        # Audit log
        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="manufacturing_day",
            entity_id=plan.id,
            performed_by=created_by,
            payload={
                "plan_date": str(target_date),
                "items_count": len(items),
            },
        )

        self.db.commit()
        self.db.refresh(plan)

        log_manufacturing_plan_created(
            plan_id=plan.id,
            plan_date=target_date,
            items_count=len(items),
            created_by=created_by,
        )

        return plan

    def add_items_to_plan(
        self,
        plan: ManufacturingDay,
        items: list[dict],  # [{sku_id, quantity_planned}, ...]
        added_by: UUID,
    ) -> ManufacturingDay:
        """
        Add items to an existing manufacturing day plan.

        Validation:
        - Quantities must be > 0
        - Quantities must not exceed outstanding demand
        - SKU must not already be in the plan
        """
        # Get existing SKU IDs in plan
        existing_sku_ids = {item.sku_id for item in plan.items}

        # Validate items against outstanding demand
        demand = self.get_outstanding_demand()
        demand_by_sku = {sku["sku_id"]: sku["total_outstanding"] for sku in demand["skus"]}

        for item in items:
            sku_id = item["sku_id"]
            qty_planned = item["quantity_planned"]

            if qty_planned <= 0:
                raise ConflictException("Quantity planned must be > 0")

            if sku_id in existing_sku_ids:
                raise ConflictException(f"SKU {sku_id} is already in today's plan")

            outstanding = demand_by_sku.get(sku_id, 0)
            if qty_planned > outstanding:
                raise ConflictException(
                    f"Cannot plan {qty_planned} for SKU {sku_id} - only {outstanding} outstanding"
                )

        # Add new items to plan
        for item in items:
            plan_item = ManufacturingDayItem(
                manufacturing_day_id=plan.id,
                sku_id=item["sku_id"],
                quantity_planned=item["quantity_planned"],
                quantity_completed=0,
            )
            self.db.add(plan_item)

        # Audit log
        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="manufacturing_day",
            entity_id=plan.id,
            performed_by=added_by,
            payload={
                "action": "add_items",
                "items_added": len(items),
            },
        )

        self.db.commit()
        self.db.refresh(plan)

        return plan

    def update_item_completion(
        self,
        item_id: UUID,
        quantity_completed: int,
        performed_by: UUID | None,
    ) -> ManufacturingDayItem:
        """
        Update completed quantity for a manufacturing day item.

        When completion increases (delta > 0):
        - Update inventory with delta
        - Trigger FIFO allocation

        When completion decreases (delta < 0):
        - Subtract from inventory
        - Re-run FIFO allocation for that SKU
        """
        item = (
            self.db.query(ManufacturingDayItem)
            .filter(ManufacturingDayItem.id == item_id)
            .first()
        )
        if not item:
            raise NotFoundException(f"Manufacturing day item {item_id} not found")

        # Guardrail: strict validation instead of silent clamping
        if quantity_completed < 0:
            raise ConflictException("Quantity completed cannot be negative")
        if quantity_completed > item.quantity_planned:
            raise ConflictException(
                f"Cannot complete {quantity_completed} — only {item.quantity_planned} planned for this item"
            )

        old_completed = item.quantity_completed
        delta = quantity_completed - old_completed

        # Update item
        item.quantity_completed = quantity_completed

        # Update quantity_manufactured on corresponding order items
        # so delivery readiness checks pass (they require both manufactured AND allocated)
        self._update_order_items_manufactured(item.sku_id, quantity_completed)

        # If delta > 0, add to inventory and run allocation
        if delta > 0:
            self.inventory_service.add_inventory(
                sku_id=item.sku_id,
                quantity=delta,
                performed_by=performed_by,
            )
            # Trigger FIFO allocation for this SKU
            self.inventory_service.allocate_inventory_fifo(
                sku_ids=[item.sku_id],
                performed_by=performed_by,
            )
        elif delta < 0:
            # Decrease: subtract from inventory and re-run allocation
            self.inventory_service.subtract_inventory(
                sku_id=item.sku_id,
                quantity=abs(delta),
                performed_by=performed_by,
            )
            # Re-run FIFO allocation to potentially deallocate if stock went negative
            self.inventory_service.allocate_inventory_fifo(
                sku_ids=[item.sku_id],
                performed_by=performed_by,
            )

        # Audit log
        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="manufacturing_day_item",
            entity_id=item.id,
            performed_by=performed_by,
            payload={
                "quantity_completed": {
                    "old": old_completed,
                    "new": quantity_completed,
                },
                "delta": delta,
            },
        )

        self.db.commit()
        self.db.refresh(item)

        log_manufacturing_completion(
            plan_item_id=item.id,
            sku_id=item.sku_id,
            old_completed=old_completed,
            new_completed=quantity_completed,
            delta=delta,
        )

        return item

    def _update_order_items_manufactured(self, sku_id: UUID, total_completed: int) -> None:
        """
        Distribute manufactured quantity across approved order items for this SKU (FIFO).

        Uses the same FIFO order as inventory allocation: oldest orders first.
        Each order item gets min(quantity_ordered, remaining_completed) as quantity_manufactured.
        """
        # Get all approved order items for this SKU, oldest order first
        order_items = (
            self.db.query(OrderItem)
            .join(Order)
            .filter(
                OrderItem.sku_id == sku_id,
                Order.status == OrderStatus.APPROVED,
            )
            .order_by(Order.created_at.asc(), OrderItem.created_at.asc())
            .all()
        )

        remaining = total_completed
        for oi in order_items:
            if remaining <= 0:
                oi.quantity_manufactured = 0
            else:
                qty = min(oi.quantity_ordered, remaining)
                oi.quantity_manufactured = qty
                remaining -= qty

        self.db.flush()

    def format_plan_response(self, plan: ManufacturingDay) -> dict:
        """Format a manufacturing day plan for API response."""
        items = []
        total_planned = 0
        total_completed = 0

        for item in plan.items:
            sku = item.sku
            product_name = sku.product.name if sku and sku.product else "Unknown"

            items.append({
                "id": item.id,
                "sku_id": item.sku_id,
                "sku_code": sku.code if sku else "Unknown",
                "product_name": product_name,
                "size": sku.size if sku else "",
                "color": sku.color if sku else "",
                "quantity_planned": item.quantity_planned,
                "quantity_completed": item.quantity_completed,
                "display_string": _build_sku_display_string(
                    item.quantity_planned,
                    product_name,
                    sku.size if sku else "",
                    sku.color if sku else "",
                ),
                "remaining": item.quantity_planned - item.quantity_completed,
            })
            total_planned += item.quantity_planned
            total_completed += item.quantity_completed

        return {
            "id": plan.id,
            "plan_date": plan.plan_date,
            "created_by": plan.created_by,
            "created_at": plan.created_at,
            "items": items,
            "total_planned": total_planned,
            "total_completed": total_completed,
        }
