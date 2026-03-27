"""Add Shopify integration tables.

Revision ID: shopify_integration_001
Revises: 20260203_1600_add_factory_teams
Create Date: 2026-03-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "shopify_integration_001"
down_revision = "20260203_1600_add_factory_teams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── shopify_products ──────────────────────────────────────
    op.create_table(
        "shopify_products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("shopify_product_id", sa.BigInteger, nullable=False, unique=True, index=True),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("product_type", sa.String(255), nullable=True),
        sa.Column("vendor", sa.String(255), nullable=True),
        sa.Column("shopify_handle", sa.String(500), nullable=True),
        sa.Column("shopify_status", sa.String(50), nullable=True),
        sa.Column("raw_payload", JSONB, nullable=True),
        sa.Column("last_synced_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ── shopify_variants ──────────────────────────────────────
    op.create_table(
        "shopify_variants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("shopify_variant_id", sa.BigInteger, nullable=False, unique=True, index=True),
        sa.Column("shopify_product_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("product_id_fk", UUID(as_uuid=True), sa.ForeignKey("shopify_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("shopify_sku", sa.String(255), nullable=True, index=True),
        sa.Column("price", sa.String(50), nullable=True),
        sa.Column("option1", sa.String(255), nullable=True),
        sa.Column("option2", sa.String(255), nullable=True),
        sa.Column("option3", sa.String(255), nullable=True),
        sa.Column("inventory_quantity", sa.Integer, nullable=True),
        sa.Column("sku_id", UUID(as_uuid=True), sa.ForeignKey("skus.id"), nullable=True),
        sa.Column("mapping_status", sa.String(20), nullable=False, default="unmapped", index=True),
        sa.Column("last_synced_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ── shopify_orders ────────────────────────────────────────
    op.create_table(
        "shopify_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("shopify_order_id", sa.BigInteger, nullable=False, unique=True, index=True),
        sa.Column("shopify_order_number", sa.String(100), nullable=True),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("internal_order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=True, index=True),
        sa.Column("shopify_status", sa.String(50), nullable=True),
        sa.Column("financial_status", sa.String(50), nullable=True),
        sa.Column("fulfillment_status", sa.String(50), nullable=True),
        sa.Column("customer_name", sa.String(500), nullable=True),
        sa.Column("customer_email", sa.String(500), nullable=True),
        sa.Column("total_price", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("shopify_created_at", sa.DateTime, nullable=True),
        sa.Column("shopify_updated_at", sa.DateTime, nullable=True),
        sa.Column("sync_status", sa.String(20), nullable=False, default="pending", index=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("unmapped_items", JSONB, nullable=True),
        sa.Column("raw_payload", JSONB, nullable=True),
        sa.Column("last_synced_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ── shopify_webhook_events ────────────────────────────────
    op.create_table(
        "shopify_webhook_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("shopify_webhook_id", sa.String(255), nullable=True, index=True),
        sa.Column("topic", sa.String(100), nullable=False, index=True),
        sa.Column("shop_domain", sa.String(255), nullable=True),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="received", index=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("processing_time_ms", sa.Integer, nullable=True),
        sa.Column("raw_payload", JSONB, nullable=True),
        sa.Column("headers", JSONB, nullable=True),
        sa.Column("received_at", sa.DateTime, nullable=False, index=True),
        sa.Column("processed_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("shopify_webhook_events")
    op.drop_table("shopify_orders")
    op.drop_table("shopify_variants")
    op.drop_table("shopify_products")
