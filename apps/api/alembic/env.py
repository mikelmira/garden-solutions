import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app_dir = os.path.join(base_dir, "app")
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
from app.core.config import get_settings
from app.core.database import Base

# Import all models so Alembic can see them for autogenerate
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.price_tier import PriceTier
from app.models.client import Client
from app.models.product import Product
from app.models.sku import SKU
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.sales_agent import SalesAgent
from app.models.delivery_team import DeliveryTeam
from app.models.delivery_team_member import DeliveryTeamMember

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

settings = get_settings()
# Overwrite sqlalchemy.url with the one from settings
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
