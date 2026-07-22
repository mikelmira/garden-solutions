"""
Shopify push-back service.

Dashboard is the source of truth for the Pot Shack Shopify store. This service
performs outbound writes against the Shopify Admin API using stdlib urllib (no
new dependencies).

Capabilities:
- update_product(...)          PUT /products/{id}.json
- update_variant(...)          PUT /variants/{id}.json
- create_variant(...)          POST /products/{id}/variants.json
- delete_variant(...)          DELETE /products/{id}/variants/{variant_id}.json
- set_inventory_level(...)     POST /inventory_levels/set.json (requires location)

Configuration:
- SHOPIFY_SHOP_DOMAIN (e.g. "pot-shack.myshopify.com")
- SHOPIFY_ACCESS_TOKEN
- SHOPIFY_API_VERSION (default 2024-01)

All public methods raise on hard failure (caller is admin endpoint, surfaces
the error to the user).
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictException, NotFoundException
from app.models.shopify import ShopifyProduct, ShopifyVariant
from app.services.audit import AuditService
from app.models.audit_log import AuditAction

logger = logging.getLogger(__name__)

# Cache the primary location id for the lifetime of the process. Shopify's
# location set rarely changes and re-fetching on every inventory set burns
# rate limit unnecessarily.
_CACHED_LOCATION_ID: int | None = None


class ShopifyPushError(Exception):
    """Raised when Shopify rejects a write or the request errors out."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _shopify_url(path: str) -> str:
    settings = get_settings()
    if not settings.SHOPIFY_SHOP_DOMAIN:
        raise ShopifyPushError("SHOPIFY_SHOP_DOMAIN is not configured")
    return f"https://{settings.SHOPIFY_SHOP_DOMAIN}/admin/api/{settings.SHOPIFY_API_VERSION}{path}"


def _humanize_shopify_error(status: int, raw: str) -> str:
    """Turn Shopify's JSON error envelope into a short, human-readable string."""
    if not raw:
        return f"Shopify returned {status} with no body"
    try:
        parsed = json.loads(raw)
    except Exception:
        return raw[:500]
    if isinstance(parsed, dict):
        errors = parsed.get("errors")
        if isinstance(errors, str):
            return errors
        if isinstance(errors, dict):
            # {"field": ["msg1", "msg2"], ...}
            bits = []
            for k, v in errors.items():
                if isinstance(v, list):
                    bits.append(f"{k}: {'; '.join(str(x) for x in v)}")
                else:
                    bits.append(f"{k}: {v}")
            return " | ".join(bits) or raw[:500]
        if isinstance(errors, list):
            return "; ".join(str(x) for x in errors)
    return raw[:500]


def _shopify_request(method: str, path: str, body: dict | None = None) -> Any:
    settings = get_settings()
    if not settings.SHOPIFY_ACCESS_TOKEN:
        raise ShopifyPushError("SHOPIFY_ACCESS_TOKEN is not configured")
    url = _shopify_url(path)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "X-Shopify-Access-Token": settings.SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8") or "{}"
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode("utf-8")
        except Exception:
            err = ""
        logger.error("Shopify %s %s failed status=%s body=%s", method, path, e.code, err[:1000])
        if e.code == 429:
            raise ShopifyPushError("Shopify rate limit hit — try again in a few seconds", status_code=429) from e
        if e.code == 401:
            raise ShopifyPushError("Shopify access token rejected (401). Check SHOPIFY_ACCESS_TOKEN.", status_code=401) from e
        if e.code == 404:
            raise ShopifyPushError(f"Shopify resource not found: {path}", status_code=404) from e
        raise ShopifyPushError(
            f"Shopify {method} {path} failed ({e.code}): {_humanize_shopify_error(e.code, err)}",
            status_code=e.code,
        ) from e
    except Exception as e:  # noqa: BLE001
        logger.error("Shopify %s %s error: %s", method, path, e)
        raise ShopifyPushError(str(e)) from e


class ShopifyPushService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # ------------------------------------------------------------------
    # Locations (used for inventory updates)
    # ------------------------------------------------------------------
    def get_primary_location_id(self) -> int:
        """Return the first active Shopify location id (cached per-process)."""
        global _CACHED_LOCATION_ID
        if _CACHED_LOCATION_ID is not None:
            return _CACHED_LOCATION_ID
        payload = _shopify_request("GET", "/locations.json")
        locations = payload.get("locations", [])
        if not locations:
            raise ShopifyPushError("No Shopify locations available")
        active = [loc for loc in locations if loc.get("active")]
        chosen = active[0] if active else locations[0]
        if not chosen.get("id"):
            raise ShopifyPushError("Shopify returned a location without an id")
        _CACHED_LOCATION_ID = int(chosen["id"])
        return _CACHED_LOCATION_ID

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------
    def update_product(
        self,
        product_db_id: UUID,
        *,
        title: str | None = None,
        product_type: str | None = None,
        vendor: str | None = None,
        status: str | None = None,
        body_html: str | None = None,
        performed_by: UUID | None = None,
    ) -> ShopifyProduct:
        product = self.db.query(ShopifyProduct).filter(ShopifyProduct.id == product_db_id).first()
        if not product:
            raise NotFoundException("Shopify product not found")

        update_fields: dict[str, Any] = {"id": product.shopify_product_id}
        if title is not None:
            update_fields["title"] = title
        if product_type is not None:
            update_fields["product_type"] = product_type
        if vendor is not None:
            update_fields["vendor"] = vendor
        if status is not None:
            if status not in ("active", "draft", "archived"):
                raise ConflictException("status must be one of: active, draft, archived")
            update_fields["status"] = status
        if body_html is not None:
            update_fields["body_html"] = body_html

        if len(update_fields) == 1:  # only the id
            return product

        payload = _shopify_request(
            "PUT",
            f"/products/{product.shopify_product_id}.json",
            {"product": update_fields},
        )

        # Mirror to local row
        returned = payload.get("product", {})
        if "title" in returned:
            product.title = returned["title"]
        if "product_type" in returned:
            product.product_type = returned["product_type"]
        if "vendor" in returned:
            product.vendor = returned["vendor"]
        if "status" in returned:
            product.shopify_status = returned["status"]
        product.raw_payload = returned or product.raw_payload

        self.audit.log(
            action=AuditAction.UPDATE,
            entity_type="shopify_product",
            entity_id=product.id,
            performed_by=performed_by,
            payload={"pushed_fields": list(update_fields.keys())},
        )
        self.db.commit()
        self.db.refresh(product)
        return product

    # ------------------------------------------------------------------
    # Variants
    # ------------------------------------------------------------------
    def update_variant(
        self,
        variant_db_id: UUID,
        *,
        title: str | None = None,
        price: str | None = None,
        sku: str | None = None,
        option1: str | None = None,
        option2: str | None = None,
        option3: str | None = None,
        performed_by: UUID | None = None,
    ) -> ShopifyVariant:
        variant = self.db.query(ShopifyVariant).filter(ShopifyVariant.id == variant_db_id).first()
        if not variant:
            raise NotFoundException("Shopify variant not found")

        update_fields: dict[str, Any] = {"id": variant.shopify_variant_id}
        if title is not None:
            update_fields["title"] = title
        if price is not None:
            update_fields["price"] = price
        if sku is not None:
            update_fields["sku"] = sku
        if option1 is not None:
            update_fields["option1"] = option1
        if option2 is not None:
            update_fields["option2"] = option2
        if option3 is not None:
            update_fields["option3"] = option3

        if len(update_fields) == 1:
            return variant

        payload = _shopify_request(
            "PUT",
            f"/variants/{variant.shopify_variant_id}.json",
            {"variant": update_fields},
        )
        returned = payload.get("variant", {})
        if "title" in returned:
            variant.title = returned["title"]
        if "price" in returned:
            variant.price = str(returned["price"])
        if "sku" in returned:
            variant.shopify_sku = returned["sku"]
        if "option1" in returned:
            variant.option1 = returned["option1"]
        if "option2" in returned:
            variant.option2 = returned["option2"]
        if "option3" in returned:
            variant.option3 = returned["option3"]
        if returned.get("inventory_item_id") and not variant.inventory_item_id:
            variant.inventory_item_id = returned["inventory_item_id"]

        self.audit.log(
            action=AuditAction.UPDATE,
            entity_type="shopify_variant",
            entity_id=variant.id,
            performed_by=performed_by,
            payload={"pushed_fields": list(update_fields.keys())},
        )
        self.db.commit()
        self.db.refresh(variant)
        return variant

    def create_variant(
        self,
        product_db_id: UUID,
        *,
        title: str | None = None,
        price: str = "0.00",
        sku: str | None = None,
        option1: str | None = None,
        option2: str | None = None,
        option3: str | None = None,
        performed_by: UUID | None = None,
    ) -> ShopifyVariant:
        product = self.db.query(ShopifyProduct).filter(ShopifyProduct.id == product_db_id).first()
        if not product:
            raise NotFoundException("Shopify product not found")

        body: dict[str, Any] = {
            "price": price,
            "inventory_management": "shopify",
        }
        if title is not None:
            body["title"] = title
        if sku is not None:
            body["sku"] = sku
        if option1 is not None:
            body["option1"] = option1
        if option2 is not None:
            body["option2"] = option2
        if option3 is not None:
            body["option3"] = option3

        payload = _shopify_request(
            "POST",
            f"/products/{product.shopify_product_id}/variants.json",
            {"variant": body},
        )
        returned = payload.get("variant") or {}
        if not returned.get("id"):
            # The POST succeeded on Shopify's side but the response is not in
            # the expected shape — the variant likely exists remotely with no
            # local mirror. Surface as 502 with a recovery hint, not a 500.
            raise ShopifyPushError(
                "Shopify created the variant but returned an unexpected response. "
                "Run a product sync to reconcile."
            )
        new = ShopifyVariant(
            shopify_variant_id=returned["id"],
            shopify_product_id=product.shopify_product_id,
            product_id_fk=product.id,
            title=returned.get("title"),
            shopify_sku=returned.get("sku"),
            price=str(returned.get("price", "")),
            option1=returned.get("option1"),
            option2=returned.get("option2"),
            option3=returned.get("option3"),
            inventory_quantity=returned.get("inventory_quantity"),
            inventory_item_id=returned.get("inventory_item_id"),
            inventory_management=returned.get("inventory_management"),
            mapping_status="unmapped",
        )
        self.db.add(new)
        # Flush first: the UUID default fires at INSERT time, so without this
        # the audit row would be written with entity_id=NULL.
        self.db.flush()
        self.audit.log(
            action=AuditAction.CREATE,
            entity_type="shopify_variant",
            entity_id=new.id,
            performed_by=performed_by,
            payload={"created_on_shopify": True, "shopify_variant_id": new.shopify_variant_id},
        )
        self.db.commit()
        self.db.refresh(new)
        return new

    def delete_variant(self, variant_db_id: UUID, *, performed_by: UUID | None = None) -> None:
        variant = self.db.query(ShopifyVariant).filter(ShopifyVariant.id == variant_db_id).first()
        if not variant:
            raise NotFoundException("Shopify variant not found")

        # Shopify rejects deleting the last variant of a product. Pre-check so
        # the user gets a clear message instead of a generic 422.
        sibling_count = (
            self.db.query(ShopifyVariant)
            .filter(ShopifyVariant.product_id_fk == variant.product_id_fk)
            .count()
        )
        if sibling_count <= 1:
            raise ConflictException(
                "Cannot delete the only variant of a product. Add another variant first, or archive the product instead."
            )

        try:
            _shopify_request(
                "DELETE",
                f"/products/{variant.shopify_product_id}/variants/{variant.shopify_variant_id}.json",
            )
        except ShopifyPushError as e:
            # Already gone on Shopify (stale local mirror) — treat the delete
            # as idempotent so the local orphan row can still be cleaned up.
            if e.status_code != 404:
                raise
        self.audit.log(
            action=AuditAction.DELETE,
            entity_type="shopify_variant",
            entity_id=variant.id,
            performed_by=performed_by,
            payload={"shopify_variant_id": variant.shopify_variant_id},
        )
        self.db.delete(variant)
        self.db.commit()

    # ------------------------------------------------------------------
    # Inventory levels
    # ------------------------------------------------------------------
    def set_inventory_level(
        self,
        variant_db_id: UUID,
        *,
        quantity: int,
        location_id: int | None = None,
        performed_by: UUID | None = None,
    ) -> ShopifyVariant:
        variant = self.db.query(ShopifyVariant).filter(ShopifyVariant.id == variant_db_id).first()
        if not variant:
            raise NotFoundException("Shopify variant not found")
        if not variant.inventory_item_id:
            raise ConflictException(
                "Variant has no inventory_item_id. Sync products from Shopify first."
            )

        loc = location_id or self.get_primary_location_id()

        try:
            _shopify_request(
                "POST",
                "/inventory_levels/set.json",
                {
                    "location_id": loc,
                    "inventory_item_id": variant.inventory_item_id,
                    "available": int(quantity),
                },
            )
        except ShopifyPushError:
            # The cached location may be stale (deactivated/deleted on
            # Shopify). Drop the cache so the next attempt re-resolves it
            # instead of failing forever until a process restart.
            global _CACHED_LOCATION_ID
            if location_id is None:
                _CACHED_LOCATION_ID = None
            raise
        variant.inventory_quantity = int(quantity)
        self.audit.log(
            action=AuditAction.UPDATE,
            entity_type="shopify_variant",
            entity_id=variant.id,
            performed_by=performed_by,
            payload={
                "inventory_set": {"quantity": int(quantity), "location_id": loc},
            },
        )
        self.db.commit()
        self.db.refresh(variant)
        return variant
