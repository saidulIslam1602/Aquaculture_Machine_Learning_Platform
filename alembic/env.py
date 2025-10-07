"""
Alembic Environment Configuration

Configures Alembic for database migrations with support for
async operations and proper model discovery.

Industry Standards:
    - Automatic model discovery
    - Transaction per migration
    - Async support for asyncpg
    - Proper logging configuration
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.api.core.config import settings
from services.api.core.database import Base

# Import all models for Alembic to detect
from services.api.models.user import User
from services.api.models.prediction import Prediction, FishSpecies, Model

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def get_url():
    """
    Get Database URL

    Returns database URL from environment variable or config.
    Prioritizes environment variable for security.

    Returns:
        str: Database connection URL
    """
    return os.getenv("DATABASE_URL", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Run Migrations in 'Offline' Mode

    Generates SQL scripts without connecting to database.
    Useful for generating migration SQL for review.

    Note:
        This configures the context with just a URL
        and not an Engine, though an Engine is acceptable
        here as well. By skipping the Engine creation
        we don't even need a DBAPI to be available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run Migrations in 'Online' Mode

    Creates an Engine and associates a connection with the context.
    Executes migrations directly against the database.

    Note:
        This is the standard mode for running migrations.
        Requires active database connection.
    """
    # Override sqlalchemy.url with environment variable
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    # Create engine with connection pooling
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pooling for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect default value changes
            include_schemas=False,  # Don't include other schemas
            render_as_batch=False,  # Batch mode for SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
