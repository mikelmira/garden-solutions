"""
Inventory service for stock management and FIFO allocation.

Key responsibilities:
- Manage global inventory levels per SKU
- Auto-allocate inventory to orders FIFO by order created_at
- Handle cancellation returns and reallocation
"""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.inventory import InventoryItem
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.sku import SKU
from app.services.audit import AuditService
from app.models.audit_log import AuditAction
from app.core.logging import log_inventory_updated, log_inventory_allocation


class InventoryService:
    """Service for inventory operations and FIFO allocation."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def get_or_create_inventory(self, sku_id: UUID) -> InventoryItem:
        """Get or create an inventory record for a SKU."""
        inv = self.db.query(InventoryItem).filter(InventoryItem.sku_id == sku_id).first()
        if not inv:
            inv = InventoryItem(sku_id=sku_id, quantity_on_hand=0)
            self.db.add(inv)
            self.db.flush()
        return inv

    def add_inventory(self, sku_id: UUID, quantity: int, performed_by: UUID | None = None) -> InventoryItem:
        """
        Add stock to inventory for a SKU.
        Typically called when manufacturing completes.
        """
        if quantity < 0:
            raise ValueError("Cannot add negative inventory — use subtract_inventory instead")

        inv = self.get_or_create_inventory(sku_id)
        old_qty = inv.quantity_on_hand
        inv.quantity_on_hand += quantity

        log_inventory_updated(sku_id=sku_id, old_quantity=old_qty, new_quantity=inv.quantity_on_hand, reason="manufacturing")

        if performed_by:
            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="inventory",
                entity_id=inv.id,
                performed_by=performed_by,
                payload={
                    "sku_id": str(sku_id),
                    "quantity_added": quantity,
                    "old_quantity": old_qty,
                    "new_quantity": inv.quantity_on_hand,
                },
            )

        return inv

    def subtract_inventory(self, sku_id: UUID, quantity: int, performed_by: UUID | None = None) -> InventoryItem:
        """
        Subtract stock from inventory for a SKU.
        Typically called when manufacturing completion is reduced (rollback).

        Guardrail: logs a warning if inventory goes negative but does not block
        the operation, since allocated inventory may need rebalancing.
        """
        if quantity < 0:
            raise ValueError("Cannot subtract negative quantity — use add_inventory instead")

        inv = self.get_or_create_inventory(sku_id)
        old_qty = inv.quantity_on_hand
        inv.quantity_on_hand -= quantity

        if inv.quantity_on_hand < 0:
            import logging
            logging.getLogger("app.lifecycle").warning(
                "GUARDRAIL: Inventory for SKU %s went negative (%d -> %d). FIFO rebalancing required.",
                sku_id, old_qty, inv.quantity_on_hand,
            )

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="inventory",
            entity_id=inv.id,
            performed_by=performed_by,
            payload={
                "sku_id": str(sku_id),
                "quantity_subtracted": quantity,
                "old_quantity": old_qty,
                "new_quantity": inv.quantity_on_hand,
                "reason": "manufacturing_rollback",
            },
        )

        return inv

    def get_inventory_level(self, sku_id: UUID) -> int:
        """Get current inventory level for a SKU."""
        inv = self.db.query(InventoryItem).filter(InventoryItem.sku_id == sku_id).first()
        return inv.quantity_on_hand if inv else 0

    def allocate_inventory_fifo(self, sku_ids: list[UUID] | None = None, performed_by: UUID | None = None) -> dict:
        """
        Allocate available inventory to approved orders FIFO.

        Algorithm:
        1. Get approved orders ordered by created_at ASC (oldest first)
        2. For each order, for each item:
           - Calculate need = quantity_ordered - quantity_allocated
           - If need > 0, allocate min(need, available_inventory)
           - Update order_item.quantity_allocated
           - Decrement inventory.quantity_on_hand

        Args:
            sku_ids: Optional list of SKU IDs to limit allocation to
            performed_by: User ID for audit logging

        Returns:
            dict with allocation statistics
        """
        # Get all approved orders, oldest first
        orders = (
            self.db.query(Order)
            .filter(Order.status == OrderStatus.APPROVED)
            .order_by(Order.created_at.asc())
            .all()
        )

        total_allocated = 0
        orders_updated = set()

        for order in orders:
            # Get items sorted deterministically
            items = sorted(order.items, key=lambda x: x.created_at)

            for item in items:
                # Skip if we're only processing specific SKUs
                if sku_ids and item.sku_id not in sku_ids:
                    continue

                need = item.quantity_ordered - item.quantity_allocated
                if need <= 0:
                    continue

                # Get available inventory
                inv = self.db.query(InventoryItem).filter(InventoryItem.sku_id == item.sku_id).first()
                if not inv or inv.quantity_on_hand <= 0:
                    continue

                # Allocate min(need, available)
                allocate_qty = min(need, inv.quantity_on_hand)
                if allocate_qty > 0:
                    item.quantity_allocated += allocate_qty
                    inv.quantity_on_hand -= allocate_qty
                    total_allocated += allocate_qty
                    orders_updated.add(order.id)

        # Commit allocation changes
        self.db.flush()

        if total_allocated > 0:
            log_inventory_allocation(total_allocated=total_allocated, orders_updated=len(orders_updated))

        return {
            "total_allocated": total_allocated,
            "orders_updated": len(orders_updated),
        }

    def deallocate_order(self, order: Order, performed_by: UUID | None = None) -> dict:
        """
        Return allocated inventory from an order back to stock.
        Typically called when order is cancelled.

        Returns dict with deallocation stats.
        """
        total_returned = 0

        for item in order.items:
            if item.quantity_allocated > 0:
                # Return to inventory
                inv = self.get_or_create_inventory(item.sku_id)
                returned_qty = item.quantity_allocated
                inv.quantity_on_hand += returned_qty
                total_returned += returned_qty

                # Clear allocation
                item.quantity_allocated = 0

        self.db.flush()

        return {"total_returned": total_returned}

    def get_inventory_summary(self) -> list[dict]:
        """Get inventory summary for all SKUs with stock."""
        items = (
            self.db.query(InventoryItem)
            .filter(InventoryItem.quantity_on_hand > 0)
            .all()
        )

        result = []
        for inv in items:
            sku = inv.sku
            result.append({
                "sku_id": inv.sku_id,
                "sku_code": sku.code if sku else None,
                "product_name": sku.product.name if sku and sku.product else None,
                "size": sku.size if sku else None,
                "color": sku.color if sku else None,
                "quantity_on_hand": inv.quantity_on_hand,
            })

        return result
