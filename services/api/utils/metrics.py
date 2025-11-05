"""
API Metrics Tracking Utilities

This module provides decorators and utilities for tracking API performance metrics
including request latency, throughput, error rates, and custom business metrics.

Industry Standards:
    - Prometheus-compatible metrics
    - Non-blocking metric collection
    - Proper error handling
    - Performance optimization
    - Thread-safe operations
"""

import time
import functools
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import logging
from prometheus_client import Counter, Histogram, Gauge, Summary

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'api_active_connections',
    'Number of active API connections'
)

ERROR_COUNT = Counter(
    'api_errors_total',
    'Total number of API errors',
    ['error_type', 'endpoint']
)

# Agricultural IoT specific metrics
TELEMETRY_INGESTION_RATE = Counter(
    'telemetry_data_ingested_total',
    'Total telemetry data points ingested',
    ['entity_type', 'sensor_type']
)

HEALTH_ALERTS_GENERATED = Counter(
    'health_alerts_generated_total',
    'Total health alerts generated',
    ['severity', 'alert_type']
)

FENCE_VIOLATIONS = Counter(
    'fence_violations_total',
    'Total fence violations detected',
    ['violation_type', 'severity']
)

DATA_QUALITY_SCORE = Gauge(
    'data_quality_score',
    'Current data quality score',
    ['entity_id', 'sensor_type']
)

ANIMAL_COUNT = Gauge(
    'active_animals_total',
    'Total number of active animals being monitored',
    ['farm_id', 'species']
)


def track_api_metrics(func: Callable) -> Callable:
    """
    Decorator to track API endpoint metrics.
    
    Tracks request count, duration, and error rates for API endpoints.
    
    Args:
        func: FastAPI route function to track
        
    Returns:
        Wrapped function with metrics tracking
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = "unknown"
        endpoint = func.__name__
        status_code = 200
        
        try:
            # Extract request information if available
            if 'request' in kwargs:
                request = kwargs['request']
                method = request.method
                endpoint = request.url.path
            
            # Increment active connections
            ACTIVE_CONNECTIONS.inc()
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            return result
            
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            ERROR_COUNT.labels(
                error_type=type(e).__name__,
                endpoint=endpoint
            ).inc()
            raise
            
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            ACTIVE_CONNECTIONS.dec()
    
    return wrapper


def track_telemetry_ingestion(
    entity_type: str,
    sensor_type: str,
    data_points: int = 1
) -> None:
    """
    Track telemetry data ingestion metrics.
    
    Args:
        entity_type: Type of entity (livestock, aquaculture, etc.)
        sensor_type: Type of sensor (collar, tank_sensor, etc.)
        data_points: Number of data points ingested
    """
    try:
        TELEMETRY_INGESTION_RATE.labels(
            entity_type=entity_type,
            sensor_type=sensor_type
        ).inc(data_points)
    except Exception as e:
        logger.error(f"Failed to track telemetry ingestion: {e}")


def track_health_alert(severity: str, alert_type: str) -> None:
    """
    Track health alert generation.
    
    Args:
        severity: Alert severity (low, medium, high, critical)
        alert_type: Type of alert (health_anomaly, behavior_change, etc.)
    """
    try:
        HEALTH_ALERTS_GENERATED.labels(
            severity=severity,
            alert_type=alert_type
        ).inc()
    except Exception as e:
        logger.error(f"Failed to track health alert: {e}")


def track_fence_violation(violation_type: str, severity: str) -> None:
    """
    Track fence violation events.
    
    Args:
        violation_type: Type of violation (entry, exit, breach)
        severity: Violation severity (low, medium, high, critical)
    """
    try:
        FENCE_VIOLATIONS.labels(
            violation_type=violation_type,
            severity=severity
        ).inc()
    except Exception as e:
        logger.error(f"Failed to track fence violation: {e}")


def update_data_quality_score(
    entity_id: str,
    sensor_type: str,
    quality_score: float
) -> None:
    """
    Update data quality score metric.
    
    Args:
        entity_id: Entity identifier
        sensor_type: Type of sensor
        quality_score: Quality score (0.0 to 1.0)
    """
    try:
        DATA_QUALITY_SCORE.labels(
            entity_id=entity_id,
            sensor_type=sensor_type
        ).set(quality_score)
    except Exception as e:
        logger.error(f"Failed to update data quality score: {e}")


def update_animal_count(farm_id: str, species: str, count: int) -> None:
    """
    Update active animal count metric.
    
    Args:
        farm_id: Farm identifier
        species: Animal species
        count: Number of active animals
    """
    try:
        ANIMAL_COUNT.labels(
            farm_id=farm_id,
            species=species
        ).set(count)
    except Exception as e:
        logger.error(f"Failed to update animal count: {e}")


class MetricsCollector:
    """
    Centralized metrics collection and reporting.
    
    Provides methods for collecting and aggregating various
    platform metrics for monitoring and alerting.
    """
    
    def __init__(self):
        self.custom_metrics: Dict[str, Any] = {}
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """
        Collect system-level metrics.
        
        Returns:
            Dict with system metrics
        """
        try:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "active_connections": ACTIVE_CONNECTIONS._value._value,
                "total_requests": sum(
                    sample.value for sample in REQUEST_COUNT.collect()[0].samples
                ),
                "total_errors": sum(
                    sample.value for sample in ERROR_COUNT.collect()[0].samples
                ),
                "telemetry_ingestion_rate": sum(
                    sample.value for sample in TELEMETRY_INGESTION_RATE.collect()[0].samples
                ),
                "health_alerts_generated": sum(
                    sample.value for sample in HEALTH_ALERTS_GENERATED.collect()[0].samples
                ),
                "fence_violations": sum(
                    sample.value for sample in FENCE_VIOLATIONS.collect()[0].samples
                )
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {"error": str(e)}
    
    def collect_performance_metrics(self) -> Dict[str, Any]:
        """
        Collect performance metrics.
        
        Returns:
            Dict with performance metrics
        """
        try:
            # Get request duration histogram data
            duration_samples = REQUEST_DURATION.collect()[0].samples
            
            # Calculate percentiles (simplified)
            durations = [sample.value for sample in duration_samples if sample.name.endswith('_sum')]
            counts = [sample.value for sample in duration_samples if sample.name.endswith('_count')]
            
            avg_duration = sum(durations) / sum(counts) if sum(counts) > 0 else 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "average_response_time_seconds": avg_duration,
                "total_request_duration_seconds": sum(durations),
                "total_requests_processed": sum(counts),
                "requests_per_second": sum(counts) / 3600 if sum(counts) > 0 else 0  # Approximate
            }
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
            return {"error": str(e)}
    
    def collect_business_metrics(self) -> Dict[str, Any]:
        """
        Collect business-specific metrics.
        
        Returns:
            Dict with business metrics
        """
        try:
            # Get animal count data
            animal_samples = ANIMAL_COUNT.collect()[0].samples
            total_animals = sum(sample.value for sample in animal_samples)
            
            # Get data quality scores
            quality_samples = DATA_QUALITY_SCORE.collect()[0].samples
            avg_quality = (
                sum(sample.value for sample in quality_samples) / len(quality_samples)
                if quality_samples else 0
            )
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_active_animals": total_animals,
                "average_data_quality_score": avg_quality,
                "farms_monitored": len(set(
                    sample.labels.get('farm_id', '') 
                    for sample in animal_samples
                )),
                "species_monitored": len(set(
                    sample.labels.get('species', '') 
                    for sample in animal_samples
                ))
            }
        except Exception as e:
            logger.error(f"Failed to collect business metrics: {e}")
            return {"error": str(e)}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.
        
        Returns:
            Dict with all metrics categories
        """
        return {
            "system": self.collect_system_metrics(),
            "performance": self.collect_performance_metrics(),
            "business": self.collect_business_metrics(),
            "custom": self.custom_metrics.copy()
        }
    
    def add_custom_metric(self, name: str, value: Any, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Add a custom metric.
        
        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels for the metric
        """
        try:
            metric_key = f"{name}_{datetime.utcnow().timestamp()}"
            self.custom_metrics[metric_key] = {
                "name": name,
                "value": value,
                "labels": labels or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Keep only recent custom metrics (last 1000)
            if len(self.custom_metrics) > 1000:
                oldest_keys = sorted(self.custom_metrics.keys())[:100]
                for key in oldest_keys:
                    del self.custom_metrics[key]
                    
        except Exception as e:
            logger.error(f"Failed to add custom metric: {e}")


# Global metrics collector instance
metrics_collector = MetricsCollector()