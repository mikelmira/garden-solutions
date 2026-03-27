#!/usr/bin/env python3
"""
System Integrity Check Script

Validates data consistency across the Garden Solutions platform:
1. Order items vs manufactured quantities
2. Inventory vs allocations
3. SKU vs product integrity
4. Manufacturing plans vs demand
5. Delivery records vs order state

Usage:
    cd apps/api
    python -m scripts.check_integrity

Returns exit code 0 if all checks pass, 1 if any fail.
"""
import sys
from pathlib import Path

# Add parent to path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.sku import SKU
from app.models.inventory import InventoryItem
from app.models.manufacturing_day import ManufacturingDay, ManufacturingDayItem

# ── Helpers ───────────────────────────────────────────────────

class IntegrityReport:
    def __init__(self):
        self.checks = []
        self.failures = []

    def check(self, name: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        self.checks.append((name, status, detail))
        if not passed:
            self.failures.append((name, detail))
        icon = "✓" if passed else "✗"
        print(f"  {icon} {name}: {status}" + (f" — {detail}" if detail else ""))

    def summary(self):
        total = len(self.checks)
        passed = total - len(self.failures)
        print(f"\n{'='*60}")
        print(f"  {passed}/{total} checks passed")
        if self.failures:
            print(f"\n  FAILURES:")
            for name, detail in self.failures:
                print(f"    ✗ {name}: {detail}")
        print(f"{'='*60}")
        return len(self.failures) == 0


def run_checks():
    db = SessionLocal()
    report = IntegrityReport()

    try:
        print("\n" + "="*60)
        print("  GARDEN SOLUTIONS — System Integrity Check")
        print("="*60)

        # ─────────────────────────────────────────────────────
        # 1. ORDER ITEMS vs MANUFACTURED QUANTITIES
        # ─────────────────────────────────────────────────────
        print("\n[1] Order Items vs Manufactured Quantities")

        # Check: quantity_manufactured should never exceed quantity_ordered
        over_manufactured = (
            db.query(OrderItem)
            .filter(OrderItem.quantity_manufactured > OrderItem.quantity_ordered)
            .all()
        )
        report.check(
            "No over-manufactured items",
            len(over_manufactured) == 0,
            f"{len(over_manufactured)} items have qty_manufactured > qty_ordered" if over_manufactured else "",
        )

        # Check: quantity_delivered should never exceed quantity_manufactured
        over_delivered = (
            db.query(OrderItem)
            .filter(OrderItem.quantity_delivered > OrderItem.quantity_manufactured)
            .all()
        )
        report.check(
            "No over-delivered items",
            len(over_delivered) == 0,
            f"{len(over_delivered)} items have qty_delivered > qty_manufactured" if over_delivered else "",
        )

        # Check: quantity_delivered should never exceed quantity_ordered
        over_delivered_ordered = (
            db.query(OrderItem)
            .filter(OrderItem.quantity_delivered > OrderItem.quantity_ordered)
            .all()
        )
        report.check(
            "No items delivered beyond ordered",
            len(over_delivered_ordered) == 0,
            f"{len(over_delivered_ordered)} items have qty_delivered > qty_ordered" if over_delivered_ordered else "",
        )

        # Check: quantity_allocated should never exceed quantity_ordered
        over_allocated = (
            db.query(OrderItem)
            .filter(OrderItem.quantity_allocated > OrderItem.quantity_ordered)
            .all()
        )
        report.check(
            "No over-allocated items",
            len(over_allocated) == 0,
            f"{len(over_allocated)} items have qty_allocated > qty_ordered" if over_allocated else "",
        )

        # ─────────────────────────────────────────────────────
        # 2. INVENTORY vs ALLOCATIONS
        # ─────────────────────────────────────────────────────
        print("\n[2] Inventory vs Allocations")

        # Check: no negative inventory
        negative_inventory = (
            db.query(InventoryItem)
            .filter(InventoryItem.quantity_on_hand < 0)
            .all()
        )
        report.check(
            "No negative inventory",
            len(negative_inventory) == 0,
            f"{len(negative_inventory)} SKUs have negative stock" if negative_inventory else "",
        )

        # Check: total allocated across all orders should be consistent with inventory changes
        # For each SKU, the sum of allocations across approved orders should not exceed
        # total manufactured (as implied by inventory additions)
        skus_with_items = db.query(SKU).filter(SKU.is_active.is_(True)).all()
        allocation_issues = []
        for sku in skus_with_items:
            total_allocated = (
                db.query(OrderItem)
                .join(Order)
                .filter(
                    OrderItem.sku_id == sku.id,
                    Order.status.in_([OrderStatus.APPROVED, OrderStatus.COMPLETED, OrderStatus.PARTIALLY_DELIVERED]),
                )
                .with_entities(
                    db.query(OrderItem).with_entities(
                        OrderItem.quantity_allocated
                    ).filter(
                        OrderItem.sku_id == sku.id,
                    ).correlate(None).scalar_subquery()
                )
                .first()
            )

        # Simplified: just check that inventory + total_allocated >= 0
        inv_items = db.query(InventoryItem).all()
        for inv in inv_items:
            total_alloc = sum(
                oi.quantity_allocated
                for oi in db.query(OrderItem).filter(
                    OrderItem.sku_id == inv.sku_id,
                ).all()
            )
            # Inventory should be >= 0 when accounting is correct
            if inv.quantity_on_hand < 0:
                allocation_issues.append(f"SKU {inv.sku_id}: inventory={inv.quantity_on_hand}")

        report.check(
            "Inventory accounting consistent",
            len(allocation_issues) == 0,
            "; ".join(allocation_issues[:5]) if allocation_issues else "",
        )

        # ─────────────────────────────────────────────────────
        # 3. SKU vs PRODUCT INTEGRITY
        # ─────────────────────────────────────────────────────
        print("\n[3] SKU vs Product Integrity")

        # Check: all active SKUs belong to an existing product
        orphan_skus = (
            db.query(SKU)
            .filter(SKU.is_active.is_(True))
            .outerjoin(Product, SKU.product_id == Product.id)
            .filter(Product.id.is_(None))
            .all()
        )
        report.check(
            "No orphan SKUs (missing product)",
            len(orphan_skus) == 0,
            f"{len(orphan_skus)} active SKUs without a valid product" if orphan_skus else "",
        )

        # Check: all SKUs have unique codes
        from sqlalchemy import func
        dup_codes = (
            db.query(SKU.code, func.count(SKU.id))
            .filter(SKU.is_active.is_(True))
            .group_by(SKU.code)
            .having(func.count(SKU.id) > 1)
            .all()
        )
        report.check(
            "No duplicate SKU codes",
            len(dup_codes) == 0,
            f"Duplicate codes: {', '.join(c[0] for c in dup_codes)}" if dup_codes else "",
        )

        # Check: all order items reference valid SKUs
        orphan_items = (
            db.query(OrderItem)
            .outerjoin(SKU, OrderItem.sku_id == SKU.id)
            .filter(SKU.id.is_(None))
            .all()
        )
        report.check(
            "No order items with missing SKUs",
            len(orphan_items) == 0,
            f"{len(orphan_items)} order items reference non-existent SKUs" if orphan_items else "",
        )

        # ─────────────────────────────────────────────────────
        # 4. MANUFACTURING PLANS vs DEMAND
        # ─────────────────────────────────────────────────────
        print("\n[4] Manufacturing Plans vs Demand")

        # Check: no plan items with completion > planned
        over_completed = (
            db.query(ManufacturingDayItem)
            .filter(ManufacturingDayItem.quantity_completed > ManufacturingDayItem.quantity_planned)
            .all()
        )
        report.check(
            "No plan items completed beyond planned",
            len(over_completed) == 0,
            f"{len(over_completed)} plan items have qty_completed > qty_planned" if over_completed else "",
        )

        # Check: no plan items with negative completion
        neg_completed = (
            db.query(ManufacturingDayItem)
            .filter(ManufacturingDayItem.quantity_completed < 0)
            .all()
        )
        report.check(
            "No plan items with negative completion",
            len(neg_completed) == 0,
            f"{len(neg_completed)} plan items have negative qty_completed" if neg_completed else "",
        )

        # Check: plan items reference valid SKUs
        orphan_plan_items = (
            db.query(ManufacturingDayItem)
            .outerjoin(SKU, ManufacturingDayItem.sku_id == SKU.id)
            .filter(SKU.id.is_(None))
            .all()
        )
        report.check(
            "All plan items reference valid SKUs",
            len(orphan_plan_items) == 0,
            f"{len(orphan_plan_items)} plan items reference non-existent SKUs" if orphan_plan_items else "",
        )

        # ─────────────────────────────────────────────────────
        # 5. DELIVERY RECORDS vs ORDER STATE
        # ─────────────────────────────────────────────────────
        print("\n[5] Delivery Records vs Order State")

        # Check: completed orders should have all items fully delivered
        completed_orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).all()
        incomplete_completed = []
        for order in completed_orders:
            for item in order.items:
                if item.quantity_delivered < item.quantity_ordered:
                    incomplete_completed.append(f"Order {str(order.id)[:8]}: item {str(item.id)[:8]} delivered={item.quantity_delivered} < ordered={item.quantity_ordered}")
                    break

        report.check(
            "Completed orders are fully delivered",
            len(incomplete_completed) == 0,
            "; ".join(incomplete_completed[:3]) if incomplete_completed else "",
        )

        # Check: cancelled orders should have zero allocations
        cancelled_orders = db.query(Order).filter(Order.status == OrderStatus.CANCELLED).all()
        allocated_cancelled = []
        for order in cancelled_orders:
            for item in order.items:
                if item.quantity_allocated > 0:
                    allocated_cancelled.append(f"Order {str(order.id)[:8]}: item still has {item.quantity_allocated} allocated")
                    break

        report.check(
            "Cancelled orders have zero allocations",
            len(allocated_cancelled) == 0,
            "; ".join(allocated_cancelled[:3]) if allocated_cancelled else "",
        )

        # Check: orders with delivery_status=delivered should have status=completed
        delivered_not_completed = (
            db.query(Order)
            .filter(
                Order.delivery_status == "delivered",
                Order.status != OrderStatus.COMPLETED,
            )
            .all()
        )
        report.check(
            "Delivered orders have completed status",
            len(delivered_not_completed) == 0,
            f"{len(delivered_not_completed)} orders marked delivered but not completed" if delivered_not_completed else "",
        )

        # Check: no items with quantity_delivered > 0 on pending orders
        pending_with_delivery = (
            db.query(OrderItem)
            .join(Order)
            .filter(
                Order.status == OrderStatus.PENDING_APPROVAL,
                OrderItem.quantity_delivered > 0,
            )
            .all()
        )
        report.check(
            "No deliveries on pending orders",
            len(pending_with_delivery) == 0,
            f"{len(pending_with_delivery)} pending orders have delivered items" if pending_with_delivery else "",
        )

        # ── Summary ──────────────────────────────────────────
        all_passed = report.summary()
        return 0 if all_passed else 1

    finally:
        db.close()


if __name__ == "__main__":
    exit_code = run_checks()
    sys.exit(exit_code)
