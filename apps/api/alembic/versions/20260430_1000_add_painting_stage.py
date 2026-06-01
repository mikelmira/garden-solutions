"""add painting stage: teams, daily plan, quantity_painted column, email_recipients

Revision ID: 20260430_1000_painting
Revises: shopify_integration_001
Create Date: 2026-04-30 10:00:00.000000

Adds the painting stage that sits between moulding (in_production) and
ready_for_delivery in the order lifecycle.

- order_items.quantity_painted (Integer, default 0)
- painting_teams, painting_team_members (mirror factory_teams shape)
- painting_days header + painting_day_items keyed on order_item_id
- email_recipients (who gets the daily moulding/painting plan emails)

Order status enum and User role are VARCHAR with app-level validation so
no DB-level enum changes are required.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "20260430_1000_painting"
down_revision = "shopify_integration_001"
branch_labels = None
depends_on = None


def upgrade():
    # --- quantity_painted on order_items ---
    op.add_column(
        "order_items",
        sa.Column("quantity_painted", sa.Integer(), nullable=False, server_default="0"),
    )
    # Drop the server_default after backfilling so future inserts rely on app default.
    op.alter_column("order_items", "quantity_painted", server_default=None)

    # --- painting_teams ---
    op.create_table(
        "painting_teams",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_painting_teams_code", "painting_teams", ["code"], unique=True)

    # --- painting_team_members ---
    op.create_table(
        "painting_team_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "painting_team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("painting_teams.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_painting_team_members_code", "painting_team_members", ["code"], unique=True
    )

    # --- painting_days ---
    op.create_table(
        "painting_days",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column(
            "created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_painting_days_plan_date", "painting_days", ["plan_date"], unique=True
    )

    # --- painting_day_items (FK to order_items, NOT skus) ---
    op.create_table(
        "painting_day_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "painting_day_id",
            UUID(as_uuid=True),
            sa.ForeignKey("painting_days.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_item_id",
            UUID(as_uuid=True),
            sa.ForeignKey("order_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity_planned", sa.Integer(), nullable=False),
        sa.Column("quantity_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_painting_day_items_order_item_id",
        "painting_day_items",
        ["order_item_id"],
    )
    op.alter_column("painting_day_items", "quantity_completed", server_default=None)

    # --- email_recipients ---
    op.create_table(
        "email_recipients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column(
            "category",
            sa.String(length=20),
            nullable=False,
            server_default="moulding",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_email_recipients_email", "email_recipients", ["email"])


def downgrade():
    op.drop_index("ix_email_recipients_email", table_name="email_recipients")
    op.drop_table("email_recipients")
    op.drop_index("ix_painting_day_items_order_item_id", table_name="painting_day_items")
    op.drop_table("painting_day_items")
    op.drop_index("ix_painting_days_plan_date", table_name="painting_days")
    op.drop_table("painting_days")
    op.drop_index("ix_painting_team_members_code", table_name="painting_team_members")
    op.drop_table("painting_team_members")
    op.drop_index("ix_painting_teams_code", table_name="painting_teams")
    op.drop_table("painting_teams")
    op.drop_column("order_items", "quantity_painted")
