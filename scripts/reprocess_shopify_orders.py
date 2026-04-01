#!/usr/bin/env python3
"""
Reprocess Shopify orders: fetch all orders from Shopify API and re-ingest them.

This script:
1. Fetches all orders from the Shopify Admin API
2. Deletes existing internal orders that are still pending_approval
3. Re-ingests each order using the updated matching logic (name-based matching,
   customer name in notes, Shopify total_price)

Run inside the API container:
  docker compose -f docker-compose.live.yml exec api python3 scripts/reprocess_shopify_orders.py
"""
import os
import sys
import json
import urllib.request
import urllib.error

# Add app to path
sys.path.insert(0, "/app")

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.shopify import ShopifyService
from app.models.store import Store
from app.models.order import Order, OrderStatus
from app.models.shopify import ShopifyOrder
from app.models.user import User

settings = get_settings()


def fetch_shopify_orders():
    """Fetch all orders from Shopify Admin API."""
    shop = settings.SHOPIFY_SHOP_DOMAIN
    token = settings.SHOPIFY_ACCESS_TOKEN
    api_version = settings.SHOPIFY_API_VERSION

    if not shop or not token:
        print("ERROR: SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN must be set")
        sys.exit(1)

    all_orders = []
    url = f"https://{shop}/admin/api/{api_version}/orders.json?status=any&limit=250"

    while url:
        req = urllib.request.Request(url, headers={
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        })

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                orders = data.get("orders", [])
                all_orders.extend(orders)
                print(f"  Fetched {len(orders)} orders (total: {len(all_orders)})")

                # Check for pagination
                link_header = resp.headers.get("Link", "")
                url = None
                if 'rel="next"' in link_header:
                    for part in link_header.split(","):
                        if 'rel="next"' in part:
                            url = part.split("<")[1].split(">")[0]
                            break
        except urllib.error.HTTPError as e:
            print(f"ERROR fetching orders: {e.code} {e.reason}")
            body = e.read().decode() if e.fp else ""
            print(f"  Response: {body[:500]}")
            sys.exit(1)

    return all_orders


def fetch_shopify_products():
    """Fetch all products from Shopify Admin API."""
    shop = settings.SHOPIFY_SHOP_DOMAIN
    token = settings.SHOPIFY_ACCESS_TOKEN
    api_version = settings.SHOPIFY_API_VERSION

    all_products = []
    url = f"https://{shop}/admin/api/{api_version}/products.json?limit=250"

    while url:
        req = urllib.request.Request(url, headers={
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        })

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                products = data.get("products", [])
                all_products.extend(products)
                print(f"  Fetched {len(products)} products (total: {len(all_products)})")

                link_header = resp.headers.get("Link", "")
                url = None
                if 'rel="next"' in link_header:
                    for part in link_header.split(","):
                        if 'rel="next"' in part:
                            url = part.split("<")[1].split(">")[0]
                            break
        except urllib.error.HTTPError as e:
            print(f"ERROR fetching products: {e.code} {e.reason}")
            body = e.read().decode() if e.fp else ""
            print(f"  Response: {body[:500]}")
            # Don't exit - products are optional, orders are the priority
            return all_products

    return all_products


def main():
    print("=" * 60)
    print("SHOPIFY ORDER REPROCESSING")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Find Shopify store
        store = db.query(Store).filter(
            Store.store_type == "shopify",
            Store.is_active.is_(True),
        ).first()

        if not store:
            print("ERROR: No active Shopify store found")
            sys.exit(1)

        print(f"\nStore: {store.name} (ID: {store.id})")

        # Find admin user for created_by
        admin = db.query(User).filter(User.role == "admin", User.is_active.is_(True)).first()
        if not admin:
            print("ERROR: No active admin user found")
            sys.exit(1)

        print(f"Admin: {admin.email}")

        service = ShopifyService(db)

        # Step 1: Sync products first (so name matching works)
        print(f"\n--- Step 1: Syncing products from Shopify ---")
        products = fetch_shopify_products()
        if products:
            synced = 0
            for p in products:
                try:
                    service.sync_product(p, store.id)
                    synced += 1
                except Exception as e:
                    print(f"  WARNING: Failed to sync product '{p.get('title')}': {e}")
            print(f"  Synced {synced}/{len(products)} products")
        else:
            print("  No products fetched (may need read_products scope)")

        # Step 2: Reconcile variant mappings with new name-based logic
        print(f"\n--- Step 2: Reconciling variant mappings ---")
        result = service.reconcile_mappings()
        print(f"  Unmapped: {result['total_unmapped']}, Resolved: {result['resolved']}, Remaining: {result['remaining']}")

        # Step 3: Delete existing pending internal orders from Shopify
        print(f"\n--- Step 3: Clearing existing Shopify orders for re-ingestion ---")
        existing_shopify_orders = db.query(ShopifyOrder).filter(
            ShopifyOrder.store_id == store.id,
        ).all()
        print(f"  Found {len(existing_shopify_orders)} existing Shopify order records")

        deleted_internal = 0
        deleted_shopify = 0
        for so in existing_shopify_orders:
            # Delete linked internal order if still pending
            if so.internal_order_id:
                internal = db.query(Order).filter(Order.id == so.internal_order_id).first()
                if internal and internal.status == OrderStatus.PENDING_APPROVAL:
                    # Delete order items first
                    for item in internal.items:
                        db.delete(item)
                    db.delete(internal)
                    deleted_internal += 1

            # Delete the ShopifyOrder record so it can be re-ingested
            db.delete(so)
            deleted_shopify += 1

        db.commit()
        print(f"  Deleted {deleted_shopify} Shopify order records, {deleted_internal} internal orders")

        # Step 4: Fetch and re-ingest all orders from Shopify
        print(f"\n--- Step 4: Fetching orders from Shopify API ---")
        orders = fetch_shopify_orders()
        print(f"  Total orders from Shopify: {len(orders)}")

        print(f"\n--- Step 5: Re-ingesting orders ---")
        success = 0
        failed = 0
        for order_data in orders:
            try:
                so = service.ingest_order(order_data, store.id, system_user_id=admin.id)
                order_num = order_data.get("order_number", "?")
                customer = order_data.get("customer", {}) or {}
                name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Unknown"
                total = order_data.get("total_price", "0")
                items = len(order_data.get("line_items", []))
                print(f"  #{order_num} | {name} | R{total} | {items} items | sync: {so.sync_status}")
                success += 1
            except Exception as e:
                order_num = order_data.get("order_number", "?")
                print(f"  #{order_num} | FAILED: {e}")
                failed += 1

        print(f"\n{'=' * 60}")
        print(f"COMPLETE")
        print(f"  Orders processed: {success}")
        print(f"  Failed: {failed}")
        print(f"  Products synced: {len(products)}")
        print(f"  Variant mappings resolved: {result['resolved']}")
        print(f"{'=' * 60}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
