"""
============================================================================
Health Check API Routes for Aquaculture ML Platform
============================================================================

This module provides comprehensive health monitoring endpoints for the
aquaculture platform API service. These endpoints are essential for:

- Container orchestration health checks (Docker, Kubernetes)
- Load balancer health verification
- Monitoring system integration (Prometheus, Grafana)
- DevOps pipeline status verification
- Production troubleshooting and diagnostics

ENDPOINTS:
- GET /health: Basic health status for simple checks
- GET /health/detailed: Comprehensive system status with dependencies

HEALTH CHECK LEVELS:
1. Basic: Service is running and responding
2. Detailed: Service + database + cache + external dependencies

USAGE:
- Docker: HEALTHCHECK instruction uses /health endpoint
- Kubernetes: liveness and readiness probes
- Load Balancers: Backend health verification
- Monitoring: Alerting based on health status

RESPONSE FORMATS:
- 200 OK: Service is healthy
- 503 Service Unavailable: Service or dependencies are unhealthy
- Consistent JSON format for programmatic consumption
============================================================================
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.redis_client import get_redis

# Create router with health-specific tags for OpenAPI documentation
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "api",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with dependency status.

    Args:
        db: Database session

    Returns:
        Detailed health status
    """
    health_status = {
        "status": "healthy",
        "service": "api",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe.

    Args:
        db: Database session

    Returns:
        Readiness status
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe.

    Returns:
        Liveness status
    """
    return {"status": "alive"}
