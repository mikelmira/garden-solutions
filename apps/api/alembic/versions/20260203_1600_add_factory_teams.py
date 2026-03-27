"""add factory teams

Revision ID: 20260203_1600_add_factory_teams
Revises: 20260203_143827
Create Date: 2026-02-03 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260203_1600_add_factory_teams"
down_revision = "20260203_143827"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "factory_teams",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_factory_teams_code", "factory_teams", ["code"], unique=True)

    op.create_table(
        "factory_team_members",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("factory_team_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("factory_teams.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_factory_team_members_code", "factory_team_members", ["code"], unique=True)


def downgrade():
    op.drop_index("ix_factory_team_members_code", table_name="factory_team_members")
    op.drop_table("factory_team_members")
    op.drop_index("ix_factory_teams_code", table_name="factory_teams")
    op.drop_table("factory_teams")
