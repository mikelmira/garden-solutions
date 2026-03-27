"""Sprint 1: Add core business entities

Creates tables for:
- price_tiers: Global discount structures
- clients: B2B customers
- products: Top-level product definitions
- skus: Specific sellable variants
- orders: B2B sale headers
- order_items: Line items within orders

Per docs:
- Use VARCHAR for status fields (not PostgreSQL ENUM) for flexibility
- All monetary values use Numeric/Decimal
- Foreign keys with appropriate cascades

Revision ID: 20260130_1400
Revises: 20260130_1200
Create Date: 2026-01-30 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260130_1400'
down_revision: Union[str, None] = '20260130_1200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create price_tiers table
    op.create_table(
        'price_tiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('discount_percentage', sa.Numeric(5, 4), nullable=False, server_default='0.0000'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_price_tiers_name')
    )

    # Create clients table - per Sprint 1 spec: id, name, tier_id, created_by, timestamps
    op.create_table(
        'clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tier_id'], ['price_tiers.id'], name='fk_clients_tier'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_clients_created_by')
    )
    op.create_index('ix_clients_name', 'clients', ['name'])
    op.create_index('ix_clients_created_by', 'clients', ['created_by'])

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_products_category', 'products', ['category'])

    # Create skus table
    op.create_table(
        'skus',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('size', sa.String(50), nullable=False),
        sa.Column('color', sa.String(50), nullable=False),
        sa.Column('base_price_rands', sa.Numeric(12, 2), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_skus_product'),
        sa.UniqueConstraint('code', name='uq_skus_code')
    )
    op.create_index('ix_skus_code', 'skus', ['code'])
    op.create_index('ix_skus_product_id', 'skus', ['product_id'])

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sales_agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('delivery_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending_approval'),
        sa.Column('total_price_rands', sa.Numeric(14, 2), nullable=False, server_default='0.00'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='fk_orders_client'),
        sa.ForeignKeyConstraint(['sales_agent_id'], ['users.id'], name='fk_orders_sales_agent')
    )
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_client_id', 'orders', ['client_id'])
    op.create_index('ix_orders_sales_agent_id', 'orders', ['sales_agent_id'])
    op.create_index('ix_orders_delivery_date', 'orders', ['delivery_date'])

    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity_ordered', sa.Integer(), nullable=False),
        sa.Column('quantity_manufactured', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit_price_rands', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='fk_order_items_order', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sku_id'], ['skus.id'], name='fk_order_items_sku')
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_sku_id', 'order_items', ['sku_id'])


def downgrade() -> None:
    # Drop order_items table
    op.drop_index('ix_order_items_sku_id', table_name='order_items')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_table('order_items')

    # Drop orders table
    op.drop_index('ix_orders_delivery_date', table_name='orders')
    op.drop_index('ix_orders_sales_agent_id', table_name='orders')
    op.drop_index('ix_orders_client_id', table_name='orders')
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_table('orders')

    # Drop skus table
    op.drop_index('ix_skus_product_id', table_name='skus')
    op.drop_index('ix_skus_code', table_name='skus')
    op.drop_table('skus')

    # Drop products table
    op.drop_index('ix_products_category', table_name='products')
    op.drop_index('ix_products_name', table_name='products')
    op.drop_table('products')

    # Drop clients table
    op.drop_index('ix_clients_created_by', table_name='clients')
    op.drop_index('ix_clients_name', table_name='clients')
    op.drop_table('clients')

    # Drop price_tiers table
    op.drop_table('price_tiers')
