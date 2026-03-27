"""Add manufacturing day plans and inventory tracking

Creates tables for:
- inventory_items: Global SKU-level stock on hand
- manufacturing_days: Daily manufacturing plan headers
- manufacturing_day_items: Line items in daily plans

Also adds:
- quantity_allocated column to order_items for FIFO allocation tracking

Revision ID: 20260202_1000
Revises: 20260201_1300
Create Date: 2026-02-02 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260202_1000'
down_revision: Union[str, None] = '20260201_1300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create inventory_items table
    op.create_table(
        'inventory_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity_on_hand', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sku_id'], ['skus.id'], name='fk_inventory_items_sku'),
        sa.UniqueConstraint('sku_id', name='uq_inventory_items_sku_id')
    )
    op.create_index('ix_inventory_items_sku_id', 'inventory_items', ['sku_id'])

    # Create manufacturing_days table
    op.create_table(
        'manufacturing_days',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_date', sa.Date(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_manufacturing_days_created_by'),
        sa.UniqueConstraint('plan_date', name='uq_manufacturing_days_plan_date')
    )
    op.create_index('ix_manufacturing_days_plan_date', 'manufacturing_days', ['plan_date'])

    # Create manufacturing_day_items table
    op.create_table(
        'manufacturing_day_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manufacturing_day_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity_planned', sa.Integer(), nullable=False),
        sa.Column('quantity_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['manufacturing_day_id'], ['manufacturing_days.id'], name='fk_mfg_day_items_day', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sku_id'], ['skus.id'], name='fk_mfg_day_items_sku')
    )
    op.create_index('ix_manufacturing_day_items_day_id', 'manufacturing_day_items', ['manufacturing_day_id'])
    op.create_index('ix_manufacturing_day_items_sku_id', 'manufacturing_day_items', ['sku_id'])

    # Add quantity_allocated to order_items (nullable at first for backwards compat)
    op.add_column('order_items', sa.Column('quantity_allocated', sa.Integer(), nullable=True, server_default='0'))

    # Backfill existing rows with 0
    op.execute("UPDATE order_items SET quantity_allocated = 0 WHERE quantity_allocated IS NULL")

    # Now make it NOT NULL
    op.alter_column('order_items', 'quantity_allocated', nullable=False)


def downgrade() -> None:
    # Remove quantity_allocated from order_items
    op.drop_column('order_items', 'quantity_allocated')

    # Drop manufacturing_day_items table
    op.drop_index('ix_manufacturing_day_items_sku_id', table_name='manufacturing_day_items')
    op.drop_index('ix_manufacturing_day_items_day_id', table_name='manufacturing_day_items')
    op.drop_table('manufacturing_day_items')

    # Drop manufacturing_days table
    op.drop_index('ix_manufacturing_days_plan_date', table_name='manufacturing_days')
    op.drop_table('manufacturing_days')

    # Drop inventory_items table
    op.drop_index('ix_inventory_items_sku_id', table_name='inventory_items')
    op.drop_table('inventory_items')
