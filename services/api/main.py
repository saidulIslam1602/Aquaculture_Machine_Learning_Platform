"""Main FastAPI application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import time

from .core.config import settings
from .core.database import init_db
from .core.redis_client import close_redis
from .routes import auth, health, tasks, metrics
from .routes.ml import inference as ml_inference
from .utils.metrics import performance_metrics, get_business_metrics_endpoint
from .middleware.error_handlers import (
    api_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    APIException,
)
from .middleware.logging_middleware import RequestLoggingMiddleware
from .middleware.rate_limiter import RateLimitMiddleware
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
    # Standard FastAPI instrumentation
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=[".*admin.*", "/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="inprogress",
        inprogress_labels=True,
    )

    # Add custom metrics collection
    @instrumentator.add_middleware
    def add_custom_metrics(request, response):
        method = request.method
        endpoint = str(request.url.path)
        status_code = response.status_code

        # Record in our custom metrics collector
        if hasattr(request.state, "start_time"):
            duration = time.time() - request.state.start_time
            performance_metrics.record_api_request(
                method, endpoint, status_code, duration
            )

    instrumentator.instrument(app).expose(app)

# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(ml_inference.router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX)


# Add custom business metrics endpoint
@app.get("/business-metrics")
async def business_metrics():
    """Custom business metrics endpoint for Prometheus scraping"""
    return get_business_metrics_endpoint()


# Add middleware to track request timing
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    request.state.start_time = start_time
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
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
