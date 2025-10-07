"""Health check routes"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..core.database import get_db
from ..core.redis_client import get_redis
from ..core.config import settings

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
