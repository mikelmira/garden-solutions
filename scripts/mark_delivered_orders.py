#!/usr/bin/env python3
"""
Mark delivered Shopify orders as completed + link all Shopify orders to Pot Shack client.

Shopify fulfillment_status:
- "fulfilled" = delivered -> mark as completed
- "partial" = partially delivered -> mark as completed (already sent)
- null/unfulfilled = not yet delivered -> keep as pending_approval

Also sets client_id on all Shopify orders so they show "Pot Shack" in the dashboard.

Run inside the API container:
  docker compose -f docker-compose.live.yml exec api python3 /app/mark_delivered_orders.py
"""
import sys
sys.path.insert(0, "/app")

from app.core.database import SessionLocal
from app.models.shopify import ShopifyOrder
from app.models.order import Order, OrderStatus
from app.models.store import Store
from app.models.client import Client

def main():
    db = SessionLocal()

    try:
        store = db.query(Store).filter(
            Store.store_type == "shopify",
            Store.is_active.is_(True),
        ).first()

        if not store:
            print("ERROR: No active Shopify store found")
            sys.exit(1)

        print(f"Store: {store.name}")

        # Find the Pot Shack client
        pot_shack = db.query(Client).filter(
            Client.name.ilike("%pot shack%"),
            Client.is_active.is_(True),
        ).first()

        if pot_shack:
            print(f"Pot Shack client: {pot_shack.name} (ID: {pot_shack.id})")
        else:
            print("WARNING: No 'Pot Shack' client found - orders won't be linked to a client")

        print()

        # Get all Shopify orders for this store
        shopify_orders = db.query(ShopifyOrder).filter(
            ShopifyOrder.store_id == store.id,
            ShopifyOrder.internal_order_id.isnot(None),
        ).all()

        print(f"Total Shopify orders with internal orders: {len(shopify_orders)}")

        completed = 0
        kept_pending = 0
        already_done = 0
        client_linked = 0

        for so in shopify_orders:
            internal = db.query(Order).filter(Order.id == so.internal_order_id).first()
            if not internal:
                continue

            # Link to Pot Shack client if not already linked
            if pot_shack and not internal.client_id:
                internal.client_id = pot_shack.id
                client_linked += 1

            # Already completed or cancelled - skip status change
            if internal.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                already_done += 1
                continue

            fulfillment = so.fulfillment_status
            financial = so.financial_status

            # Determine if this order has been delivered
            # fulfilled or partial = already delivered to customer
            is_delivered = fulfillment in ("fulfilled", "partial")

            # Also mark paid+closed orders as completed
            if not is_delivered and so.raw_payload:
                closed_at = so.raw_payload.get("closed_at")
                if closed_at:
                    is_delivered = True

            if is_delivered:
                internal.status = OrderStatus.COMPLETED
                completed += 1
                print(f"  #{so.shopify_order_number} | {so.customer_name} | {fulfillment} | -> COMPLETED")
            else:
                kept_pending += 1
                print(f"  #{so.shopify_order_number} | {so.customer_name} | {fulfillment or 'unfulfilled'} | -> KEPT PENDING")

        db.commit()

        print(f"\n{'=' * 50}")
        print(f"DONE")
        print(f"  Marked completed: {completed}")
        print(f"  Kept pending (to be delivered): {kept_pending}")
        print(f"  Already completed/cancelled: {already_done}")
        print(f"  Linked to Pot Shack: {client_linked}")
        print(f"{'=' * 50}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
