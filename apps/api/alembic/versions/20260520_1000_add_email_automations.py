"""add email_automations table

Revision ID: 20260520_1000_automations
Revises: 20260430_1100_shopify_inv
Create Date: 2026-05-20 10:00:00.000000

Adds EmailAutomation: scheduled or one-off plan emails (moulding / painting /
orders / deliveries). The existing email_recipients table continues to serve
the "fire on plan creation" flow; automations are independent.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "20260520_1000_automations"
down_revision = "20260430_1100_shopify_inv"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_automations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("plan_type", sa.String(length=20), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("send_time", sa.Time(), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("send_at", sa.DateTime(), nullable=True),
        sa.Column("recipients", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_email_automations_plan_type", "email_automations", ["plan_type"])
    op.create_index("ix_email_automations_next_run_at", "email_automations", ["next_run_at"])


def downgrade():
    op.drop_index("ix_email_automations_next_run_at", table_name="email_automations")
    op.drop_index("ix_email_automations_plan_type", table_name="email_automations")
    op.drop_table("email_automations")
