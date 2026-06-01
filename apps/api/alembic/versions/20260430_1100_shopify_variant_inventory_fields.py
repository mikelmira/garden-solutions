"""add inventory_item_id + inventory_management to shopify_variants

Revision ID: 20260430_1100_shopify_inv
Revises: 20260430_1000_painting
Create Date: 2026-04-30 11:00:00.000000

Adds the two columns needed to push inventory updates back to Shopify
via the Admin API:
- inventory_item_id (Shopify's stable identifier for the variant's inventory)
- inventory_management (whether Shopify manages this variant's stock)
"""
from alembic import op
import sqlalchemy as sa


revision = "20260430_1100_shopify_inv"
down_revision = "20260430_1000_painting"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "shopify_variants",
        sa.Column("inventory_item_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "shopify_variants",
        sa.Column("inventory_management", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ix_shopify_variants_inventory_item_id",
        "shopify_variants",
        ["inventory_item_id"],
    )


def downgrade():
    op.drop_index("ix_shopify_variants_inventory_item_id", table_name="shopify_variants")
    op.drop_column("shopify_variants", "inventory_management")
    op.drop_column("shopify_variants", "inventory_item_id")
