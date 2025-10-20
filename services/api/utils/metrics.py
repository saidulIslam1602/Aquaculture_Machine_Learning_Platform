"""
Advanced Metrics Collection and Monitoring

Provides comprehensive metrics collection for the Aquaculture ML Platform
including business KPIs, system performance, and custom metrics.
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from prometheus_client import Counter, Histogram, Gauge, Info, Enum
import logging

logger = logging.getLogger(__name__)

# Prometheus Metrics Definitions
# API Metrics
api_requests_total = Counter(
    "api_requests_total", "Total API requests", ["method", "endpoint", "status"]
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

api_active_connections = Gauge(
    "api_active_connections", "Number of active API connections"
)

# Business Metrics
business_fish_count = Gauge(
    "business_fish_count_total", "Total number of fish", ["tank_id", "species"]
)

business_mortality_rate = Gauge(
    "business_fish_mortality_rate", "Fish mortality rate", ["tank_id", "species"]
)

business_feed_conversion_ratio = Gauge(
    "business_feed_conversion_ratio", "Feed conversion ratio", ["tank_id"]
)

business_water_quality_score = Gauge(
    "business_water_quality_score",
    "Water quality score (0-1)",
    ["tank_id", "parameter"],
)

business_daily_production_kg = Gauge(
    "business_daily_production_kg", "Daily production in kg", ["date"]
)

business_average_growth_rate = Gauge(
    "business_average_growth_rate_grams_per_day",
    "Average fish growth rate in grams per day",
    ["tank_id", "species"],
)

business_system_uptime = Gauge(
    "business_system_uptime_percentage", "System uptime percentage"
)

business_prediction_accuracy = Gauge(
    "business_prediction_accuracy_sla",
    "ML prediction accuracy SLA compliance",
    ["model_type"],
)

# ML Model Metrics
model_predictions_total = Counter(
    "model_predictions_total",
    "Total model predictions",
    ["model_type", "model_version"],
)

model_prediction_duration = Histogram(
    "model_prediction_duration_seconds",
    "Model prediction duration",
    ["model_type"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

model_prediction_accuracy = Gauge(
    "model_prediction_accuracy",
    "Model prediction accuracy",
    ["model_type", "model_version"],
)

model_prediction_uncertainty = Gauge(
    "model_prediction_uncertainty", "Model prediction uncertainty", ["model_type"]
)

model_drift_score = Gauge(
    "model_drift_score", "Model drift detection score", ["model_type"]
)

model_training_duration = Histogram(
    "model_training_duration_seconds",
    "Model training duration",
    ["model_type"],
    buckets=[60, 300, 600, 1800, 3600, 7200],
)

model_training_failures = Counter(
    "model_training_failures_total",
    "Model training failures",
    ["model_type", "error_type"],
)

model_last_training_timestamp = Gauge(
    "model_last_training_timestamp", "Timestamp of last model training", ["model_type"]
)

# Data Quality Metrics
data_quality_score = Gauge(
    "data_quality_score", "Data quality score (0-1)", ["stage", "data_type"]
)

feature_missing_rate = Gauge(
    "feature_missing_rate", "Rate of missing features", ["feature_name"]
)

data_pipeline_last_success = Gauge(
    "data_pipeline_last_success_timestamp",
    "Timestamp of last successful data pipeline run",
)

data_last_updated = Gauge(
    "data_last_updated_timestamp",
    "Timestamp when data was last updated",
    ["data_source"],
)

# Security Metrics
security_login_attempts = Counter(
    "security_login_attempts_total", "Login attempts", ["status", "source_ip"]
)

security_api_key_usage = Counter(
    "security_api_key_usage_total", "API key usage", ["key_id", "endpoint"]
)

security_suspicious_activity = Counter(
    "security_suspicious_activity_total",
    "Suspicious security activity",
    ["activity_type", "source_ip"],
)

# Infrastructure Metrics
database_connections = Gauge(
    "database_connections_active", "Active database connections"
)

database_query_duration = Histogram(
    "database_query_duration_seconds",
    "Database query duration",
    ["query_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

cache_hit_rate = Gauge("cache_hit_rate", "Cache hit rate", ["cache_type"])

queue_size = Gauge("queue_size", "Queue size", ["queue_name"])


@dataclass
class PerformanceWindow:
    """Sliding window for performance metrics calculation"""

    max_size: int = 10000
    requests: deque = field(default_factory=deque)
    response_times: deque = field(default_factory=deque)
    errors: deque = field(default_factory=deque)
    start_time: float = field(default_factory=time.time)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add_request(self, response_time: float, is_error: bool = False):
        """Add a request to the performance window"""
        with self.lock:
            current_time = time.time()

            # Add new data
            self.requests.append(current_time)
            self.response_times.append(response_time)
            self.errors.append(is_error)

            # Remove old data if window is full
            if len(self.requests) > self.max_size:
                self.requests.popleft()
                self.response_times.popleft()
                self.errors.popleft()

    def get_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        with self.lock:
            if not self.requests:
                return self._empty_stats()

            current_time = time.time()
            response_times = list(self.response_times)
            errors = list(self.errors)

            # Calculate basic stats
            total_requests = len(response_times)
            total_errors = sum(errors)
            error_rate = (
                (total_errors / total_requests) * 100 if total_requests > 0 else 0
            )

            # Calculate latency percentiles
            sorted_times = sorted(response_times)
            mean_latency = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            def percentile(data: List[float], p: float) -> float:
                if not data:
                    return 0.0
                k = (len(data) - 1) * p
                f = int(k)
                c = k - f
                if f + 1 < len(data):
                    return data[f] * (1 - c) + data[f + 1] * c
                return data[f]

            p50 = percentile(sorted_times, 0.50)
            p95 = percentile(sorted_times, 0.95)
            p99 = percentile(sorted_times, 0.99)

            # Calculate throughput (requests per second over last 5 minutes)
            five_min_ago = current_time - 300
            recent_requests = [t for t in self.requests if t >= five_min_ago]
            throughput = len(recent_requests) / 300 if recent_requests else 0

            uptime = current_time - self.start_time

            return {
                "latency_mean_ms": round(mean_latency * 1000, 2),
                "latency_p50_ms": round(p50 * 1000, 2),
                "latency_p95_ms": round(p95 * 1000, 2),
                "latency_p99_ms": round(p99 * 1000, 2),
                "throughput_rps": round(throughput, 2),
                "error_rate": round(error_rate, 2),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "uptime_seconds": round(uptime, 2),
            }

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats when no data is available"""
        return {
            "latency_mean_ms": 0.0,
            "latency_p50_ms": 0.0,
            "latency_p95_ms": 0.0,
            "latency_p99_ms": 0.0,
            "throughput_rps": 0.0,
            "error_rate": 0.0,
            "total_requests": 0,
            "total_errors": 0,
            "uptime_seconds": 0.0,
        }

    def reset(self):
        """Reset all performance metrics"""
        with self.lock:
            self.requests.clear()
            self.response_times.clear()
            self.errors.clear()
            self.start_time = time.time()


class MetricsCollector:
    """Advanced metrics collection and management"""

    def __init__(self):
        self.performance_window = PerformanceWindow()
        self.business_metrics = defaultdict(float)
        self.system_metrics = defaultdict(float)
        self._start_background_collection()

    def record_api_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record API request metrics"""
        # Prometheus metrics
        api_requests_total.labels(
            method=method, endpoint=endpoint, status=str(status_code)
        ).inc()
        api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

        # Performance window
        is_error = status_code >= 400
        self.performance_window.add_request(duration, is_error)

    def record_model_prediction(
        self,
        model_type: str,
        model_version: str,
        duration: float,
        accuracy: Optional[float] = None,
        uncertainty: Optional[float] = None,
    ):
        """Record ML model prediction metrics"""
        model_predictions_total.labels(
            model_type=model_type, model_version=model_version
        ).inc()
        model_prediction_duration.labels(model_type=model_type).observe(duration)

        if accuracy is not None:
            model_prediction_accuracy.labels(
                model_type=model_type, model_version=model_version
            ).set(accuracy)

        if uncertainty is not None:
            model_prediction_uncertainty.labels(model_type=model_type).set(uncertainty)

    def record_business_metric(
        self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record business KPI metrics"""
        labels = labels or {}

        metric_map = {
            "fish_count": business_fish_count,
            "mortality_rate": business_mortality_rate,
            "feed_conversion_ratio": business_feed_conversion_ratio,
            "water_quality_score": business_water_quality_score,
            "daily_production_kg": business_daily_production_kg,
            "growth_rate": business_average_growth_rate,
            "system_uptime": business_system_uptime,
            "prediction_accuracy": business_prediction_accuracy,
        }

        if metric_name in metric_map:
            if labels:
                metric_map[metric_name].labels(**labels).set(value)
            else:
                metric_map[metric_name].set(value)

    def record_security_event(
        self,
        event_type: str,
        source_ip: str,
        additional_labels: Optional[Dict[str, str]] = None,
    ):
        """Record security-related events"""
        labels = additional_labels or {}

        if event_type == "login_attempt":
            status = labels.get("status", "unknown")
            security_login_attempts.labels(status=status, source_ip=source_ip).inc()
        elif event_type == "suspicious_activity":
            activity_type = labels.get("activity_type", "unknown")
            security_suspicious_activity.labels(
                activity_type=activity_type, source_ip=source_ip
            ).inc()

    def record_data_quality(self, stage: str, data_type: str, quality_score: float):
        """Record data quality metrics"""
        data_quality_score.labels(stage=stage, data_type=data_type).set(quality_score)

    def update_system_metrics(self):
        """Update system-level metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            # Database connections (mock - replace with actual DB connection count)
            database_connections.set(10)  # Replace with actual count

            # Cache hit rate (mock - replace with actual cache metrics)
            cache_hit_rate.labels(cache_type="redis").set(0.85)

            # Update timestamps
            data_pipeline_last_success.set(time.time())
            data_last_updated.labels(data_source="sensors").set(time.time())

        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return self.performance_window.get_stats()

    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_window.reset()

    def _start_background_collection(self):
        """Start background thread for periodic metrics collection"""

        def collect_metrics():
            while True:
                try:
                    self.update_system_metrics()
                    time.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    logger.error(f"Error in background metrics collection: {e}")
                    time.sleep(60)  # Wait longer on error

        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()


# Global metrics collector instance
performance_metrics = MetricsCollector()


def get_business_metrics_endpoint() -> Dict[str, Any]:
    """
    Custom endpoint for business metrics that Prometheus can scrape
    Returns business KPIs in Prometheus format
    """
    current_time = time.time()

    # Mock business data - replace with actual business logic
    business_data = {
        "fish_mortality_rate": 0.02,  # 2% mortality rate
        "feed_conversion_ratio": 1.5,
        "water_quality_score": 0.92,
        "daily_production_kg": 1250.5,
        "average_growth_rate_grams_per_day": 18.5,
        "system_uptime_percentage": 0.9995,
        "prediction_accuracy_sla": 0.94,
        "energy_efficiency_kwh_per_kg": 6.8,
        "operational_cost_usd": 2850.75,
        "customer_satisfaction_score": 4.3,
        "environmental_compliance_score": 0.98,
    }

    # Update Prometheus metrics
    for metric_name, value in business_data.items():
        performance_metrics.record_business_metric(metric_name, value)

    return {"timestamp": current_time, "metrics": business_data, "status": "success"}
