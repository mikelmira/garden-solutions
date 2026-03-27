"""
Shopify integration models.

Tables:
- shopify_products: Synced Shopify product records
- shopify_variants: Synced Shopify variants with mapping to internal SKUs
- shopify_orders: Synced Shopify orders with mapping to internal orders
- shopify_webhook_events: Raw webhook payload storage for diagnostics/replay
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ShopifyProduct(Base):
    """Synced Shopify product — one row per Shopify product."""
    __tablename__ = "shopify_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shopify_product_id = Column(BigInteger, nullable=False, unique=True, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    title = Column(String(500), nullable=False)
    product_type = Column(String(255), nullable=True)
    vendor = Column(String(255), nullable=True)
    shopify_handle = Column(String(500), nullable=True)
    shopify_status = Column(String(50), nullable=True)  # active, draft, archived
    raw_payload = Column(JSONB, nullable=True)  # Full Shopify product JSON
    last_synced_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    store = relationship("Store", lazy="joined")
    variants = relationship("ShopifyVariant", back_populates="shopify_product", lazy="joined", cascade="all, delete-orphan")


class ShopifyVariant(Base):
    """
    Synced Shopify variant with optional mapping to internal SKU.

    mapping_status:
      - "mapped"   → sku_id is set, variant is linked to an internal SKU
      - "unmapped"  → no internal SKU match found
      - "ignored"   → admin explicitly marked as not relevant
    """
    __tablename__ = "shopify_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shopify_variant_id = Column(BigInteger, nullable=False, unique=True, index=True)
    shopify_product_id = Column(BigInteger, nullable=False, index=True)
    product_id_fk = Column(UUID(as_uuid=True), ForeignKey("shopify_products.id", ondelete="CASCADE"), nullable=False)

    # Shopify variant details
    title = Column(String(500), nullable=True)
    shopify_sku = Column(String(255), nullable=True, index=True)
    price = Column(String(50), nullable=True)
    option1 = Column(String(255), nullable=True)
    option2 = Column(String(255), nullable=True)
    option3 = Column(String(255), nullable=True)
    inventory_quantity = Column(Integer, nullable=True)

    # Mapping to internal SKU
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=True)
    mapping_status = Column(String(20), nullable=False, default="unmapped", index=True)  # mapped | unmapped | ignored

    last_synced_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    shopify_product = relationship("ShopifyProduct", back_populates="variants")
    sku = relationship("SKU", lazy="joined")


class ShopifyOrder(Base):
    """
    Synced Shopify order with mapping to internal order.

    sync_status:
      - "synced"       → internal order created successfully
      - "partial"      → created but some items unmapped
      - "failed"       → ingestion failed (see error_message)
      - "pending"      → awaiting processing
      - "cancelled"    → Shopify order was cancelled
    """
    __tablename__ = "shopify_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shopify_order_id = Column(BigInteger, nullable=False, unique=True, index=True)
    shopify_order_number = Column(String(100), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)

    # Mapping to internal order (null if not yet created)
    internal_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True, index=True)

    # Shopify order details
    shopify_status = Column(String(50), nullable=True)  # open, closed, cancelled
    financial_status = Column(String(50), nullable=True)  # paid, pending, refunded
    fulfillment_status = Column(String(50), nullable=True)
    customer_name = Column(String(500), nullable=True)
    customer_email = Column(String(500), nullable=True)
    total_price = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    shopify_created_at = Column(DateTime, nullable=True)
    shopify_updated_at = Column(DateTime, nullable=True)

    # Sync tracking
    sync_status = Column(String(20), nullable=False, default="pending", index=True)
    error_message = Column(Text, nullable=True)
    unmapped_items = Column(JSONB, nullable=True)  # List of variant IDs that couldn't be mapped
    raw_payload = Column(JSONB, nullable=True)

    last_synced_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    store = relationship("Store", lazy="joined")
    internal_order = relationship("Order", lazy="joined")


class ShopifyWebhookEvent(Base):
    """
    Raw webhook event log for diagnostics, replay, and idempotency.
    Stores every incoming webhook payload regardless of processing outcome.
    """
    __tablename__ = "shopify_webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shopify_webhook_id = Column(String(255), nullable=True, index=True)  # X-Shopify-Webhook-Id header
    topic = Column(String(100), nullable=False, index=True)  # e.g. "orders/create"
    shop_domain = Column(String(255), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)

    # Processing
    status = Column(String(20), nullable=False, default="received", index=True)  # received | processed | failed | duplicate
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Payload
    raw_payload = Column(JSONB, nullable=True)
    headers = Column(JSONB, nullable=True)

    received_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
