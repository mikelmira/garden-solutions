"""
Shopify admin management endpoints.

Provides:
- Integration status overview
- Variant listing (mapped, unmapped, ignored)
- Manual variant mapping
- Sync triggers (products, orders)
- Reconciliation triggers
- Recent webhook activity
"""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse
from app.models.shopify import ShopifyProduct, ShopifyVariant, ShopifyOrder, ShopifyWebhookEvent
from app.models.store import Store
from app.models.sku import SKU
from app.services.shopify import ShopifyService

router = APIRouter()


def _get_shopify_store(db: Session) -> Store:
    """Get the active Shopify store or raise 404."""
    store = db.query(Store).filter(
        Store.store_type == "shopify",
        Store.is_active.is_(True),
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="No active Shopify store configured")
    return store


# ══════════════════════════════════════════════════════════════
# STATUS OVERVIEW
# ══════════════════════════════════════════════════════════════

@router.get("/status")
def get_shopify_status(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Integration overview: sync counts, last sync times, webhook activity."""
    store = _get_shopify_store(db)
    service = ShopifyService(db)
    status = service.get_integration_status(store.id)
    status["store"] = {
        "id": str(store.id),
        "name": store.name,
        "code": store.code,
    }
    return DataResponse(data=status)


# ══════════════════════════════════════════════════════════════
# PRODUCTS
# ══════════════════════════════════════════════════════════════

@router.get("/products")
def list_shopify_products(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """List synced Shopify products with variant counts."""
    store = _get_shopify_store(db)
    products = (
        db.query(ShopifyProduct)
        .filter(ShopifyProduct.store_id == store.id)
        .order_by(ShopifyProduct.title)
        .limit(limit)
        .all()
    )

    data = []
    for p in products:
        mapped = sum(1 for v in p.variants if v.mapping_status == "mapped")
        unmapped = sum(1 for v in p.variants if v.mapping_status == "unmapped")
        data.append({
            "id": str(p.id),
            "shopify_product_id": p.shopify_product_id,
            "title": p.title,
            "product_type": p.product_type,
            "vendor": p.vendor,
            "shopify_status": p.shopify_status,
            "variant_count": len(p.variants),
            "mapped_count": mapped,
            "unmapped_count": unmapped,
            "last_synced_at": p.last_synced_at.isoformat() if p.last_synced_at else None,
        })

    return DataResponse(data=data)


# ══════════════════════════════════════════════════════════════
# VARIANTS
# ══════════════════════════════════════════════════════════════

@router.get("/variants")
def list_shopify_variants(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    status: str | None = Query(None, description="Filter: mapped, unmapped, ignored"),
    limit: int = Query(100, ge=1, le=500),
):
    """List Shopify variants with their mapping status."""
    store = _get_shopify_store(db)
    query = (
        db.query(ShopifyVariant)
        .join(ShopifyProduct)
        .filter(ShopifyProduct.store_id == store.id)
    )

    if status:
        query = query.filter(ShopifyVariant.mapping_status == status)

    variants = query.order_by(ShopifyVariant.mapping_status, ShopifyVariant.shopify_sku).limit(limit).all()

    data = []
    for v in variants:
        product_title = v.shopify_product.title if v.shopify_product else "Unknown"

        # Suggest internal SKU match if unmapped
        suggested_sku = None
        if v.mapping_status == "unmapped" and v.shopify_sku:
            # Try partial match for suggestions
            candidates = (
                db.query(SKU)
                .filter(
                    SKU.is_active.is_(True),
                    func.lower(SKU.code).contains(v.shopify_sku.lower()[:6])
                )
                .limit(3)
                .all()
            )
            if candidates:
                suggested_sku = [
                    {"id": str(s.id), "code": s.code, "product_name": s.product.name if s.product else ""}
                    for s in candidates
                ]

        data.append({
            "id": str(v.id),
            "shopify_variant_id": v.shopify_variant_id,
            "shopify_product_id": v.shopify_product_id,
            "product_title": product_title,
            "title": v.title,
            "shopify_sku": v.shopify_sku,
            "price": v.price,
            "option1": v.option1,
            "option2": v.option2,
            "option3": v.option3,
            "mapping_status": v.mapping_status,
            "sku_id": str(v.sku_id) if v.sku_id else None,
            "sku_code": v.sku.code if v.sku else None,
            "sku_product_name": v.sku.product.name if v.sku and v.sku.product else None,
            "suggested_sku": suggested_sku,
            "last_synced_at": v.last_synced_at.isoformat() if v.last_synced_at else None,
        })

    return DataResponse(data=data)


# ══════════════════════════════════════════════════════════════
# VARIANT MAPPING
# ══════════════════════════════════════════════════════════════

class MapVariantRequest(BaseModel):
    sku_id: str


@router.post("/variants/{variant_id}/map")
def map_variant(
    variant_id: str,
    body: MapVariantRequest,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Manually map a Shopify variant to an internal SKU."""
    service = ShopifyService(db)
    try:
        variant = service.map_variant_to_sku(
            variant_id=UUID(variant_id),
            sku_id=UUID(body.sku_id),
            performed_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return DataResponse(data={
        "id": str(variant.id),
        "mapping_status": variant.mapping_status,
        "sku_id": str(variant.sku_id),
    })


@router.post("/variants/{variant_id}/ignore")
def ignore_variant(
    variant_id: str,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Mark a Shopify variant as intentionally ignored."""
    service = ShopifyService(db)
    try:
        variant = service.ignore_variant(
            variant_id=UUID(variant_id),
            performed_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return DataResponse(data={
        "id": str(variant.id),
        "mapping_status": variant.mapping_status,
    })


# ══════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════

@router.get("/orders")
def list_shopify_orders(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    sync_status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List synced Shopify orders with their sync status."""
    store = _get_shopify_store(db)
    query = (
        db.query(ShopifyOrder)
        .filter(ShopifyOrder.store_id == store.id)
    )

    if sync_status:
        query = query.filter(ShopifyOrder.sync_status == sync_status)

    orders = query.order_by(ShopifyOrder.created_at.desc()).limit(limit).all()

    data = []
    for o in orders:
        data.append({
            "id": str(o.id),
            "shopify_order_id": o.shopify_order_id,
            "shopify_order_number": o.shopify_order_number,
            "internal_order_id": str(o.internal_order_id) if o.internal_order_id else None,
            "customer_name": o.customer_name,
            "total_price": o.total_price,
            "currency": o.currency,
            "shopify_status": o.shopify_status,
            "financial_status": o.financial_status,
            "sync_status": o.sync_status,
            "error_message": o.error_message,
            "unmapped_items": o.unmapped_items,
            "shopify_created_at": o.shopify_created_at.isoformat() if o.shopify_created_at else None,
            "last_synced_at": o.last_synced_at.isoformat() if o.last_synced_at else None,
        })

    return DataResponse(data=data)


# ══════════════════════════════════════════════════════════════
# SYNC ACTIONS
# ══════════════════════════════════════════════════════════════

class SyncProductsRequest(BaseModel):
    products: list[dict]  # Array of Shopify product JSON objects


@router.post("/sync/products")
def sync_products(
    body: SyncProductsRequest,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Manual product sync — accepts an array of Shopify product payloads.
    In production, the admin UI would fetch these from the Shopify API
    client-side or via a separate API call, then POST them here.
    """
    store = _get_shopify_store(db)
    service = ShopifyService(db)

    synced = 0
    errors = []
    for product_data in body.products:
        try:
            service.sync_product(product_data, store.id)
            synced += 1
        except Exception as e:
            errors.append({"product_id": product_data.get("id"), "error": str(e)})

    return DataResponse(data={
        "synced": synced,
        "errors": errors,
        "total": len(body.products),
    })


class SyncOrdersRequest(BaseModel):
    orders: list[dict]  # Array of Shopify order JSON objects


@router.post("/sync/orders")
def sync_orders(
    body: SyncOrdersRequest,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Manual order sync — accepts an array of Shopify order payloads.
    """
    store = _get_shopify_store(db)
    service = ShopifyService(db)

    synced = 0
    errors = []
    for order_data in body.orders:
        try:
            service.ingest_order(order_data, store.id, system_user_id=current_user.id)
            synced += 1
        except Exception as e:
            errors.append({"order_id": order_data.get("id"), "error": str(e)})

    return DataResponse(data={
        "synced": synced,
        "errors": errors,
        "total": len(body.orders),
    })


# ══════════════════════════════════════════════════════════════
# RECONCILIATION
# ══════════════════════════════════════════════════════════════

@router.post("/reconcile/mappings")
def reconcile_mappings(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Re-attempt auto-mapping for all unmapped variants."""
    service = ShopifyService(db)
    result = service.reconcile_mappings()
    return DataResponse(data=result)


@router.post("/reconcile/orders")
def reconcile_orders(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Re-process failed/partial Shopify orders."""
    store = _get_shopify_store(db)
    service = ShopifyService(db)
    result = service.reprocess_failed_orders(store.id, system_user_id=current_user.id)
    return DataResponse(data=result)


# ══════════════════════════════════════════════════════════════
# WEBHOOK ACTIVITY
# ══════════════════════════════════════════════════════════════

@router.get("/webhooks/recent")
def get_recent_webhooks(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    limit: int = Query(30, ge=1, le=100),
):
    """Recent webhook events for diagnostics."""
    store = _get_shopify_store(db)
    events = (
        db.query(ShopifyWebhookEvent)
        .filter(ShopifyWebhookEvent.store_id == store.id)
        .order_by(ShopifyWebhookEvent.received_at.desc())
        .limit(limit)
        .all()
    )

    data = []
    for e in events:
        data.append({
            "id": str(e.id),
            "topic": e.topic,
            "status": e.status,
            "error_message": e.error_message,
            "processing_time_ms": e.processing_time_ms,
            "received_at": e.received_at.isoformat() if e.received_at else None,
            "processed_at": e.processed_at.isoformat() if e.processed_at else None,
        })

    return DataResponse(data=data)


# ══════════════════════════════════════════════════════════════
# CUSTOMERS (extracted from Shopify orders)
# ══════════════════════════════════════════════════════════════

@router.get("/customers")
def list_shopify_customers(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    q: str = Query("", description="Search by name or email"),
    limit: int = Query(200, ge=1, le=500),
):
    """
    List unique Shopify customers extracted from order data.
    Pulls name, email, phone, and address from ShopifyOrder raw_payload.
    """
    store = _get_shopify_store(db)
    orders = (
        db.query(ShopifyOrder)
        .filter(
            ShopifyOrder.store_id == store.id,
            ShopifyOrder.customer_email.isnot(None),
        )
        .all()
    )

    # Deduplicate by email
    seen_emails: dict[str, dict] = {}
    for o in orders:
        email = (o.customer_email or "").strip().lower()
        if not email:
            continue

        if email in seen_emails:
            # Keep the most recent order's data
            if o.shopify_created_at and (
                not seen_emails[email].get("_created_at")
                or o.shopify_created_at > seen_emails[email]["_created_at"]
            ):
                seen_emails[email].update(_extract_customer(o))
            continue

        customer_data = _extract_customer(o)
        customer_data["_created_at"] = o.shopify_created_at
        seen_emails[email] = customer_data

    # Build result list
    customers = []
    for email, data in seen_emails.items():
        data.pop("_created_at", None)
        customers.append(data)

    # Apply search filter
    if q:
        q_lower = q.lower()
        customers = [
            c for c in customers
            if q_lower in (c.get("name") or "").lower()
            or q_lower in (c.get("email") or "").lower()
            or q_lower in (c.get("phone") or "").lower()
        ]

    # Sort by name
    customers.sort(key=lambda c: (c.get("name") or "").lower())

    return DataResponse(data=customers[:limit])


def _extract_customer(order: ShopifyOrder) -> dict:
    """Extract customer details from a ShopifyOrder record."""
    name = order.customer_name or ""
    email = (order.customer_email or "").strip().lower()
    phone = ""
    address = ""

    # Try to get richer data from raw_payload
    if order.raw_payload:
        customer = order.raw_payload.get("customer", {}) or {}
        phone = customer.get("phone") or ""

        # Get default address
        default_addr = customer.get("default_address", {}) or {}
        if not default_addr:
            # Try shipping address from the order itself
            default_addr = order.raw_payload.get("shipping_address", {}) or {}

        addr_parts = []
        for field in ["address1", "address2", "city", "province", "zip", "country"]:
            val = (default_addr.get(field) or "").strip()
            if val:
                addr_parts.append(val)
        address = ", ".join(addr_parts)

        # Also try phone from address if not on customer
        if not phone:
            phone = default_addr.get("phone") or ""

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
        "order_count": 1,
    }


# ══════════════════════════════════════════════════════════════
# SKU SEARCH (for mapping UI)
# ══════════════════════════════════════════════════════════════

@router.get("/internal-skus")
def search_internal_skus(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    q: str = Query("", description="Search by SKU code or product name"),
    limit: int = Query(20, ge=1, le=50),
):
    """Search internal SKUs for the mapping dropdown."""
    query = db.query(SKU).filter(SKU.is_active.is_(True))

    if q:
        search = f"%{q}%"
        query = query.filter(
            func.lower(SKU.code).like(search.lower())
        )

    skus = query.order_by(SKU.code).limit(limit).all()

    data = []
    for s in skus:
        data.append({
            "id": str(s.id),
            "code": s.code,
            "size": s.size,
            "color": s.color,
            "product_name": s.product.name if s.product else "Unknown",
            "base_price_rands": float(s.base_price_rands) if s.base_price_rands else 0,
        })

    return DataResponse(data=data)
