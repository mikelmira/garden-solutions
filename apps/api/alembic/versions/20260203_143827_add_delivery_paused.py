"""add delivery_paused to orders

Revision ID: 20260203_143827
Revises: 4ce431613629
Create Date: 2026-02-03 14:38:27
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260203_143827"
down_revision = "4ce431613629"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("delivery_paused", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.alter_column("orders", "delivery_paused", server_default=None)


def downgrade() -> None:
    op.drop_column("orders", "delivery_paused")
