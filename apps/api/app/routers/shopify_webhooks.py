"""
Shopify webhook receiver.

Endpoints are PUBLIC (no auth) but verified via HMAC signature.
Each webhook:
1. Logs the raw event
2. Validates signature
3. Dispatches to the shared ShopifyService for processing
4. Returns 200 immediately (Shopify expects fast responses)

Supported topics:
- orders/create
- orders/updated
- orders/cancelled
- products/create
- products/update
"""
import time
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.shopify import ShopifyService

router = APIRouter()
logger = logging.getLogger("app.lifecycle")


@router.post("/orders/create")
@router.post("/orders/updated")
@router.post("/orders/cancelled")
async def handle_shopify_order_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Shopify order webhooks (create, update, cancel)."""
    start = time.time()
    body = await request.body()

    # Extract headers
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    topic = request.headers.get("X-Shopify-Topic", "orders/unknown")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain")

    service = ShopifyService(db)

    # Verify signature
    if not service.verify_webhook_signature(body, hmac_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    try:
        import json
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Resolve store
    store = service.get_shopify_store(shop_domain)
    store_id = store.id if store else None

    # Log the raw event
    headers_dict = {
        "x-shopify-webhook-id": request.headers.get("X-Shopify-Webhook-Id"),
        "x-shopify-topic": topic,
        "x-shopify-shop-domain": shop_domain,
        "x-shopify-api-version": request.headers.get("X-Shopify-API-Version"),
    }
    event = service.log_webhook_event(
        topic=topic,
        payload=payload,
        headers=headers_dict,
        shop_domain=shop_domain,
        store_id=store_id,
    )

    # Idempotency — if this webhook was already processed, return success
    if event.status == "duplicate":
        return {"status": "ok", "message": "duplicate webhook, already processed"}

    if not store:
        service.mark_webhook_processed(event, status="failed", error="No matching Shopify store found")
        return {"status": "ok", "message": "no matching store"}

    # Process
    try:
        service.ingest_order(payload, store.id)
        elapsed = int((time.time() - start) * 1000)
        service.mark_webhook_processed(event, status="processed", elapsed_ms=elapsed)
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        service.mark_webhook_processed(event, status="failed", error=str(e)[:2000], elapsed_ms=elapsed)
        logger.warning(f"Webhook processing failed for {topic}: {e}")

    # Always return 200 to Shopify — we've logged the event regardless
    return {"status": "ok"}


@router.post("/products/create")
@router.post("/products/update")
async def handle_shopify_product_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Shopify product webhooks (create, update)."""
    start = time.time()
    body = await request.body()

    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    topic = request.headers.get("X-Shopify-Topic", "products/unknown")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain")

    service = ShopifyService(db)

    if not service.verify_webhook_signature(body, hmac_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        import json
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    store = service.get_shopify_store(shop_domain)
    store_id = store.id if store else None

    headers_dict = {
        "x-shopify-webhook-id": request.headers.get("X-Shopify-Webhook-Id"),
        "x-shopify-topic": topic,
        "x-shopify-shop-domain": shop_domain,
    }
    event = service.log_webhook_event(
        topic=topic,
        payload=payload,
        headers=headers_dict,
        shop_domain=shop_domain,
        store_id=store_id,
    )

    if event.status == "duplicate":
        return {"status": "ok", "message": "duplicate webhook, already processed"}

    if not store:
        service.mark_webhook_processed(event, status="failed", error="No matching Shopify store found")
        return {"status": "ok", "message": "no matching store"}

    try:
        service.sync_product(payload, store.id)
        elapsed = int((time.time() - start) * 1000)
        service.mark_webhook_processed(event, status="processed", elapsed_ms=elapsed)
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        service.mark_webhook_processed(event, status="failed", error=str(e)[:2000], elapsed_ms=elapsed)
        logger.warning(f"Webhook processing failed for {topic}: {e}")

    return {"status": "ok"}
