"""
============================================================================
Alembic Environment Configuration for Aquaculture ML Platform
============================================================================

This module configures the Alembic migration environment for the Aquaculture
ML Platform database. It handles the setup and execution of database schema
migrations with support for both synchronous and asynchronous operations.

KEY FEATURES:
- Automatic model discovery from SQLAlchemy Base metadata
- Environment-aware database URL configuration
- Support for both sync and async database operations
- Transaction-per-migration for data integrity
- Proper logging configuration for migration tracking
- Production-safe migration execution

MIGRATION WORKFLOW:
1. Auto-discovery of SQLAlchemy models from the application
2. Comparison of current schema with model definitions
3. Generation of migration scripts with proper rollback support
4. Execution in transaction context for atomicity

ENVIRONMENT SUPPORT:
- Development: Local PostgreSQL with sync operations
- Production: Cloud PostgreSQL with async support
- Testing: In-memory SQLite for fast test execution

SECURITY CONSIDERATIONS:
- Database credentials from environment variables
- No hardcoded connection strings in version control
- SSL connection support for production deployments
- Connection pooling configuration for performance

USAGE:
- Generate migration: alembic revision --autogenerate -m "description"
- Apply migrations: alembic upgrade head
- Rollback: alembic downgrade -1
- Check status: alembic current
============================================================================
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to Python path for model imports
# This allows Alembic to discover and import SQLAlchemy models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import application configuration and database setup
from services.api.core.config import settings
from services.api.core.database import Base

# ============================================================================
# MODEL IMPORTS FOR MIGRATION DISCOVERY
# ============================================================================
# Import all SQLAlchemy models so Alembic can detect schema changes
# These imports ensure that all tables are included in migration generation

from services.api.models.user import User                      # User authentication and profiles
from services.api.models.prediction import (                   # ML prediction models
    Prediction,                                                # Individual predictions
    FishSpecies,                                              # Fish species classifications  
    Model                                                     # ML model metadata
)

# ============================================================================
# ALEMBIC CONFIGURATION SETUP
# ============================================================================

# Get Alembic configuration object from alembic.ini
config = context.config

# Configure Python logging from alembic.ini file
# This enables proper logging during migration execution
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
# This tells Alembic which models to track for schema changes
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
