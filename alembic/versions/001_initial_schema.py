"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-27 12:00:00.000000

Multi-cloud compatible database schema for the Aquaculture ML Platform.
Supports PostgreSQL, SQL Server, and MySQL across AWS, Azure, and GCP.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mssql, mysql
import uuid


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def get_uuid_column():
    """Get UUID column type based on database dialect"""
    dialect = op.get_bind().dialect.name
    
    if dialect == 'postgresql':
        return postgresql.UUID(as_uuid=True)
    elif dialect == 'mssql':
        return mssql.UNIQUEIDENTIFIER()
    else:  # MySQL and others
        return sa.String(36)


def get_json_column():
    """Get JSON column type based on database dialect"""
    dialect = op.get_bind().dialect.name
    
    if dialect == 'postgresql':
        return postgresql.JSONB()
    elif dialect == 'mssql':
        return sa.Text()  # SQL Server 2016+ has JSON support, but we'll use TEXT for compatibility
    else:  # MySQL 5.7+
        return mysql.JSON()


def upgrade() -> None:
    """Create all tables for the aquaculture platform"""
    
    # Users table - Authentication and user management
    op.create_table(
        'users',
        sa.Column('id', get_uuid_column(), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_superuser', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Fish Species table - Master data for fish species
    op.create_table(
        'fish_species',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('scientific_name', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('optimal_temperature_min', sa.Numeric(5, 2), nullable=True),
        sa.Column('optimal_temperature_max', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # ML Models table - Model versioning and metadata
    op.create_table(
        'models',
        sa.Column('id', get_uuid_column(), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('architecture', sa.String(100), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('accuracy', sa.Numeric(5, 4), nullable=True),
        sa.Column('precision_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('recall_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('f1_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=False, nullable=False),
        sa.Column('model_metadata', get_json_column(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', get_uuid_column(), nullable=True),
    )
    
    # Predictions table - ML prediction results
    op.create_table(
        'predictions',
        sa.Column('id', get_uuid_column(), primary_key=True, default=uuid.uuid4),
        sa.Column('model_id', get_uuid_column(), nullable=True),
        sa.Column('image_path', sa.String(500), nullable=True),
        sa.Column('predicted_species_id', sa.Integer(), nullable=True),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('inference_time_ms', sa.Integer(), nullable=True),
        sa.Column('prediction_metadata', get_json_column(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', get_uuid_column(), nullable=True),
    )
    
    # Audit Logs table - System audit trail
    op.create_table(
        'audit_logs',
        sa.Column('id', get_uuid_column(), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', get_uuid_column(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('details', get_json_column(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 compatible
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # System Metrics table - Performance and monitoring data
    op.create_table(
        'system_metrics',
        sa.Column('id', get_uuid_column(), primary_key=True, default=uuid.uuid4),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(50), nullable=True),
        sa.Column('tags', get_json_column(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create Foreign Key Constraints
    op.create_foreign_key(
        'fk_predictions_model_id',
        'predictions', 'models',
        ['model_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_predictions_species_id',
        'predictions', 'fish_species',
        ['predicted_species_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_predictions_created_by',
        'predictions', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_models_created_by',
        'models', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_audit_logs_user_id',
        'audit_logs', 'users',
        ['user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create Indexes for Performance
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_active', 'users', ['is_active'])
    
    op.create_index('idx_fish_species_name', 'fish_species', ['name'])
    
    op.create_index('idx_models_name_version', 'models', ['name', 'version'])
    op.create_index('idx_models_active', 'models', ['is_active'])
    op.create_index('idx_models_created_at', 'models', ['created_at'])
    
    op.create_index('idx_predictions_created_at', 'predictions', ['created_at'])
    op.create_index('idx_predictions_species', 'predictions', ['predicted_species_id'])
    op.create_index('idx_predictions_confidence', 'predictions', ['confidence'])
    op.create_index('idx_predictions_model', 'predictions', ['model_id'])
    
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    
    op.create_index('idx_system_metrics_name_timestamp', 'system_metrics', ['metric_name', 'timestamp'])
    op.create_index('idx_system_metrics_timestamp', 'system_metrics', ['timestamp'])


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop indexes first
    op.drop_index('idx_system_metrics_timestamp')
    op.drop_index('idx_system_metrics_name_timestamp')
    op.drop_index('idx_audit_logs_action')
    op.drop_index('idx_audit_logs_user')
    op.drop_index('idx_audit_logs_created_at')
    op.drop_index('idx_predictions_model')
    op.drop_index('idx_predictions_confidence')
    op.drop_index('idx_predictions_species')
    op.drop_index('idx_predictions_created_at')
    op.drop_index('idx_models_created_at')
    op.drop_index('idx_models_active')
    op.drop_index('idx_models_name_version')
    op.drop_index('idx_fish_species_name')
    op.drop_index('idx_users_active')
    op.drop_index('idx_users_username')
    op.drop_index('idx_users_email')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_audit_logs_user_id', 'audit_logs', type_='foreignkey')
    op.drop_constraint('fk_models_created_by', 'models', type_='foreignkey')
    op.drop_constraint('fk_predictions_created_by', 'predictions', type_='foreignkey')
    op.drop_constraint('fk_predictions_species_id', 'predictions', type_='foreignkey')
    op.drop_constraint('fk_predictions_model_id', 'predictions', type_='foreignkey')
    
    # Drop tables in reverse order
    op.drop_table('system_metrics')
    op.drop_table('audit_logs')
    op.drop_table('predictions')
    op.drop_table('models')
    op.drop_table('fish_species')
    op.drop_table('users')
