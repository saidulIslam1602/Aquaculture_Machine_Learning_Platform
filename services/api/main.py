"""
Aquaculture Machine Learning Platform - Main FastAPI Application

This module serves as the entry point for the FastAPI-based REST API service
of the Aquaculture ML Platform. It configures the application with all necessary
middleware, routes, error handlers, and integrations required for production use.

Key Features:
- RESTful API endpoints for aquaculture data management
- Machine learning inference integration
- Real-time monitoring and metrics collection
- Database connectivity (PostgreSQL/TimescaleDB)
- Redis caching and session management
- Comprehensive error handling and logging
- Rate limiting and security middleware
- CORS support for frontend integration
- Prometheus metrics instrumentation

Architecture:
The application follows a modular architecture with clear separation of concerns:
- Core: Configuration, database, and infrastructure components
- Routes: API endpoint definitions organized by domain
- Middleware: Cross-cutting concerns (logging, rate limiting, error handling)
- Models: Data models and database schemas
- Utils: Utility functions and helper classes

Author: Aquaculture ML Platform Team
Version: 2.1.0
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging

# Core infrastructure imports
from .core.config import settings
from .core.database import init_db
from .core.timescaledb import initialize_timescaledb
from .core.redis_client import close_redis

# API route imports organized by domain
from .routes import auth, health, tasks, metrics, livestock
from .routes.ml import inference as ml_inference

# Middleware imports for cross-cutting concerns
from .middleware.error_handlers import (
    api_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    APIException,
)
from .middleware.logging_middleware import RequestLoggingMiddleware
from .middleware.rate_limiter import RateLimitMiddleware

# FastAPI and SQLAlchemy exception imports
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add custom middleware (order matters - first added = outermost)
app.add_middleware(RequestLoggingMiddleware)  # Log all requests
if settings.RATE_LIMIT_PER_MINUTE > 0:
    app.add_middleware(RateLimitMiddleware)  # Rate limiting
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Response compression

# Register exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Setup Prometheus metrics
if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(ml_inference.router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX)
app.include_router(livestock.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize TimescaleDB
        if initialize_timescaledb():
            logger.info("TimescaleDB initialized successfully")
        else:
            logger.warning("TimescaleDB initialization failed")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")

    # Close Redis connection
    await close_redis()

    logger.info("Application shutdown complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
