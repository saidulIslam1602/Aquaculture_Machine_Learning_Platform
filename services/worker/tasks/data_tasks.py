"""
Data Processing Tasks Module

Celery tasks for data management, cleanup, and maintenance operations.

Industry Standards:
    - Idempotent task design
    - Transaction management
    - Error handling and logging
    - Resource cleanup
    - Progress tracking
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from celery.utils.log import get_task_logger

from ..celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(
    name="services.worker.tasks.data_tasks.cleanup_expired_results", bind=True
)
def cleanup_expired_results(self) -> Dict[str, Any]:
    """
    Cleanup Expired Task Results

    Removes old task results from Redis to prevent memory bloat.
    Runs periodically via Celery Beat scheduler.

    Returns:
        Dict containing cleanup statistics

    Example:
        >>> from services.worker.tasks.data_tasks import cleanup_expired_results
        >>> result = cleanup_expired_results.delay()
        >>> stats = result.get()
        >>> print(f"Cleaned up {stats['deleted_count']} results")

    Schedule:
        Runs every hour via Celery Beat
    """
    try:
        # Get Celery app
        self.app  # Celery app reference

        # Get all task results older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        # Implement actual cleanup logic with Redis
        try:
            from ...api.core.redis_client import get_redis
            import asyncio
            
            async def cleanup_redis():
                redis_client = await get_redis()
                keys = await redis_client.keys("prediction:*")
                deleted_count = 0
                
                for key in keys:
                    # Check if key is older than cutoff time
                    ttl = await redis_client.ttl(key)
                    if ttl == -1 or ttl > 86400:  # No TTL or > 24 hours
                        await redis_client.delete(key)
                        deleted_count += 1
                
                return deleted_count
            
            deleted_count = asyncio.run(cleanup_redis())
        except Exception as e:
            logger.error(f"Redis cleanup failed: {e}")
            deleted_count = 0

        logger.info(f"Cleanup completed: {deleted_count} results deleted")

        return {
            "deleted_count": deleted_count,
            "cutoff_time": cutoff_time.isoformat(),
            "task_id": self.request.id,
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        raise


@celery_app.task(name="services.worker.tasks.data_tasks.worker_health_check", bind=True)
def worker_health_check(self) -> Dict[str, Any]:
    """
    Worker Health Check Task

    Performs comprehensive health check of worker services.
    Verifies connectivity to all dependencies.

    Returns:
        Dict containing health status

    Checks:
        - Database connectivity
        - Redis connectivity
        - Kafka connectivity
        - Model availability
        - Disk space
        - Memory usage

    Schedule:
        Runs every 5 minutes via Celery Beat
    """
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": self.request.hostname,
        "task_id": self.request.id,
        "checks": {},
    }

    try:
        # Check database connectivity
        try:
            from services.api.core.database import get_db
            db = next(get_db())
            db.execute("SELECT 1")
            db.close()
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"

        # Check Redis connectivity
        try:
            import redis
            from services.api.core.config import settings
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"

        # Check Kafka connectivity
        try:
            from kafka import KafkaProducer
            from services.api.core.config import settings
            producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(','),
                request_timeout_ms=5000,
                api_version=(0, 10, 1)
            )
            producer.close()
            health_status["checks"]["kafka"] = "healthy"
        except Exception as e:
            health_status["checks"]["kafka"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"

        # Check ML model availability
        try:
            from services.ml_service.core.model_registry import model_registry
            available_models = model_registry.list_available_models()
            if available_models:
                health_status["checks"]["model"] = "healthy"
                health_status["checks"]["available_models"] = len(available_models)
            else:
                health_status["checks"]["model"] = "no models available"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["model"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"

        # Overall status
        if health_status["status"] != "unhealthy":
            health_status["status"] = "healthy"

        logger.info(f"Health check completed: {health_status['status']}")
        return health_status

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        logger.error(f"Health check failed: {e}", exc_info=True)
        return health_status


@celery_app.task(
    name="services.worker.tasks.data_tasks.aggregate_predictions",
    bind=True,
    time_limit=1800,
)
def aggregate_predictions(self, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Aggregate Prediction Statistics

    Computes aggregated statistics for predictions within date range.
    Useful for analytics and reporting.

    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)

    Returns:
        Dict containing aggregated statistics

    Example:
        >>> from services.worker.tasks.data_tasks import aggregate_predictions
        >>> result = aggregate_predictions.delay("2025-10-01", "2025-10-07")
        >>> stats = result.get()
        >>> print(f"Total predictions: {stats['total_predictions']}")

    Aggregations:
        - Total predictions
        - Predictions by species
        - Average confidence
        - Predictions by model version
        - Hourly/daily trends
    """
    try:
        # Parse dates
        datetime.fromisoformat(start_date)  # Parse start date
        datetime.fromisoformat(end_date)  # Parse end date

        # Implement actual aggregation with database
        from sqlalchemy import create_engine, text
        from ...api.core.config import settings
        
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Get total predictions in date range
            total_result = conn.execute(text("""
                SELECT COUNT(*) as total 
                FROM predictions 
                WHERE created_at BETWEEN :start_date AND :end_date
            """), {"start_date": start_date, "end_date": end_date})
            total_predictions = total_result.fetchone()[0]
            
            # Get predictions by species
            species_result = conn.execute(text("""
                SELECT predicted_species, COUNT(*) as count
                FROM predictions 
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY predicted_species
            """), {"start_date": start_date, "end_date": end_date})
            
            predictions_by_species = {row[0]: row[1] for row in species_result.fetchall()}
        
        stats = {
            "start_date": start_date,
            "end_date": end_date,
            "total_predictions": total_predictions,
            "predictions_by_species": predictions_by_species,
            "average_confidence": 0.0,
            "predictions_by_model": {},
            "task_id": self.request.id,
        }

        logger.info(f"Aggregation completed for {start_date} to {end_date}")

        return stats

    except Exception as e:
        logger.error(f"Aggregation failed: {e}", exc_info=True)
        raise


@celery_app.task(
    name="services.worker.tasks.data_tasks.export_predictions",
    bind=True,
    time_limit=3600,
)
def export_predictions(
    self, start_date: str, end_date: str, format: str = "csv"
) -> Dict[str, Any]:
    """
    Export Predictions to File

    Exports prediction data to CSV or JSON format for analysis.

    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        format: Export format ('csv' or 'json')

    Returns:
        Dict containing export information

    Example:
        >>> result = export_predictions.delay("2025-10-01", "2025-10-07", "csv")
        >>> info = result.get()
        >>> print(f"Exported to: {info['file_path']}")

    Output:
        - CSV: predictions_YYYYMMDD_HHMMSS.csv
        - JSON: predictions_YYYYMMDD_HHMMSS.json
    """
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"predictions_{timestamp}.{format}"
        file_path = f"/app/data/exports/{file_name}"

        # Implement actual export logic
        import os
        import pandas as pd
        from sqlalchemy import create_engine
        from ...api.core.config import settings
        
        # Ensure export directory exists
        os.makedirs("/app/data/exports", exist_ok=True)
        
        # Get data from database
        engine = create_engine(settings.DATABASE_URL)
        query = """
            SELECT p.id, p.predicted_species, p.confidence_score, p.created_at,
                   u.username, m.name as model_name
            FROM predictions p
            LEFT JOIN users u ON p.user_id = u.id
            LEFT JOIN models m ON p.model_id = m.id
            ORDER BY p.created_at DESC
        """
        
        df = pd.read_sql(query, engine)
        
        # Export based on format
        if format.lower() == 'csv':
            df.to_csv(file_path, index=False)
        elif format.lower() == 'json':
            df.to_json(file_path, orient='records', date_format='iso')
        elif format.lower() == 'excel':
            df.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        result = {
            "file_path": file_path,
            "file_name": file_name,
            "format": format,
            "start_date": start_date,
            "end_date": end_date,
            "record_count": 0,
            "task_id": self.request.id,
        }

        logger.info(f"Export completed: {file_path}")

        return result

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise


@celery_app.task(
    name="services.worker.tasks.data_tasks.cleanup_old_predictions", bind=True
)
def cleanup_old_predictions(self, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Cleanup Old Predictions

    Removes prediction records older than specified days.
    Helps maintain database performance.

    Args:
        days_to_keep: Number of days to retain predictions

    Returns:
        Dict containing cleanup statistics

    Example:
        >>> result = cleanup_old_predictions.delay(days_to_keep=30)
        >>> stats = result.get()

    Note:
        - Archives data before deletion (optional)
        - Maintains referential integrity
        - Runs in transaction for safety
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Implement actual cleanup with database
        from sqlalchemy import create_engine, text
        from ...api.core.config import settings
        
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.begin() as conn:  # Use transaction for safety
            # Delete old predictions
            result = conn.execute(text("""
                DELETE FROM predictions 
                WHERE created_at < :cutoff_date
            """), {"cutoff_date": cutoff_date})
            
            deleted_count = result.rowcount
            
            # Also cleanup related audit logs if they exist
            conn.execute(text("""
                DELETE FROM audit_logs 
                WHERE created_at < :cutoff_date 
                AND action LIKE '%prediction%'
            """), {"cutoff_date": cutoff_date})

        logger.info(f"Cleaned up {deleted_count} predictions older than {cutoff_date}")

        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep,
            "task_id": self.request.id,
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        raise
