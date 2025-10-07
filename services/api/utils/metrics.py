"""
Performance Metrics Module

Tracks and calculates actual performance metrics for the application.

Industry Standards:
    - Prometheus metrics integration
    - Percentile calculations (p50, p95, p99)
    - Sliding window for recent metrics
    - Thread-safe operations
    - Memory-efficient storage
"""

from typing import List, Dict, Any
from collections import deque
from threading import Lock
import time
import statistics


class PerformanceMetrics:
    """
    Performance Metrics Tracker

    Tracks request latencies, throughput, and error rates with
    sliding window for real-time metrics.

    Features:
        - Percentile calculations (p50, p95, p99)
        - Throughput tracking (requests/second)
        - Error rate monitoring
        - Memory-efficient circular buffer
        - Thread-safe operations

    Example:
        >>> metrics = PerformanceMetrics()
        >>> metrics.record_request(45.2, success=True)
        >>> stats = metrics.get_stats()
        >>> print(f"p95 latency: {stats['latency_p95_ms']}ms")
    """

    def __init__(self, window_size: int = 10000):
        """
        Initialize Performance Metrics

        Args:
            window_size: Number of recent requests to track
        """
        self.window_size = window_size

        # Circular buffers for metrics (memory-efficient)
        self.latencies: deque = deque(maxlen=window_size)
        self.timestamps: deque = deque(maxlen=window_size)
        self.successes: deque = deque(maxlen=window_size)

        # Counters
        self.total_requests = 0
        self.total_errors = 0
        self.start_time = time.time()

        # Thread safety
        self.lock = Lock()

    def record_request(self, latency_ms: float, success: bool = True) -> None:
        """
        Record Request Metrics

        Records latency and success status for a request.

        Args:
            latency_ms: Request latency in milliseconds
            success: Whether request succeeded

        Note:
            Uses circular buffer - automatically drops old entries
            when window size is exceeded.
        """
        with self.lock:
            self.latencies.append(latency_ms)
            self.timestamps.append(time.time())
            self.successes.append(success)

            self.total_requests += 1
            if not success:
                self.total_errors += 1

    def get_percentile(self, data: List[float], percentile: float) -> float:
        """
        Calculate Percentile

        Calculates specified percentile from data.

        Args:
            data: List of values
            percentile: Percentile to calculate (0-100)

        Returns:
            float: Percentile value

        Algorithm:
            Uses linear interpolation between closest ranks
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * (percentile / 100)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get Performance Statistics

        Calculates comprehensive performance metrics.

        Returns:
            Dict containing:
                - latency_mean_ms: Average latency
                - latency_p50_ms: Median latency
                - latency_p95_ms: 95th percentile latency
                - latency_p99_ms: 99th percentile latency
                - throughput_rps: Requests per second
                - error_rate: Percentage of failed requests
                - total_requests: Total requests processed
                - window_size: Current window size

        Example:
            >>> stats = metrics.get_stats()
            >>> print(f"p95: {stats['latency_p95_ms']:.2f}ms")
            >>> print(f"Throughput: {stats['throughput_rps']:.2f} req/s")
        """
        with self.lock:
            if not self.latencies:
                return {
                    "latency_mean_ms": 0.0,
                    "latency_p50_ms": 0.0,
                    "latency_p95_ms": 0.0,
                    "latency_p99_ms": 0.0,
                    "throughput_rps": 0.0,
                    "error_rate": 0.0,
                    "total_requests": 0,
                    "window_size": 0,
                }

            latencies_list = list(self.latencies)

            # Calculate latency percentiles
            latency_mean = statistics.mean(latencies_list)
            latency_p50 = self.get_percentile(latencies_list, 50)
            latency_p95 = self.get_percentile(latencies_list, 95)
            latency_p99 = self.get_percentile(latencies_list, 99)

            # Calculate throughput (requests per second)
            # Use recent window for accurate current throughput
            if len(self.timestamps) > 1:
                time_window = self.timestamps[-1] - self.timestamps[0]
                if time_window > 0:
                    throughput = len(self.timestamps) / time_window
                else:
                    throughput = 0.0
            else:
                throughput = 0.0

            # Calculate error rate
            error_count = sum(1 for s in self.successes if not s)
            error_rate = error_count / len(self.successes) if self.successes else 0.0

            return {
                "latency_mean_ms": round(latency_mean, 2),
                "latency_p50_ms": round(latency_p50, 2),
                "latency_p95_ms": round(latency_p95, 2),
                "latency_p99_ms": round(latency_p99, 2),
                "throughput_rps": round(throughput, 2),
                "error_rate": round(error_rate, 4),
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "window_size": len(self.latencies),
                "uptime_seconds": round(time.time() - self.start_time, 2),
            }

    def reset(self) -> None:
        """Reset all metrics"""
        with self.lock:
            self.latencies.clear()
            self.timestamps.clear()
            self.successes.clear()
            self.total_requests = 0
            self.total_errors = 0
            self.start_time = time.time()


# Global metrics instance
performance_metrics = PerformanceMetrics(window_size=10000)
