"""
Manufacturing service for queue and order item updates.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.audit_log import AuditAction
from app.services.audit import AuditService
from app.core.exceptions import NotFoundException, ConflictException


class ManufacturingService:
    """Service for manufacturing operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def get_queue(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """
        Return approved orders with items and manufacturing counts.
        """
        query = self.db.query(Order).filter(Order.status == OrderStatus.APPROVED)
        total = query.count()
        orders = query.order_by(Order.delivery_date.asc(), Order.created_at.asc()).offset(skip).limit(limit).all()

        result: list[dict] = []
        for order in orders:
            items = []
            for item in order.items:
                remaining = item.quantity_ordered - item.quantity_manufactured
                if remaining < 0:
                    remaining = 0
                items.append(
                    {
                        "id": item.id,
                        "order_id": item.order_id,
                        "sku_id": item.sku_id,
                        "quantity_ordered": item.quantity_ordered,
                        "quantity_manufactured": item.quantity_manufactured,
                        "remaining_to_manufacture": remaining,
                        "sku": item.sku,
                    }
                )

            result.append(
                {
                    "id": order.id,
                    "client_id": order.client_id,
                    "client_name": order.client.name if order.client else None,
                    "delivery_date": order.delivery_date,
                    "status": order.status,
                    "items": items,
                }
            )

        return result, total

    def update_item_manufactured(
        self,
        item_id: UUID,
        quantity_manufactured: int,
        performed_by: UUID,
    ) -> OrderItem:
        """
        Update an order item's manufactured quantity with validation.

        Rules enforced per docs:
        - 0 <= quantity_manufactured <= quantity_ordered
        - Monotonically increasing (cannot decrease)
        - Does NOT change Order.status (derived status per STATUS_MODEL.md)
        - Writes AuditLog in same transaction (atomic)
        """
        item = self.db.query(OrderItem).filter(OrderItem.id == item_id).first()
        if not item:
            raise NotFoundException(f"Order item with id {item_id} not found")

        # Validation: cannot exceed quantity_ordered
        if quantity_manufactured > item.quantity_ordered:
            raise ConflictException("quantity_manufactured cannot exceed quantity_ordered")

        # Validation: monotonically increasing (cannot decrease)
        if quantity_manufactured < item.quantity_manufactured:
            raise ConflictException("quantity_manufactured cannot decrease (monotonic increase only)")

        old_value = item.quantity_manufactured

        # Atomic transaction: update item + audit log
        try:
            item.quantity_manufactured = quantity_manufactured

            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="order_item",
                entity_id=item.id,
                performed_by=performed_by,
                payload={"quantity_manufactured": {"old": old_value, "new": quantity_manufactured}},
            )

            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            raise
