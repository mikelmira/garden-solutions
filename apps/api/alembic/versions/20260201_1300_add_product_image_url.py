"""add product image_url

Revision ID: 20260201_1300
Revises: 20260201_1200
Create Date: 2026-02-01 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260201_1300"
down_revision = "20260201_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "image_url")
