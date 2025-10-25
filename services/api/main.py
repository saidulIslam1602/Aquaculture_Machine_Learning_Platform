"""
============================================================================
Aquaculture ML Platform - FastAPI Main Application
============================================================================

This module serves as the entry point for the Aquaculture Machine Learning
Platform's REST API service. Built with FastAPI, it provides a modern,
high-performance web API with automatic documentation, data validation,
and comprehensive monitoring.

CORE FEATURES:
- RESTful API endpoints for aquaculture data management
- ML model inference and prediction services
- User authentication and authorization
- Real-time monitoring and metrics collection
- Rate limiting and security middleware
- Comprehensive error handling and logging

ARCHITECTURE:
- FastAPI framework with async/await support
- PostgreSQL database with SQLAlchemy ORM
- Redis caching and session management
- Celery integration for background tasks
- Prometheus metrics for observability
- CORS support for frontend integration

ENDPOINT GROUPS:
- /health: System health checks and status
- /auth: User authentication and authorization
- /api/v1/predictions: ML prediction services
- /api/v1/models: ML model management
- /api/v1/tasks: Background task management
- /metrics: Prometheus metrics endpoint

MIDDLEWARE STACK:
- CORS: Cross-origin request handling
- Rate Limiting: API abuse prevention
- Request Logging: Structured request/response logging
- Error Handling: Consistent error responses
- Compression: GZip response compression
- Metrics: Prometheus instrumentation

USAGE:
This application is typically run via:
- Development: uvicorn services.api.main:app --reload
- Production: gunicorn services.api.main:app -k uvicorn.workers.UvicornWorker
- Docker: Configured in infrastructure/docker/Dockerfile.api
============================================================================
"""

import logging
import time
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.exc import SQLAlchemyError

# Core application configuration and database
from .core.config import settings
from .core.database import init_db
from .core.redis_client import close_redis

# Custom middleware for security, logging, and rate limiting
from .middleware.error_handlers import (
    APIException,
    api_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from .middleware.logging_middleware import RequestLoggingMiddleware
from .middleware.rate_limiter import RateLimitMiddleware

# API route modules organized by functionality
from .routes import auth, health, metrics, tasks, predictions, models
from .routes.ml import inference as ml_inference

# Metrics and monitoring utilities
from .utils.metrics import get_business_metrics_endpoint, performance_metrics

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
# Configure structured logging for the entire application

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ============================================================================
# Create the main FastAPI application instance with metadata and configuration

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",                                    # Swagger UI endpoint
    redoc_url="/redoc",                                  # ReDoc documentation endpoint
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",  # OpenAPI schema endpoint
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================
# Configure middleware stack in execution order (first added = outermost layer)

# CORS Middleware - Enable cross-origin requests for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,                # Allowed origin domains
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,  # Allow cookies/auth headers
    allow_methods=settings.CORS_ALLOW_METHODS,          # Allowed HTTP methods
    allow_headers=settings.CORS_ALLOW_HEADERS,          # Allowed request headers
)

# Custom Application Middleware
app.add_middleware(RequestLoggingMiddleware)         # Log all requests/responses

# Rate Limiting Middleware - Prevent API abuse
if settings.RATE_LIMIT_PER_MINUTE > 0:
    app.add_middleware(RateLimitMiddleware)           # Apply rate limiting if configured

# Compression Middleware - Reduce response payload size
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# ============================================================================
# EXCEPTION HANDLER REGISTRATION
# ============================================================================
# Register custom exception handlers for consistent error responses

app.add_exception_handler(APIException, api_exception_handler)           # Custom API exceptions
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # Pydantic validation errors
app.add_exception_handler(SQLAlchemyError, database_exception_handler)   # Database operation errors
app.add_exception_handler(Exception, generic_exception_handler)          # Catch-all for unexpected errors

# ============================================================================
# PROMETHEUS METRICS SETUP
# ============================================================================
# Configure application monitoring and metrics collection

if settings.PROMETHEUS_ENABLED:
    try:
        # Initialize Prometheus FastAPI instrumentator with custom configuration
        instrumentator = Instrumentator(
            should_group_status_codes=False,              # Keep individual status codes for detailed metrics
            should_ignore_untemplated=True,               # Ignore requests to non-templated routes
            should_respect_env_var=True,                  # Respect PROMETHEUS_* environment variables
            should_instrument_requests_inprogress=True,   # Track in-progress requests
            excluded_handlers=[".*admin.*", "/metrics"],  # Exclude admin and metrics endpoints
        )

        # Apply instrumentation and expose metrics endpoint
        instrumentator.instrument(app).expose(app)
        logger.info("Prometheus instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to setup Prometheus instrumentation: {e}")
        logger.info("Continuing without Prometheus metrics")

# ============================================================================
# ROUTER REGISTRATION
# ============================================================================
# Register API route modules with appropriate prefixes

# Health check endpoint (no prefix for direct access)
app.include_router(health.router)

# API v1 endpoints with versioned prefix
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)          # User authentication
app.include_router(predictions.router, prefix=settings.API_V1_PREFIX)   # ML predictions
app.include_router(models.router, prefix=settings.API_V1_PREFIX)        # Model management
app.include_router(ml_inference.router, prefix=settings.API_V1_PREFIX)  # ML inference service
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)         # Background tasks
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX)       # System metrics


# ============================================================================
# CUSTOM ENDPOINTS
# ============================================================================

@app.get("/business-metrics")
async def business_metrics() -> Dict[str, Any]:
    """
    Custom business metrics endpoint for Prometheus scraping.
    
    Provides aquaculture-specific metrics like prediction counts,
    model performance, and business KPIs.
    """
    return get_business_metrics_endpoint()


# ============================================================================
# CUSTOM MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def add_process_time_header(request, call_next):
    """
    Middleware to track and add request processing time to response headers.
    
    Adds X-Process-Time header with the total request processing duration
    in seconds. Useful for performance monitoring and debugging.
    """
    start_time = time.time()
    request.state.start_time = start_time
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ============================================================================
# APPLICATION LIFECYCLE EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Initialize services and resources on application startup.
    
    Performs essential setup including database initialization,
    connection pool creation, and service health verification.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database connection and create tables if needed
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Continue startup even if database initialization fails
        # Health checks will catch this issue

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup resources and connections on application shutdown.
    
    Ensures graceful shutdown by closing database connections,
    Redis connections, and other resources.
    """
    logger.info("Shutting down application")

    # Close Redis connection pool
    await close_redis()

    logger.info("Application shutdown complete")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root API endpoint providing basic application information.
    
    Returns:
        Dictionary containing application metadata and navigation links
    """
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
