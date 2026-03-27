"""add stores and order source

Revision ID: 20260201_1000
Revises: 20260131_1600
Create Date: 2026-02-01 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260201_1000"
down_revision = "20260131_1600"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("store_type", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_stores_code", "stores", ["code"], unique=True)

    op.add_column("orders", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("orders", sa.Column("order_source", sa.String(length=50), nullable=True))
    op.create_index("ix_orders_store_id", "orders", ["store_id"])
    op.create_index("ix_orders_order_source", "orders", ["order_source"])
    op.create_foreign_key(
        "fk_orders_store_id",
        "orders",
        "stores",
        ["store_id"],
        ["id"],
    )

    op.alter_column("orders", "client_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    op.alter_column("orders", "client_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.drop_constraint("fk_orders_store_id", "orders", type_="foreignkey")
    op.drop_index("ix_orders_order_source", table_name="orders")
    op.drop_index("ix_orders_store_id", table_name="orders")
    op.drop_column("orders", "order_source")
    op.drop_column("orders", "store_id")

    op.drop_index("ix_stores_code", table_name="stores")
    op.drop_table("stores")
