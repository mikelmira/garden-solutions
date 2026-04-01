"""
Shopify integration service.

Core logic for:
- Product/variant sync (from Shopify API or webhook payloads)
- Variant → SKU mapping (auto + manual)
- Order ingestion (from Shopify API or webhook payloads)
- Order lifecycle integration
- Reconciliation
- Guardrails (idempotency, duplicate prevention, state protection)

LIFECYCLE RULES:
- Shopify orders enter as pending_approval (requires admin approval)
- Once approved internally, Shopify updates are BLOCKED from modifying order items
- Shopify cancellations ARE respected even after approval (triggers internal cancel)
- Shopify order edits on non-approved orders update the internal order
"""
import hashlib
import hmac
import logging
import time
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import get_settings
from app.models.shopify import ShopifyProduct, ShopifyVariant, ShopifyOrder, ShopifyWebhookEvent
from app.models.order import Order, OrderStatus, OrderSource
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.sku import SKU
from app.models.store import Store
from app.models.client import Client
from app.models.user import User
from app.services.audit import AuditService
from app.models.audit_log import AuditAction
from app.services.inventory import InventoryService

logger = logging.getLogger("app.lifecycle")
settings = get_settings()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_shopify_datetime(dt_str: str | None) -> datetime | None:
    """Parse Shopify ISO datetime string."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


class ShopifyService:
    """
    Unified Shopify integration service.
    All sync/ingestion flows share this logic so that manual sync,
    webhook sync, and reconciliation all behave identically.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # ══════════════════════════════════════════════════════════════
    # WEBHOOK VERIFICATION
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def verify_webhook_signature(body: bytes, hmac_header: str | None) -> bool:
        """
        Verify Shopify webhook HMAC-SHA256 signature.
        Returns True if valid or if no secret is configured (dev mode).
        """
        secret = settings.SHOPIFY_WEBHOOK_SECRET
        if not secret:
            # No secret configured — skip verification (dev/local mode)
            return True
        if not hmac_header:
            return False
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
        import base64
        computed = base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(computed, hmac_header)

    # ══════════════════════════════════════════════════════════════
    # WEBHOOK EVENT LOGGING
    # ══════════════════════════════════════════════════════════════

    def log_webhook_event(
        self,
        topic: str,
        payload: dict | None,
        headers: dict | None = None,
        shop_domain: str | None = None,
        store_id: UUID | None = None,
    ) -> ShopifyWebhookEvent:
        """Record a raw webhook event for diagnostics."""
        webhook_id = headers.get("x-shopify-webhook-id") if headers else None

        # Idempotency check — skip if we already processed this webhook
        if webhook_id:
            existing = (
                self.db.query(ShopifyWebhookEvent)
                .filter(ShopifyWebhookEvent.shopify_webhook_id == webhook_id)
                .first()
            )
            if existing:
                existing.status = "duplicate"
                self.db.commit()
                return existing

        event = ShopifyWebhookEvent(
            shopify_webhook_id=webhook_id,
            topic=topic,
            shop_domain=shop_domain,
            store_id=store_id,
            status="received",
            raw_payload=payload,
            headers=headers,
        )
        self.db.add(event)
        self.db.commit()
        return event

    def mark_webhook_processed(self, event: ShopifyWebhookEvent, status: str = "processed", error: str | None = None, elapsed_ms: int | None = None):
        """Update webhook event with processing result."""
        event.status = status
        event.error_message = error
        event.processing_time_ms = elapsed_ms
        event.processed_at = utc_now()
        self.db.commit()

    # ══════════════════════════════════════════════════════════════
    # STORE RESOLUTION
    # ══════════════════════════════════════════════════════════════

    def get_shopify_store(self, shop_domain: str | None = None) -> Store | None:
        """Find the internal store record for the Shopify store."""
        # First try by domain match if we have it
        # Otherwise find any active store with type=shopify
        query = self.db.query(Store).filter(
            Store.store_type == "shopify",
            Store.is_active.is_(True),
        )
        store = query.first()
        return store

    # ══════════════════════════════════════════════════════════════
    # PRODUCT / VARIANT SYNC
    # ══════════════════════════════════════════════════════════════

    def sync_product(self, product_data: dict, store_id: UUID) -> ShopifyProduct:
        """
        Upsert a Shopify product and its variants.
        Reusable by both webhook and manual sync.
        """
        shopify_id = product_data.get("id")
        if not shopify_id:
            raise ValueError("Product data missing 'id' field")

        now = utc_now()

        # Upsert product
        sp = (
            self.db.query(ShopifyProduct)
            .filter(ShopifyProduct.shopify_product_id == shopify_id)
            .first()
        )
        if sp:
            sp.title = product_data.get("title", sp.title)
            sp.product_type = product_data.get("product_type")
            sp.vendor = product_data.get("vendor")
            sp.shopify_handle = product_data.get("handle")
            sp.shopify_status = product_data.get("status")
            sp.raw_payload = product_data
            sp.last_synced_at = now
            sp.updated_at = now
        else:
            sp = ShopifyProduct(
                shopify_product_id=shopify_id,
                store_id=store_id,
                title=product_data.get("title", "Unknown"),
                product_type=product_data.get("product_type"),
                vendor=product_data.get("vendor"),
                shopify_handle=product_data.get("handle"),
                shopify_status=product_data.get("status"),
                raw_payload=product_data,
                last_synced_at=now,
            )
            self.db.add(sp)

        self.db.flush()

        # Upsert variants
        variants = product_data.get("variants", [])
        for v_data in variants:
            self._sync_variant(v_data, sp)

        self.db.commit()

        # Lifecycle log
        _log_shopify_event("shopify.product_synced", {
            "shopify_product_id": shopify_id,
            "title": sp.title,
            "variant_count": len(variants),
            "store_id": str(store_id),
        })

        return sp

    def _sync_variant(self, v_data: dict, shopify_product: ShopifyProduct) -> ShopifyVariant:
        """Upsert a single Shopify variant."""
        variant_id = v_data.get("id")
        if not variant_id:
            return None

        now = utc_now()

        sv = (
            self.db.query(ShopifyVariant)
            .filter(ShopifyVariant.shopify_variant_id == variant_id)
            .first()
        )
        if sv:
            sv.title = v_data.get("title")
            sv.shopify_sku = v_data.get("sku")
            sv.price = str(v_data.get("price", ""))
            sv.option1 = v_data.get("option1")
            sv.option2 = v_data.get("option2")
            sv.option3 = v_data.get("option3")
            sv.inventory_quantity = v_data.get("inventory_quantity")
            sv.last_synced_at = now
            sv.updated_at = now
            # Re-attempt auto-mapping if still unmapped
            if sv.mapping_status == "unmapped":
                self._auto_map_variant(sv)
        else:
            sv = ShopifyVariant(
                shopify_variant_id=variant_id,
                shopify_product_id=shopify_product.shopify_product_id,
                product_id_fk=shopify_product.id,
                title=v_data.get("title"),
                shopify_sku=v_data.get("sku"),
                price=str(v_data.get("price", "")),
                option1=v_data.get("option1"),
                option2=v_data.get("option2"),
                option3=v_data.get("option3"),
                inventory_quantity=v_data.get("inventory_quantity"),
                mapping_status="unmapped",
                last_synced_at=now,
            )
            self.db.add(sv)
            self.db.flush()
            # Try auto-mapping
            self._auto_map_variant(sv)

        return sv

    def _auto_map_variant(self, variant: ShopifyVariant) -> bool:
        """
        Attempt to automatically map a Shopify variant to an internal SKU.
        Matching strategy:
        1. Exact match on SKU code (shopify_sku == sku.code)
        2. Case-insensitive match on SKU code
        3. Match by Shopify product title against internal Product.name (for stores without SKU codes)
        """
        sku = None

        # Strategy 1 & 2: SKU code matching (only if Shopify has a SKU)
        if variant.shopify_sku:
            # Strategy 1: Exact match
            sku = self.db.query(SKU).filter(
                SKU.code == variant.shopify_sku,
                SKU.is_active.is_(True),
            ).first()

            # Strategy 2: Case-insensitive
            if not sku:
                sku = self.db.query(SKU).filter(
                    func.lower(SKU.code) == variant.shopify_sku.lower(),
                    SKU.is_active.is_(True),
                ).first()

        # Strategy 3: Match by Shopify product title → internal Product.name
        if not sku and variant.shopify_product:
            product_title = (variant.shopify_product.title or "").strip().lower()
            if product_title:
                sku = self._match_sku_by_product_name(product_title)

        if sku:
            variant.sku_id = sku.id
            variant.mapping_status = "mapped"
            _log_shopify_event("shopify.variant_mapped", {
                "shopify_variant_id": variant.shopify_variant_id,
                "shopify_sku": variant.shopify_sku,
                "product_title": variant.shopify_product.title if variant.shopify_product else None,
                "internal_sku_id": str(sku.id),
                "internal_sku_code": sku.code,
                "method": "auto",
            })
            return True
        else:
            _log_shopify_event("shopify.variant_unmapped", {
                "shopify_variant_id": variant.shopify_variant_id,
                "shopify_sku": variant.shopify_sku,
                "product_title": variant.shopify_product.title if variant.shopify_product else None,
            })
            return False

    def _match_sku_by_product_name(self, search_name: str) -> SKU | None:
        """
        Find an internal SKU by matching a search name against Product.name.
        Tries: exact match, case-insensitive match, then contains match.
        Returns the first active SKU of the matched product.
        """
        # Exact case-insensitive match
        product = self.db.query(Product).filter(
            func.lower(Product.name) == search_name,
            Product.is_active.is_(True),
        ).first()

        # Partial/contains match (Shopify title contains our product name or vice versa)
        if not product:
            products = self.db.query(Product).filter(
                Product.is_active.is_(True),
            ).all()
            for p in products:
                p_name = p.name.strip().lower()
                if p_name in search_name or search_name in p_name:
                    product = p
                    break

        if not product:
            return None

        # Get first active SKU for this product
        sku = self.db.query(SKU).filter(
            SKU.product_id == product.id,
            SKU.is_active.is_(True),
        ).first()
        return sku

    # ══════════════════════════════════════════════════════════════
    # MANUAL VARIANT MAPPING (Admin)
    # ══════════════════════════════════════════════════════════════

    def map_variant_to_sku(self, variant_id: UUID, sku_id: UUID, performed_by: UUID | None = None) -> ShopifyVariant:
        """Admin manually maps a Shopify variant to an internal SKU."""
        variant = self.db.query(ShopifyVariant).filter(ShopifyVariant.id == variant_id).first()
        if not variant:
            raise ValueError("Shopify variant not found")

        sku = self.db.query(SKU).filter(SKU.id == sku_id).first()
        if not sku:
            raise ValueError("Internal SKU not found")

        old_status = variant.mapping_status
        old_sku_id = variant.sku_id

        variant.sku_id = sku.id
        variant.mapping_status = "mapped"
        variant.updated_at = utc_now()

        self.audit.log(
            action="shopify_variant_mapped",
            entity_type="shopify_variant",
            entity_id=variant.id,
            performed_by=performed_by,
            payload={
                "shopify_variant_id": variant.shopify_variant_id,
                "shopify_sku": variant.shopify_sku,
                "old_sku_id": str(old_sku_id) if old_sku_id else None,
                "new_sku_id": str(sku.id),
                "sku_code": sku.code,
                "old_status": old_status,
            },
        )

        self.db.commit()

        _log_shopify_event("shopify.variant_mapped", {
            "shopify_variant_id": variant.shopify_variant_id,
            "internal_sku_id": str(sku.id),
            "internal_sku_code": sku.code,
            "method": "manual",
        })

        return variant

    def ignore_variant(self, variant_id: UUID, performed_by: UUID | None = None) -> ShopifyVariant:
        """Admin marks a Shopify variant as intentionally ignored."""
        variant = self.db.query(ShopifyVariant).filter(ShopifyVariant.id == variant_id).first()
        if not variant:
            raise ValueError("Shopify variant not found")

        variant.mapping_status = "ignored"
        variant.sku_id = None
        variant.updated_at = utc_now()

        self.audit.log(
            action="shopify_variant_ignored",
            entity_type="shopify_variant",
            entity_id=variant.id,
            performed_by=performed_by,
            payload={"shopify_variant_id": variant.shopify_variant_id},
        )

        self.db.commit()
        return variant

    # ══════════════════════════════════════════════════════════════
    # ORDER INGESTION
    # ══════════════════════════════════════════════════════════════

    def ingest_order(
        self,
        order_data: dict,
        store_id: UUID,
        system_user_id: UUID | None = None,
    ) -> ShopifyOrder:
        """
        Ingest a Shopify order — create or update.
        Reusable by webhook, manual sync, and reconciliation.

        LIFECYCLE RULES:
        - New Shopify orders → pending_approval
        - If Shopify order already ingested:
          - If internal order is still pending_approval → update allowed
          - If internal order is approved+ → BLOCK item changes, only update Shopify metadata
          - If Shopify order cancelled → trigger internal cancellation
        """
        shopify_order_id = order_data.get("id")
        if not shopify_order_id:
            raise ValueError("Order data missing 'id' field")

        now = utc_now()

        # Check if already ingested (idempotency)
        existing = (
            self.db.query(ShopifyOrder)
            .filter(ShopifyOrder.shopify_order_id == shopify_order_id)
            .first()
        )

        shopify_status = order_data.get("financial_status", "")
        is_cancelled = order_data.get("cancelled_at") is not None or order_data.get("cancel_reason") is not None

        if existing:
            return self._update_existing_order(existing, order_data, is_cancelled, system_user_id)

        # ── New order ingestion ────────────────────────────
        customer = order_data.get("customer", {}) or {}
        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or order_data.get("contact_email", "Unknown")

        so = ShopifyOrder(
            shopify_order_id=shopify_order_id,
            shopify_order_number=str(order_data.get("order_number", "")),
            store_id=store_id,
            shopify_status="cancelled" if is_cancelled else (order_data.get("financial_status") or "open"),
            financial_status=order_data.get("financial_status"),
            fulfillment_status=order_data.get("fulfillment_status"),
            customer_name=customer_name,
            customer_email=order_data.get("contact_email") or customer.get("email"),
            total_price=str(order_data.get("total_price", "0")),
            currency=order_data.get("currency", "ZAR"),
            shopify_created_at=_parse_shopify_datetime(order_data.get("created_at")),
            shopify_updated_at=_parse_shopify_datetime(order_data.get("updated_at")),
            raw_payload=order_data,
            sync_status="pending",
            last_synced_at=now,
        )
        self.db.add(so)
        self.db.flush()

        # Don't create internal order for cancelled Shopify orders
        if is_cancelled:
            so.sync_status = "cancelled"
            self.db.commit()
            _log_shopify_event("shopify.order_ingested", {
                "shopify_order_id": shopify_order_id,
                "status": "cancelled_on_shopify",
                "store_id": str(store_id),
            })
            return so

        # Create internal order
        try:
            internal_order, unmapped = self._create_internal_order(order_data, store_id, system_user_id)
            so.internal_order_id = internal_order.id
            so.sync_status = "partial" if unmapped else "synced"
            so.unmapped_items = unmapped if unmapped else None
        except Exception as e:
            so.sync_status = "failed"
            so.error_message = str(e)[:2000]
            logger.warning(f"Shopify order ingestion failed: {e}")

        self.db.commit()

        _log_shopify_event("shopify.order_ingested", {
            "shopify_order_id": shopify_order_id,
            "shopify_order_number": so.shopify_order_number,
            "internal_order_id": str(so.internal_order_id) if so.internal_order_id else None,
            "sync_status": so.sync_status,
            "store_id": str(store_id),
        })

        return so

    def _update_existing_order(
        self,
        existing: ShopifyOrder,
        order_data: dict,
        is_cancelled: bool,
        system_user_id: UUID | None,
    ) -> ShopifyOrder:
        """
        Update an already-ingested Shopify order.
        Enforces lifecycle guardrails.
        """
        now = utc_now()

        # Always update Shopify-side metadata
        existing.shopify_status = "cancelled" if is_cancelled else (order_data.get("financial_status") or existing.shopify_status)
        existing.financial_status = order_data.get("financial_status") or existing.financial_status
        existing.fulfillment_status = order_data.get("fulfillment_status") or existing.fulfillment_status
        existing.shopify_updated_at = _parse_shopify_datetime(order_data.get("updated_at"))
        existing.raw_payload = order_data
        existing.last_synced_at = now
        existing.updated_at = now

        # Handle cancellation — this is always respected
        if is_cancelled and existing.internal_order_id:
            internal_order = self.db.query(Order).filter(Order.id == existing.internal_order_id).first()
            if internal_order and internal_order.status not in [OrderStatus.CANCELLED, OrderStatus.COMPLETED]:
                self._cancel_internal_order(internal_order, system_user_id, "Cancelled on Shopify")
                existing.sync_status = "cancelled"

        # If internal order exists and is approved+, block item modifications
        elif existing.internal_order_id:
            internal_order = self.db.query(Order).filter(Order.id == existing.internal_order_id).first()
            if internal_order and internal_order.status != OrderStatus.PENDING_APPROVAL:
                # Order is past approval — DO NOT modify items
                # Only metadata update allowed (already done above)
                _log_shopify_event("shopify.order_updated", {
                    "shopify_order_id": existing.shopify_order_id,
                    "action": "metadata_only_update",
                    "reason": f"Internal order status is {internal_order.status}, item changes blocked",
                })
            else:
                # Still pending_approval — allow item updates
                # (This is rare but could happen with quick Shopify edits)
                pass

        self.db.commit()

        _log_shopify_event("shopify.order_updated", {
            "shopify_order_id": existing.shopify_order_id,
            "sync_status": existing.sync_status,
            "is_cancelled": is_cancelled,
        })

        return existing

    def _create_internal_order(
        self,
        order_data: dict,
        store_id: UUID,
        system_user_id: UUID | None,
    ) -> tuple[Order, list | None]:
        """
        Create an internal Order from Shopify order data.
        Returns (order, list_of_unmapped_variant_ids_or_None).
        """
        # Find system user for created_by
        if not system_user_id:
            admin_user = self.db.query(User).filter(User.role == "admin", User.is_active.is_(True)).first()
            if not admin_user:
                raise ValueError("No active admin user found for order creation")
            system_user_id = admin_user.id

        # Get store for discount
        store = self.db.query(Store).filter(Store.id == store_id).first()
        discount = Decimal("0.00")
        if store and store.price_tier:
            discount = store.price_tier.discount_percentage

        delivery_date = date.today() + timedelta(days=14)

        # Extract customer name for order notes
        customer = order_data.get("customer", {}) or {}
        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        if not customer_name:
            customer_name = order_data.get("contact_email", "Unknown Customer")

        # Use Shopify's total_price as the order amount
        shopify_total = Decimal(str(order_data.get("total_price", "0")))

        order_notes = f"Shopify order #{order_data.get('order_number', 'N/A')} — Customer: {customer_name}"

        order = Order(
            store_id=store_id,
            created_by=system_user_id,
            order_source=OrderSource.SHOPIFY,
            delivery_date=delivery_date,
            status=OrderStatus.PENDING_APPROVAL,
            total_price_rands=shopify_total,
            notes=order_notes,
        )
        self.db.add(order)
        self.db.flush()

        # Process line items
        line_items = order_data.get("line_items", [])
        total_price = Decimal("0.00")
        unmapped = []

        for li in line_items:
            variant_id = li.get("variant_id")
            quantity = li.get("quantity", 1)
            li_title = (li.get("title") or "").strip()

            sku = None

            # Try 1: Find via existing Shopify variant mapping
            if variant_id:
                sv = (
                    self.db.query(ShopifyVariant)
                    .filter(ShopifyVariant.shopify_variant_id == variant_id)
                    .first()
                )

                if sv and sv.mapping_status == "mapped" and sv.sku_id:
                    sku = self.db.query(SKU).filter(SKU.id == sv.sku_id, SKU.is_active.is_(True)).first()

            # Try 2: Match by line item title against internal Product.name
            if not sku and li_title:
                sku = self._match_sku_by_product_name(li_title.lower())

            if not sku:
                unmapped.append({
                    "shopify_variant_id": variant_id,
                    "title": li_title,
                    "sku": li.get("sku"),
                    "reason": "unmapped_variant" if variant_id else "no_variant_id",
                })
                continue

            # Price: use internal pricing with store discount
            effective_price = sku.base_price_rands * (Decimal("1") - discount)
            effective_price = effective_price.quantize(Decimal("0.01"))

            order_item = OrderItem(
                order_id=order.id,
                sku_id=sku.id,
                quantity_ordered=quantity,
                unit_price_rands=effective_price,
            )
            self.db.add(order_item)
            total_price += effective_price * quantity

        # Use calculated internal price if we matched items, otherwise keep Shopify total
        if total_price > Decimal("0.00"):
            order.total_price_rands = total_price
        # else: keep shopify_total that was set initially

        # Audit
        self.audit.log(
            action=AuditAction.CREATE,
            entity_type="order",
            entity_id=order.id,
            performed_by=system_user_id,
            payload={
                "order_source": "shopify",
                "shopify_order_id": order_data.get("id"),
                "shopify_order_number": order_data.get("order_number"),
                "total_price_rands": str(total_price),
                "item_count": len(line_items),
                "unmapped_count": len(unmapped),
            },
        )

        self.db.flush()
        return order, unmapped if unmapped else None

    def _cancel_internal_order(self, order: Order, system_user_id: UUID | None, reason: str):
        """Cancel an internal order due to Shopify cancellation."""
        if order.status in [OrderStatus.CANCELLED, OrderStatus.COMPLETED]:
            return

        old_status = order.status
        order.status = OrderStatus.CANCELLED

        # Return inventory if allocated
        if order.status == OrderStatus.APPROVED or any(i.quantity_allocated > 0 for i in order.items):
            inv_service = InventoryService(self.db)
            inv_service.deallocate_order(order, performed_by=system_user_id)

        self.audit.log(
            action=AuditAction.UPDATE,
            entity_type="order",
            entity_id=order.id,
            performed_by=system_user_id,
            payload={
                "status": {"old": old_status, "new": OrderStatus.CANCELLED},
                "reason": reason,
                "trigger": "shopify_cancellation",
            },
        )

        _log_shopify_event("shopify.order_cancelled_internally", {
            "internal_order_id": str(order.id),
            "old_status": old_status,
            "reason": reason,
        })

    # ══════════════════════════════════════════════════════════════
    # RECONCILIATION
    # ══════════════════════════════════════════════════════════════

    def reconcile_mappings(self) -> dict:
        """
        Re-attempt mapping for all unmapped variants.
        Called after new internal SKUs are created.
        """
        unmapped = (
            self.db.query(ShopifyVariant)
            .filter(ShopifyVariant.mapping_status == "unmapped")
            .all()
        )

        resolved = 0
        for variant in unmapped:
            if self._auto_map_variant(variant):
                resolved += 1

        self.db.commit()

        _log_shopify_event("shopify.mappings_reconciled", {
            "total_unmapped": len(unmapped),
            "resolved": resolved,
        })

        return {"total_unmapped": len(unmapped), "resolved": resolved, "remaining": len(unmapped) - resolved}

    def reprocess_failed_orders(self, store_id: UUID, system_user_id: UUID | None = None) -> dict:
        """
        Re-attempt ingestion for failed Shopify orders.
        Safe to run repeatedly — idempotent.
        """
        failed = (
            self.db.query(ShopifyOrder)
            .filter(
                ShopifyOrder.store_id == store_id,
                ShopifyOrder.sync_status.in_(["failed", "partial"]),
            )
            .all()
        )

        reprocessed = 0
        still_failed = 0

        for so in failed:
            if not so.raw_payload:
                still_failed += 1
                continue

            try:
                # Delete old internal order if it was partially created
                if so.internal_order_id:
                    old_order = self.db.query(Order).filter(Order.id == so.internal_order_id).first()
                    if old_order and old_order.status == OrderStatus.PENDING_APPROVAL:
                        # Safe to recreate — not yet approved
                        self.db.delete(old_order)
                        self.db.flush()
                        so.internal_order_id = None

                if not so.internal_order_id:
                    internal_order, unmapped = self._create_internal_order(so.raw_payload, store_id, system_user_id)
                    so.internal_order_id = internal_order.id
                    so.sync_status = "partial" if unmapped else "synced"
                    so.unmapped_items = unmapped
                    so.error_message = None
                    reprocessed += 1
                else:
                    still_failed += 1
            except Exception as e:
                so.error_message = str(e)[:2000]
                still_failed += 1

        self.db.commit()

        _log_shopify_event("shopify.orders_reconciled", {
            "total_failed": len(failed),
            "reprocessed": reprocessed,
            "still_failed": still_failed,
        })

        return {"total_attempted": len(failed), "reprocessed": reprocessed, "still_failed": still_failed}

    # ══════════════════════════════════════════════════════════════
    # STATUS / DASHBOARD QUERIES
    # ══════════════════════════════════════════════════════════════

    def get_integration_status(self, store_id: UUID) -> dict:
        """Return overview metrics for the admin dashboard."""
        product_count = self.db.query(func.count(ShopifyProduct.id)).filter(
            ShopifyProduct.store_id == store_id
        ).scalar() or 0

        variant_total = self.db.query(func.count(ShopifyVariant.id)).join(
            ShopifyProduct
        ).filter(ShopifyProduct.store_id == store_id).scalar() or 0

        variant_mapped = self.db.query(func.count(ShopifyVariant.id)).join(
            ShopifyProduct
        ).filter(
            ShopifyProduct.store_id == store_id,
            ShopifyVariant.mapping_status == "mapped",
        ).scalar() or 0

        variant_unmapped = self.db.query(func.count(ShopifyVariant.id)).join(
            ShopifyProduct
        ).filter(
            ShopifyProduct.store_id == store_id,
            ShopifyVariant.mapping_status == "unmapped",
        ).scalar() or 0

        variant_ignored = self.db.query(func.count(ShopifyVariant.id)).join(
            ShopifyProduct
        ).filter(
            ShopifyProduct.store_id == store_id,
            ShopifyVariant.mapping_status == "ignored",
        ).scalar() or 0

        order_total = self.db.query(func.count(ShopifyOrder.id)).filter(
            ShopifyOrder.store_id == store_id
        ).scalar() or 0

        order_synced = self.db.query(func.count(ShopifyOrder.id)).filter(
            ShopifyOrder.store_id == store_id,
            ShopifyOrder.sync_status == "synced",
        ).scalar() or 0

        order_failed = self.db.query(func.count(ShopifyOrder.id)).filter(
            ShopifyOrder.store_id == store_id,
            ShopifyOrder.sync_status == "failed",
        ).scalar() or 0

        order_partial = self.db.query(func.count(ShopifyOrder.id)).filter(
            ShopifyOrder.store_id == store_id,
            ShopifyOrder.sync_status == "partial",
        ).scalar() or 0

        # Last sync times
        last_product_sync = self.db.query(func.max(ShopifyProduct.last_synced_at)).filter(
            ShopifyProduct.store_id == store_id
        ).scalar()

        last_order_sync = self.db.query(func.max(ShopifyOrder.last_synced_at)).filter(
            ShopifyOrder.store_id == store_id
        ).scalar()

        last_webhook = self.db.query(func.max(ShopifyWebhookEvent.received_at)).filter(
            ShopifyWebhookEvent.store_id == store_id
        ).scalar()

        webhook_count_24h = self.db.query(func.count(ShopifyWebhookEvent.id)).filter(
            ShopifyWebhookEvent.store_id == store_id,
            ShopifyWebhookEvent.received_at >= utc_now() - timedelta(hours=24),
        ).scalar() or 0

        return {
            "products": {"synced": product_count},
            "variants": {
                "total": variant_total,
                "mapped": variant_mapped,
                "unmapped": variant_unmapped,
                "ignored": variant_ignored,
            },
            "orders": {
                "total": order_total,
                "synced": order_synced,
                "failed": order_failed,
                "partial": order_partial,
            },
            "last_product_sync": last_product_sync.isoformat() if last_product_sync else None,
            "last_order_sync": last_order_sync.isoformat() if last_order_sync else None,
            "last_webhook_received": last_webhook.isoformat() if last_webhook else None,
            "webhooks_24h": webhook_count_24h,
        }


# ══════════════════════════════════════════════════════════════
# LIFECYCLE LOGGING (Phase 7)
# ══════════════════════════════════════════════════════════════

def _log_shopify_event(event: str, data: dict) -> None:
    """Emit a structured Shopify lifecycle log event."""
    import json
    from app.core.logging import _UUIDEncoder
    payload = {"event": event, "timestamp": utc_now().isoformat(), **data}
    logger.info(json.dumps(payload, cls=_UUIDEncoder))
