"""Sprint 1.1 Hotfix: Rename orders.sales_agent_id to orders.created_by

Aligns Order ownership field naming with spec and Client model consistency.
This is a spec-alignment cleanup before frontend integration.

Safety: Uses conditional checks to handle both fresh installs and existing DBs.

Revision ID: 20260130_1500
Revises: 20260130_1400
Create Date: 2026-01-30 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260130_1500'
down_revision: Union[str, None] = '20260130_1400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table: str, column: str) -> bool:
    """Check if a column exists in the given table."""
    bind = op.get_bind()
    result = bind.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = :table_name
              AND column_name = :column
            LIMIT 1
            """
        ),
        {"table_name": table, "column": column},
    ).scalar()
    return result is not None


def index_exists(index_name: str) -> bool:
    """Check if an index exists in the current schema."""
    bind = op.get_bind()
    result = bind.execute(
        text(
            """
            SELECT 1
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'i'
              AND n.nspname = current_schema()
              AND c.relname = :index_name
            LIMIT 1
            """
        ),
        {"index_name": index_name},
    ).scalar()
    return result is not None


def fk_exists(table: str, fk_name: str) -> bool:
    """Check if a foreign key constraint exists on the given table."""
    bind = op.get_bind()
    result = bind.execute(
        text(
            """
            SELECT 1
            FROM pg_catalog.pg_constraint con
            JOIN pg_catalog.pg_class rel ON rel.oid = con.conrelid
            JOIN pg_catalog.pg_namespace n ON n.oid = rel.relnamespace
            WHERE con.contype = 'f'
              AND n.nspname = current_schema()
              AND rel.relname = :table_name
              AND con.conname = :fk_name
            LIMIT 1
            """
        ),
        {"table_name": table, "fk_name": fk_name},
    ).scalar()
    return result is not None


def upgrade() -> None:
    sales_agent_exists = column_exists('orders', 'sales_agent_id')
    created_by_exists = column_exists('orders', 'created_by')

    if sales_agent_exists and not created_by_exists:
        op.alter_column('orders', 'sales_agent_id', new_column_name='created_by')

        if index_exists('ix_orders_sales_agent_id') and not index_exists('ix_orders_created_by'):
            op.execute("ALTER INDEX ix_orders_sales_agent_id RENAME TO ix_orders_created_by")

        if fk_exists('orders', 'fk_orders_sales_agent') and not fk_exists('orders', 'fk_orders_created_by'):
            op.execute("ALTER TABLE orders RENAME CONSTRAINT fk_orders_sales_agent TO fk_orders_created_by")


def downgrade() -> None:
    created_by_exists = column_exists('orders', 'created_by')
    sales_agent_exists = column_exists('orders', 'sales_agent_id')

    if created_by_exists and not sales_agent_exists:
        op.alter_column('orders', 'created_by', new_column_name='sales_agent_id')

        if index_exists('ix_orders_created_by') and not index_exists('ix_orders_sales_agent_id'):
            op.execute("ALTER INDEX ix_orders_created_by RENAME TO ix_orders_sales_agent_id")

        if fk_exists('orders', 'fk_orders_created_by') and not fk_exists('orders', 'fk_orders_sales_agent'):
            op.execute("ALTER TABLE orders RENAME CONSTRAINT fk_orders_created_by TO fk_orders_sales_agent")
