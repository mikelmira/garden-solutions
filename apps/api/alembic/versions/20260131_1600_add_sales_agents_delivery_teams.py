"""Sprint 4: Add sales agents and delivery teams

Revision ID: 20260131_1600
Revises: 20260131_1000
Create Date: 2026-01-31 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260131_1600'
down_revision: Union[str, None] = '20260131_1000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sales_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_sales_agents_code'),
    )
    op.create_index('ix_sales_agents_code', 'sales_agents', ['code'])

    op.create_table(
        'delivery_teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_delivery_teams_code'),
    )
    op.create_index('ix_delivery_teams_code', 'delivery_teams', ['code'])

    op.create_table(
        'delivery_team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('delivery_team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['delivery_team_id'], ['delivery_teams.id'], name='fk_delivery_team_members_team')
    )
    op.create_index('ix_delivery_team_members_team_id', 'delivery_team_members', ['delivery_team_id'])

    op.add_column('orders', sa.Column('sales_agent_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('orders', sa.Column('delivery_team_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('orders', sa.Column('delivery_status', sa.String(50), nullable=True))
    op.add_column('orders', sa.Column('delivery_status_reason', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('delivery_receiver_name', sa.String(255), nullable=True))
    op.add_column('orders', sa.Column('delivered_at', sa.DateTime(), nullable=True))

    op.create_index('ix_orders_sales_agent_id', 'orders', ['sales_agent_id'])
    op.create_index('ix_orders_delivery_team_id', 'orders', ['delivery_team_id'])
    op.create_index('ix_orders_delivery_status', 'orders', ['delivery_status'])

    op.create_foreign_key('fk_orders_sales_agent', 'orders', 'sales_agents', ['sales_agent_id'], ['id'])
    op.create_foreign_key('fk_orders_delivery_team', 'orders', 'delivery_teams', ['delivery_team_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_orders_delivery_team', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_sales_agent', 'orders', type_='foreignkey')

    op.drop_index('ix_orders_delivery_status', table_name='orders')
    op.drop_index('ix_orders_delivery_team_id', table_name='orders')
    op.drop_index('ix_orders_sales_agent_id', table_name='orders')

    op.drop_column('orders', 'delivered_at')
    op.drop_column('orders', 'delivery_receiver_name')
    op.drop_column('orders', 'delivery_status_reason')
    op.drop_column('orders', 'delivery_status')
    op.drop_column('orders', 'delivery_team_id')
    op.drop_column('orders', 'sales_agent_id')

    op.drop_index('ix_delivery_team_members_team_id', table_name='delivery_team_members')
    op.drop_table('delivery_team_members')

    op.drop_index('ix_delivery_teams_code', table_name='delivery_teams')
    op.drop_table('delivery_teams')

    op.drop_index('ix_sales_agents_code', table_name='sales_agents')
    op.drop_table('sales_agents')
