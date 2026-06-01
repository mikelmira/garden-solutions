"""
Painting Day Plan service.

Outstanding paint demand:
- For each order_item where status >= IN_PRODUCTION:
    outstanding = quantity_manufactured - quantity_painted - planned_today
- "planned_today" is the quantity already on today's painting plan for the
  same order_item, so a refresh of the demand list doesn't double-count.

Auto-advance:
- When recording completion that takes an order's total quantity_painted
  to >= quantity_ordered across all items, advance order status to
  READY_FOR_DELIVERY (if currently PAINTING).
- When today's plan is first created including items from an order that's
  still IN_PRODUCTION but has all items moulded, advance to PAINTING.
"""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.painting_day import PaintingDay, PaintingDayItem
from app.models.shopify import ShopifyOrder
from app.core.exceptions import ConflictException, NotFoundException
from app.services.audit import AuditService
from app.services.plan_emails import send_painting_plan_email


def _build_display_string(qty: int, product_name: str, size: str | None, color: str | None) -> str:
    parts = [product_name]
    if size:
        parts.append(size)
    if color:
        parts.append(color)
    return f"{qty}x {' - '.join(parts)}"


class PaintingDayService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    # ------------------------------------------------------------------
    # Demand
    # ------------------------------------------------------------------
    def get_outstanding_demand(self, plan_date: date | None = None) -> dict:
        """
        Compute outstanding paint demand per order_item.

        Outstanding = quantity_ordered - quantity_painted - planned_today

        Includes orders in APPROVED, IN_PRODUCTION, or PAINTING. The codebase
        leaves most live orders in APPROVED throughout the lifecycle — orders
        only move to PAINTING once a paint plan touches them, and to
        READY_FOR_DELIVERY once fully painted.
        """
        target_date = plan_date or date.today()

        # planned_today map: order_item_id -> sum of quantity_planned across
        # today's painting plan items (so we don't double-count).
        plan = self.get_plan_by_date(target_date)
        planned_today: dict[UUID, int] = {}
        if plan:
            for item in plan.items:
                planned_today[item.order_item_id] = (
                    planned_today.get(item.order_item_id, 0) + item.quantity_planned
                )

        orders = (
            self.db.query(Order)
            .filter(
                Order.status.in_(
                    [OrderStatus.APPROVED, OrderStatus.IN_PRODUCTION, OrderStatus.PAINTING]
                )
            )
            .order_by(Order.created_at.asc())
            .all()
        )

        # Pre-load shopify_orders so customer_name surfaces in the response.
        order_ids = [o.id for o in orders]
        shopify_map: dict[UUID, ShopifyOrder] = {}
        if order_ids:
            rows = (
                self.db.query(ShopifyOrder)
                .filter(ShopifyOrder.internal_order_id.in_(order_ids))
                .all()
            )
            shopify_map = {r.internal_order_id: r for r in rows if r.internal_order_id}

        items_out: list[dict] = []
        total_units = 0
        for order in orders:
            if order.client:
                label = order.client.name
            elif order.store:
                label = f"Store: {order.store.name}"
            else:
                label = "Unknown"
            customer_name = shopify_map.get(order.id).customer_name if shopify_map.get(order.id) else None

            for oi in order.items:
                already_planned = planned_today.get(oi.id, 0)
                outstanding = oi.quantity_ordered - oi.quantity_painted - already_planned
                if outstanding <= 0:
                    continue
                sku = oi.sku
                product_name = sku.product.name if sku and sku.product else "Unknown"
                size = sku.size if sku else None
                color = sku.color if sku else None
                items_out.append({
                    "order_item_id": oi.id,
                    "order_id": order.id,
                    "order_created_at": order.created_at,
                    "client_or_store_label": label,
                    "customer_name": customer_name,
                    "sku_code": sku.code if sku else "Unknown",
                    "product_name": product_name,
                    "size": size,
                    "color": color,
                    "display_string": _build_display_string(outstanding, product_name, size, color),
                    "quantity_outstanding": outstanding,
                })
                total_units += outstanding

        return {
            "items": items_out,
            "total_items": len(items_out),
            "total_units": total_units,
        }

    # ------------------------------------------------------------------
    # Plan queries
    # ------------------------------------------------------------------
    def get_plan_by_date(self, plan_date: date) -> PaintingDay | None:
        return (
            self.db.query(PaintingDay)
            .filter(PaintingDay.plan_date == plan_date)
            .first()
        )

    def get_today_plan(self) -> PaintingDay | None:
        return self.get_plan_by_date(date.today())

    # ------------------------------------------------------------------
    # Plan create / add items
    # ------------------------------------------------------------------
    def _validate_items(self, items: list[dict], existing_plan: PaintingDay | None) -> None:
        # Capacity per order_item = quantity_ordered - quantity_painted - already_planned_today
        already_planned_map: dict[UUID, int] = {}
        if existing_plan:
            for it in existing_plan.items:
                already_planned_map[it.order_item_id] = (
                    already_planned_map.get(it.order_item_id, 0) + it.quantity_planned
                )

        order_item_ids = [it["order_item_id"] for it in items]
        rows = (
            self.db.query(OrderItem)
            .filter(OrderItem.id.in_(order_item_ids))
            .all()
        )
        by_id = {r.id: r for r in rows}

        for it in items:
            qty = it["quantity_planned"]
            if qty <= 0:
                raise ConflictException("quantity_planned must be > 0")
            oi = by_id.get(it["order_item_id"])
            if not oi:
                raise NotFoundException(f"order_item {it['order_item_id']} not found")
            capacity = (
                oi.quantity_ordered
                - oi.quantity_painted
                - already_planned_map.get(oi.id, 0)
            )
            if qty > capacity:
                raise ConflictException(
                    f"Cannot plan {qty} for order_item {oi.id}: only {capacity} available to paint"
                )

    def create_plan(
        self,
        plan_date: date | None,
        items: list[dict],
        created_by: UUID,
    ) -> PaintingDay:
        target_date = plan_date or date.today()

        if self.get_plan_by_date(target_date):
            raise ConflictException(f"Painting plan for {target_date} already exists")

        self._validate_items(items, existing_plan=None)

        plan = PaintingDay(plan_date=target_date, created_by=created_by)
        self.db.add(plan)
        self.db.flush()

        touched_order_ids: set[UUID] = set()
        for it in items:
            row = PaintingDayItem(
                painting_day_id=plan.id,
                order_item_id=it["order_item_id"],
                quantity_planned=it["quantity_planned"],
                quantity_completed=0,
            )
            self.db.add(row)
            oi = self.db.query(OrderItem).filter(OrderItem.id == it["order_item_id"]).first()
            if oi:
                touched_order_ids.add(oi.order_id)

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="painting_day",
            entity_id=plan.id,
            performed_by=created_by,
            payload={"plan_date": str(target_date), "items_count": len(items)},
        )

        # Advance any in_production orders that are now planned for paint.
        for order_id in touched_order_ids:
            self._maybe_advance_to_painting(order_id, performed_by=created_by)

        self.db.commit()
        self.db.refresh(plan)

        # Best-effort: email today's painting plan to configured recipients.
        try:
            send_painting_plan_email(self.db, plan)
        except Exception:
            pass

        return plan

    def add_items_to_plan(
        self,
        plan: PaintingDay,
        items: list[dict],
        added_by: UUID,
    ) -> PaintingDay:
        self._validate_items(items, existing_plan=plan)

        touched_order_ids: set[UUID] = set()
        for it in items:
            row = PaintingDayItem(
                painting_day_id=plan.id,
                order_item_id=it["order_item_id"],
                quantity_planned=it["quantity_planned"],
                quantity_completed=0,
            )
            self.db.add(row)
            oi = self.db.query(OrderItem).filter(OrderItem.id == it["order_item_id"]).first()
            if oi:
                touched_order_ids.add(oi.order_id)

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="painting_day",
            entity_id=plan.id,
            performed_by=added_by,
            payload={"action": "add_items", "items_added": len(items)},
        )

        for order_id in touched_order_ids:
            self._maybe_advance_to_painting(order_id, performed_by=added_by)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------
    def update_item_completion(
        self,
        item_id: UUID,
        quantity_completed: int,
        performed_by: UUID | None,
    ) -> PaintingDayItem:
        item = (
            self.db.query(PaintingDayItem)
            .filter(PaintingDayItem.id == item_id)
            .first()
        )
        if not item:
            raise NotFoundException(f"Painting day item {item_id} not found")

        if quantity_completed < 0:
            raise ConflictException("quantity_completed cannot be negative")
        if quantity_completed > item.quantity_planned:
            raise ConflictException(
                f"Cannot complete {quantity_completed} — only {item.quantity_planned} planned"
            )

        old_completed = item.quantity_completed
        delta = quantity_completed - old_completed
        if delta == 0:
            return item

        item.quantity_completed = quantity_completed

        # Propagate to the order_item.quantity_painted (cap at quantity_ordered).
        oi = (
            self.db.query(OrderItem)
            .filter(OrderItem.id == item.order_item_id)
            .first()
        )
        if oi:
            new_painted = max(0, min(oi.quantity_ordered, oi.quantity_painted + delta))
            oi.quantity_painted = new_painted
            self.db.flush()
            self._maybe_advance_to_ready_for_delivery(oi.order_id, performed_by=performed_by)

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="painting_day_item",
            entity_id=item.id,
            performed_by=performed_by,
            payload={
                "quantity_completed": {"old": old_completed, "new": quantity_completed},
                "delta": delta,
            },
        )

        self.db.commit()
        self.db.refresh(item)
        return item

    # ------------------------------------------------------------------
    # Order status auto-advance helpers
    # ------------------------------------------------------------------
    def _maybe_advance_to_painting(self, order_id: UUID, performed_by: UUID | None) -> None:
        """If order is APPROVED or IN_PRODUCTION, move to PAINTING when it lands on a paint plan.

        Note: the existing codebase typically leaves orders in APPROVED until late
        in the lifecycle (it does not auto-transition APPROVED -> IN_PRODUCTION).
        We treat both as valid sources for the PAINTING transition.
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status not in (OrderStatus.APPROVED, OrderStatus.IN_PRODUCTION):
            return
        if not order.items:
            return
        old_status = order.status
        order.status = OrderStatus.PAINTING
        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="order",
            entity_id=order.id,
            performed_by=performed_by,
            payload={"status": {"old": old_status, "new": OrderStatus.PAINTING}},
        )

    def _maybe_advance_to_ready_for_delivery(
        self, order_id: UUID, performed_by: UUID | None
    ) -> None:
        """If order is PAINTING and all items fully painted, move to READY_FOR_DELIVERY."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != OrderStatus.PAINTING:
            return
        if not order.items:
            return
        all_painted = all(
            oi.quantity_painted >= oi.quantity_ordered for oi in order.items
        )
        if not all_painted:
            return
        order.status = OrderStatus.READY_FOR_DELIVERY
        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="order",
            entity_id=order.id,
            performed_by=performed_by,
            payload={
                "status": {"old": OrderStatus.PAINTING, "new": OrderStatus.READY_FOR_DELIVERY}
            },
        )

    # ------------------------------------------------------------------
    # Response shaping
    # ------------------------------------------------------------------
    def format_plan_response(self, plan: PaintingDay) -> dict:
        # Pre-fetch shopify_orders for customer names.
        order_ids = {item.order_item.order_id for item in plan.items if item.order_item}
        shopify_map: dict[UUID, ShopifyOrder] = {}
        if order_ids:
            rows = (
                self.db.query(ShopifyOrder)
                .filter(ShopifyOrder.internal_order_id.in_(list(order_ids)))
                .all()
            )
            shopify_map = {r.internal_order_id: r for r in rows if r.internal_order_id}

        items_out = []
        total_planned = 0
        total_completed = 0
        for item in plan.items:
            oi = item.order_item
            order = oi.order if oi else None
            sku = oi.sku if oi else None
            product_name = sku.product.name if sku and sku.product else "Unknown"
            size = sku.size if sku else None
            color = sku.color if sku else None
            if order and order.client:
                label = order.client.name
            elif order and order.store:
                label = f"Store: {order.store.name}"
            else:
                label = None
            customer_name = (
                shopify_map[order.id].customer_name
                if order and order.id in shopify_map
                else None
            )
            items_out.append({
                "id": item.id,
                "order_item_id": item.order_item_id,
                "quantity_planned": item.quantity_planned,
                "quantity_completed": item.quantity_completed,
                "remaining": item.quantity_planned - item.quantity_completed,
                "order_id": order.id if order else None,
                "client_or_store_label": label,
                "customer_name": customer_name,
                "sku_code": sku.code if sku else None,
                "product_name": product_name,
                "size": size,
                "color": color,
                "display_string": _build_display_string(
                    item.quantity_planned, product_name, size, color
                ),
            })
            total_planned += item.quantity_planned
            total_completed += item.quantity_completed

        return {
            "id": plan.id,
            "plan_date": plan.plan_date,
            "created_by": plan.created_by,
            "created_at": plan.created_at,
            "items": items_out,
            "total_planned": total_planned,
            "total_completed": total_completed,
        }
