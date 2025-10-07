"""
Database Connection and Session Management Module

This module provides database connectivity using SQLAlchemy ORM with
connection pooling, session management, and dependency injection patterns.

Industry Standards:
    - Connection pooling for performance
    - Context manager pattern for session lifecycle
    - Dependency injection for FastAPI
    - Declarative base for ORM models
    - Pool pre-ping for connection health checks
    
Architecture:
    - Engine: Database connection pool manager
    - SessionLocal: Session factory for creating DB sessions
    - Base: Declarative base class for all ORM models
    - get_db: Dependency injection function for FastAPI routes
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from .config import settings

# Database Engine Configuration
# SQLAlchemy engine manages connection pool and database communication
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,  # Number of persistent connections
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Additional connections when pool is full
    pool_pre_ping=True,  # Verify connection health before using (prevents stale connections)
    echo=settings.DEBUG,  # Log all SQL statements when DEBUG=True
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent timeout issues
    connect_args={
        "options": "-c timezone=utc"  # Set timezone to UTC for consistency
    }
)

# Session Factory
# Creates new database sessions with proper configuration
# autocommit=False: Explicit transaction control (recommended)
# autoflush=False: Manual flush control for better performance
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent expired object errors after commit
)

# Declarative Base
# Base class for all ORM models
# All models should inherit from this class
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database Session Dependency (Dependency Injection Pattern)
    
    Provides a database session for FastAPI route handlers.
    Automatically handles session lifecycle: creation, usage, and cleanup.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        ```python
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
    
    Note:
        - Session is automatically closed after request completion
        - Exceptions trigger automatic rollback
        - Use with FastAPI's Depends() for dependency injection
        
    Best Practices:
        - Always use this dependency instead of creating sessions manually
        - Never store sessions in global variables
        - Let FastAPI handle session lifecycle
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Rollback on any exception to maintain database consistency
        db.rollback()
        raise
    finally:
        # Always close session to return connection to pool
        db.close()


def init_db() -> None:
    """
    Initialize Database Schema
    
    Creates all tables defined in SQLAlchemy models.
    Should be called on application startup.
    
    Note:
        - Only creates tables that don't exist
        - Does not handle migrations (use Alembic for that)
        - Safe to call multiple times (idempotent)
        
    Example:
        ```python
        @app.on_event("startup")
        async def startup():
            init_db()
        ```
    
    Warning:
        In production, use Alembic migrations instead of this function.
        This is primarily for development and testing.
    """
    Base.metadata.create_all(bind=engine)
