"""add store contact fields and sales agent phone

Revision ID: 20260201_1200
Revises: 20260201_1000
Create Date: 2026-02-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260201_1200"
down_revision = "20260201_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stores", sa.Column("address", sa.String(length=500), nullable=True))
    op.add_column("stores", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column("stores", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("sales_agents", sa.Column("phone", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("sales_agents", "phone")
    op.drop_column("stores", "email")
    op.drop_column("stores", "phone")
    op.drop_column("stores", "address")
