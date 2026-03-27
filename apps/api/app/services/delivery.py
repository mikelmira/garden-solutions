"""
Delivery service for queue and delivery updates.
"""
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, DeliveryStatus
from app.models.order_item import OrderItem
from app.models.delivery_team import DeliveryTeam
from app.models.audit_log import AuditLog, AuditAction
from app.services.audit import AuditService
from app.core.exceptions import NotFoundException, ConflictException
from app.schemas.delivery import DeliveryComplete, DeliveryPartial, OrderItemDeliveredUpdate, DeliveryOutcomeRequest
from app.core.logging import log_delivery_completed, log_delivery_partial


class DeliveryService:
    """Service for delivery operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def _is_ready_for_delivery(self, order: Order) -> bool:
        """Ready = all items manufactured AND allocated."""
        return all(
            item.quantity_manufactured >= item.quantity_ordered
            and item.quantity_allocated >= item.quantity_ordered
            for item in order.items
        )

    def _delivery_state(self, order: Order) -> str:
        total_items = len(order.items)
        if total_items == 0:
            return "not_delivered"

        delivered_count = sum(1 for item in order.items if item.quantity_delivered >= item.quantity_ordered)
        if delivered_count == 0:
            return "not_delivered"
        if delivered_count == total_items:
            return "completed"
        return "partially_delivered"

    def get_latest_receiver_name(self, order_id: UUID) -> str | None:
        audit = (
            self.db.query(AuditLog)
            .filter(AuditLog.entity_type == "delivery", AuditLog.entity_id == str(order_id))
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        if not audit or not audit.payload:
            return None
        receiver_name = audit.payload.get("receiver_name")
        return receiver_name if isinstance(receiver_name, str) else None

    def get_queue(self, skip: int = 0, limit: int = 100) -> tuple[list[dict], int]:
        """
        Return ready-for-delivery orders (approved and fully manufactured) with remaining items.
        """
        orders = (
            self.db.query(Order)
            .filter(
                Order.status.in_(
                    [OrderStatus.APPROVED, OrderStatus.READY_FOR_DELIVERY, OrderStatus.PARTIALLY_DELIVERED]
                )
            )
            .order_by(Order.delivery_date.asc(), Order.created_at.asc())
            .all()
        )

        ready_orders = []
        for order in orders:
            if not self._is_ready_for_delivery(order):
                continue
            if all(item.quantity_delivered >= item.quantity_ordered for item in order.items):
                continue
            ready_orders.append(order)

        total = len(ready_orders)
        orders = ready_orders[skip:skip + limit]

        result: list[dict] = []
        for order in orders:
            items = []
            for item in order.items:
                remaining = item.quantity_ordered - item.quantity_delivered
                if remaining < 0:
                    remaining = 0
                items.append(
                    {
                        "id": item.id,
                        "order_id": item.order_id,
                        "sku_id": item.sku_id,
                        "quantity_ordered": item.quantity_ordered,
                        "quantity_manufactured": item.quantity_manufactured,
                        "quantity_delivered": item.quantity_delivered,
                        "remaining_to_deliver": remaining,
                        "sku": item.sku,
                        "product_name": item.sku.product.name if item.sku and item.sku.product else None,
                        "product_image": item.sku.product.image_url if item.sku and item.sku.product else None,
                        "sku_code": item.sku.code if item.sku else None,
                    }
                )

            status_value = order.status
            if order.status == OrderStatus.APPROVED and self._is_ready_for_delivery(order):
                status_value = OrderStatus.READY_FOR_DELIVERY

            result.append(
                {
                    "id": order.id,
                    "client_id": order.client_id,
                    "client_name": order.client.name if order.client else None,
                    "client_address": order.client.address if order.client else None,
                    "delivery_date": order.delivery_date,
                    "status": status_value,
                    "delivery_state": self._delivery_state(order),
                    "delivery_receiver_name": self.get_latest_receiver_name(order.id),
                    "items": items,
                }
            )

        return result, total

    def get_public_queue(self, team_code: str, delivery_date) -> tuple[list[dict], int]:
        team = self.db.query(DeliveryTeam).filter(DeliveryTeam.code == team_code, DeliveryTeam.is_active.is_(True)).first()
        if not team:
            raise NotFoundException("Delivery team not found")

        orders = (
            self.db.query(Order)
            .filter(Order.delivery_team_id == team.id)
            .filter(Order.delivery_date == delivery_date)
            .filter(Order.delivery_paused.is_(False))
            .filter(
                Order.status.in_(
                    [OrderStatus.APPROVED, OrderStatus.READY_FOR_DELIVERY, OrderStatus.PARTIALLY_DELIVERED]
                )
            )
            .order_by(Order.created_at.asc())
            .all()
        )

        ready_orders = []
        for order in orders:
            if not self._is_ready_for_delivery(order):
                continue
            if all(item.quantity_delivered >= item.quantity_ordered for item in order.items):
                continue
            ready_orders.append(order)

        result: list[dict] = []
        for order in ready_orders:
            items = []
            for item in order.items:
                remaining = item.quantity_ordered - item.quantity_delivered
                if remaining < 0:
                    remaining = 0
                items.append(
                    {
                        "id": item.id,
                        "order_id": item.order_id,
                        "sku_id": item.sku_id,
                        "quantity_ordered": item.quantity_ordered,
                        "quantity_manufactured": item.quantity_manufactured,
                        "quantity_delivered": item.quantity_delivered,
                        "remaining_to_deliver": remaining,
                        "sku": item.sku,
                        "product_name": item.sku.product.name if item.sku and item.sku.product else None,
                        "product_image": item.sku.product.image_url if item.sku and item.sku.product else None,
                        "sku_code": item.sku.code if item.sku else None,
                    }
                )

            status_value = order.status
            if order.status == OrderStatus.APPROVED and self._is_ready_for_delivery(order):
                status_value = OrderStatus.READY_FOR_DELIVERY

            result.append(
                {
                    "id": order.id,
                    "client_id": order.client_id,
                    "client_name": order.client.name if order.client else None,
                    "client_address": order.client.address if order.client else None,
                    "delivery_date": order.delivery_date,
                    "status": status_value,
                    "delivery_state": self._delivery_state(order),
                    "delivery_status": order.delivery_status,
                    "delivery_status_reason": order.delivery_status_reason,
                    "delivery_receiver_name": order.delivery_receiver_name,
                    "delivered_at": order.delivered_at,
                    "items": items,
                }
            )

        return result, len(result)

    def update_item_delivered(
        self,
        item_id: UUID,
        data: OrderItemDeliveredUpdate,
        performed_by: UUID,
    ) -> OrderItem:
        """Update delivered quantity for an order item (absolute)."""
        try:
            item = self.db.query(OrderItem).filter(OrderItem.id == item_id).first()
            if not item:
                raise NotFoundException(f"Order item with id {item_id} not found")

            if data.quantity_delivered < item.quantity_delivered:
                raise ConflictException("quantity_delivered cannot decrease")
            if data.quantity_delivered > item.quantity_allocated:
                raise ConflictException("quantity_delivered cannot exceed quantity_allocated — items must be allocated first")
            if data.quantity_delivered > item.quantity_manufactured:
                raise ConflictException("quantity_delivered cannot exceed quantity_manufactured")
            if data.quantity_delivered > item.quantity_ordered:
                raise ConflictException("quantity_delivered cannot exceed quantity_ordered")

            old_value = item.quantity_delivered
            item.quantity_delivered = data.quantity_delivered

            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="delivery",
                entity_id=item.order_id,
                performed_by=performed_by,
                payload={
                    "order_item_id": str(item.id),
                    "quantity_delivered": {"old": old_value, "new": data.quantity_delivered},
                },
            )

            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            raise

    def mark_delivery_complete(
        self,
        order_id: UUID,
        data: DeliveryComplete,
        performed_by: UUID,
    ) -> Order:
        """Mark delivery as complete if all items fully delivered."""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise NotFoundException(f"Order with id {order_id} not found")
            if order.status not in [OrderStatus.READY_FOR_DELIVERY, OrderStatus.PARTIALLY_DELIVERED, OrderStatus.APPROVED]:
                raise ConflictException("Order is not in a deliverable state")
            if not self._is_ready_for_delivery(order):
                raise ConflictException("Order is not ready for delivery")

            old_status = order.delivery_status
            delivered_summary: list[dict] = []
            for item in order.items:
                if item.quantity_manufactured < item.quantity_ordered:
                    raise ConflictException("Cannot complete delivery: items not fully manufactured")
                old_value = item.quantity_delivered
                item.quantity_delivered = item.quantity_ordered
                delivered_summary.append(
                    {"order_item_id": str(item.id), "quantity_delivered": {"old": old_value, "new": item.quantity_delivered}}
                )

            order.delivery_status = DeliveryStatus.DELIVERED
            order.delivery_status_reason = None
            order.delivery_receiver_name = data.receiver_name
            order.delivered_at = datetime.now(timezone.utc)
            order.status = OrderStatus.COMPLETED

            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="delivery",
                entity_id=order.id,
                performed_by=performed_by,
                payload={
                    "receiver_name": data.receiver_name,
                    "delivery_status": {"old": old_status, "new": DeliveryStatus.DELIVERED},
                    "order_status": OrderStatus.COMPLETED,
                    "items": delivered_summary,
                },
            )

            self.db.commit()
            self.db.refresh(order)

            log_delivery_completed(order_id=order.id, receiver_name=data.receiver_name, outcome="delivered")

            return order
        except Exception:
            self.db.rollback()
            raise

    def record_partial_delivery(
        self,
        order_id: UUID,
        data: DeliveryPartial,
        performed_by: UUID,
    ) -> Order:
        """Record a partial delivery attempt with item updates."""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise NotFoundException(f"Order with id {order_id} not found")
            if order.status not in [OrderStatus.READY_FOR_DELIVERY, OrderStatus.PARTIALLY_DELIVERED, OrderStatus.APPROVED]:
                raise ConflictException("Order is not in a deliverable state")
            if not self._is_ready_for_delivery(order):
                raise ConflictException("Order is not ready for delivery")

            old_status = order.delivery_status
            item_map = {item.id: item for item in order.items}
            delivered_summary: list[dict] = []
            for update in data.items:
                item = item_map.get(update.order_item_id)
                if not item:
                    raise NotFoundException(f"Order item with id {update.order_item_id} not found")
                if update.quantity_delivered < item.quantity_delivered:
                    raise ConflictException("quantity_delivered cannot decrease")
                if update.quantity_delivered > item.quantity_manufactured:
                    raise ConflictException("quantity_delivered cannot exceed quantity_manufactured")
                if update.quantity_delivered > item.quantity_ordered:
                    raise ConflictException("quantity_delivered cannot exceed quantity_ordered")

                old_value = item.quantity_delivered
                item.quantity_delivered = update.quantity_delivered
                delivered_summary.append(
                    {"order_item_id": str(item.id), "quantity_delivered": {"old": old_value, "new": update.quantity_delivered}}
                )

            order.delivery_status = DeliveryStatus.PARTIAL
            order.delivery_status_reason = data.reason
            order.delivery_receiver_name = data.receiver_name
            order.status = OrderStatus.PARTIALLY_DELIVERED

            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="delivery",
                entity_id=order.id,
                performed_by=performed_by,
                payload={
                    "receiver_name": data.receiver_name,
                    "reason": data.reason,
                    "delivery_status": {"old": old_status, "new": DeliveryStatus.PARTIAL},
                    "order_status": OrderStatus.PARTIALLY_DELIVERED,
                    "items": delivered_summary,
                },
            )

            self.db.commit()
            self.db.refresh(order)

            log_delivery_partial(
                order_id=order.id,
                reason=data.reason,
                items_delivered=len(data.items),
            )

            return order
        except Exception:
            self.db.rollback()
            raise

    def record_public_outcome(self, order_id: UUID, data: DeliveryOutcomeRequest) -> Order:
        try:
            team = self.db.query(DeliveryTeam).filter(DeliveryTeam.code == data.team_code, DeliveryTeam.is_active.is_(True)).first()
            if not team:
                raise NotFoundException("Delivery team not found")

            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise NotFoundException(f"Order with id {order_id} not found")
            if order.delivery_team_id != team.id:
                raise ConflictException("Order is not assigned to this delivery team")
            if order.status not in [OrderStatus.READY_FOR_DELIVERY, OrderStatus.PARTIALLY_DELIVERED, OrderStatus.APPROVED]:
                raise ConflictException("Order is not in a deliverable state")
            if not self._is_ready_for_delivery(order):
                raise ConflictException("Order is not ready for delivery")

            outcome = data.outcome
            if outcome not in [DeliveryStatus.DELIVERED, DeliveryStatus.PARTIAL, DeliveryStatus.NOT_DELIVERED]:
                raise ConflictException("Invalid delivery outcome")

            items_summary: list[dict] = []
            if outcome == DeliveryStatus.DELIVERED:
                for item in order.items:
                    if item.quantity_manufactured < item.quantity_ordered:
                        raise ConflictException("Cannot deliver: items not fully manufactured")
                    old_value = item.quantity_delivered
                    item.quantity_delivered = item.quantity_ordered
                    items_summary.append(
                        {"order_item_id": str(item.id), "quantity_delivered": {"old": old_value, "new": item.quantity_delivered}}
                    )
                order.delivery_status = DeliveryStatus.DELIVERED
                order.delivery_status_reason = None
                order.delivery_receiver_name = data.receiver_name
                order.delivered_at = datetime.now(timezone.utc)
                order.status = OrderStatus.COMPLETED

            elif outcome == DeliveryStatus.PARTIAL:
                if not data.items:
                    raise ConflictException("Partial delivery requires items")
                if not data.reason:
                    raise ConflictException("Partial delivery requires reason")
                item_map = {item.id: item for item in order.items}
                for update in data.items:
                    item = item_map.get(update.order_item_id)
                    if not item:
                        raise NotFoundException(f"Order item with id {update.order_item_id} not found")
                    if update.quantity_delivered < item.quantity_delivered:
                        raise ConflictException("quantity_delivered cannot decrease")
                    if update.quantity_delivered > item.quantity_manufactured:
                        raise ConflictException("quantity_delivered cannot exceed quantity_manufactured")
                    if update.quantity_delivered > item.quantity_ordered:
                        raise ConflictException("quantity_delivered cannot exceed quantity_ordered")
                    old_value = item.quantity_delivered
                    item.quantity_delivered = update.quantity_delivered
                    items_summary.append(
                        {"order_item_id": str(item.id), "quantity_delivered": {"old": old_value, "new": update.quantity_delivered}}
                    )
                order.delivery_status = DeliveryStatus.PARTIAL
                order.delivery_status_reason = data.reason
                order.delivery_receiver_name = data.receiver_name
                order.status = OrderStatus.PARTIALLY_DELIVERED

            elif outcome == DeliveryStatus.NOT_DELIVERED:
                if not data.reason:
                    raise ConflictException("Not delivered requires reason")
                order.delivery_status = DeliveryStatus.NOT_DELIVERED
                order.delivery_status_reason = data.reason
                order.delivery_receiver_name = data.receiver_name

            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="delivery",
                entity_id=order.id,
                performed_by=None,
                payload={
                    "team_code": data.team_code,
                    "outcome": outcome,
                    "receiver_name": data.receiver_name,
                    "reason": data.reason,
                    "items": items_summary,
                },
            )

            self.db.commit()
            self.db.refresh(order)

            if outcome == DeliveryStatus.DELIVERED:
                log_delivery_completed(order_id=order.id, receiver_name=data.receiver_name, outcome="delivered")
            elif outcome == DeliveryStatus.PARTIAL:
                log_delivery_partial(order_id=order.id, reason=data.reason, items_delivered=len(data.items or []))

            return order
        except Exception:
            self.db.rollback()
            raise
