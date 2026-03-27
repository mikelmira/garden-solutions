"""Sprint 2.1: Add optional address field to clients table

Adds Client.address as nullable VARCHAR(500) to support frontend display.

Revision ID: 20260131_1000
Revises: 20260130_1500
Create Date: 2026-01-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '20260131_1000'
down_revision: Union[str, None] = '20260130_1500'
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


def upgrade() -> None:
    # Add address column to clients table if it doesn't exist
    if not column_exists('clients', 'address'):
        op.add_column('clients', sa.Column('address', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove address column if it exists
    if column_exists('clients', 'address'):
        op.drop_column('clients', 'address')
