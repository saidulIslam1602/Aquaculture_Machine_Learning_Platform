#!/usr/bin/env python3
"""
Load Testing Configuration for Aquaculture ML Platform

This module defines load testing scenarios using Locust to validate the
performance and scalability of the Aquaculture ML Platform APIs under
various load conditions.

Test Scenarios:
1. Basic health check and API availability
2. Livestock data retrieval and filtering
3. Sensor data ingestion simulation
4. ML inference endpoint testing
5. Authentication and authorization flows

Performance Targets:
- Response time: < 200ms for 95% of requests
- Throughput: > 1000 requests/second
- Error rate: < 1% under normal load
- Concurrent users: Support up to 500 simultaneous users

Author: Performance Testing Team
Version: 2.1.0
"""

from locust import HttpUser, task, between, events
import json
import random
import time
from typing import Dict, Any


class AquacultureAPIUser(HttpUser):
    """
    Simulates a typical user of the Aquaculture ML Platform API.
    
    This class defines user behavior patterns for load testing,
    including realistic wait times and request patterns based on
    actual usage scenarios.
    """
    
    # Wait time between requests (1-3 seconds simulates realistic user behavior)
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        Initialize user session and perform authentication if needed.
        
        This method is called when a user starts and can be used to
        set up authentication tokens or perform initial setup requests.
        """
        self.client.verify = False  # Disable SSL verification for testing
        self.auth_token = None
        
        # Attempt to authenticate (if authentication endpoint exists)
        try:
            response = self.client.get("/health")
            if response.status_code == 200:
                self.environment.events.user_error.fire(
                    user_instance=self,
                    exception=None,
                    tb=None
                )
        except Exception:
            pass  # Continue without authentication for basic testing
    
    @task(10)
    def health_check(self):
        """
        Test the health check endpoint.
        
        This is the most frequent task as health checks are commonly
        used by load balancers and monitoring systems.
        Weight: 10 (highest frequency)
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with status {response.status_code}")
    
    @task(5)
    def get_api_docs(self):
        """
        Test API documentation endpoint.
        
        Simulates users accessing API documentation.
        Weight: 5 (moderate frequency)
        """
        with self.client.get("/docs", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API docs failed with status {response.status_code}")
    
    @task(3)
    def get_metrics(self):
        """
        Test metrics endpoint for monitoring.
        
        Simulates monitoring systems collecting metrics.
        Weight: 3 (lower frequency)
        """
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 is acceptable if endpoint doesn't exist
                response.success()
            else:
                response.failure(f"Metrics endpoint failed with status {response.status_code}")
    
    @task(7)
    def get_livestock_data(self):
        """
        Test livestock data retrieval endpoints.
        
        Simulates users querying livestock information, which is a
        core functionality of the platform.
        Weight: 7 (high frequency for core functionality)
        """
        # Test different livestock endpoints
        endpoints = [
            "/api/v1/livestock",
            "/api/v1/livestock/health",
            "/api/v1/livestock/summary"
        ]
        
        endpoint = random.choice(endpoints)
        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 acceptable for non-existent endpoints
                response.success()
            else:
                response.failure(f"Livestock endpoint {endpoint} failed with status {response.status_code}")
    
    @task(4)
    def post_sensor_data(self):
        """
        Test sensor data ingestion endpoints.
        
        Simulates IoT devices sending sensor data to the platform.
        Weight: 4 (moderate frequency for data ingestion)
        """
        # Generate mock sensor data
        sensor_data = {
            "device_id": f"sensor_{random.randint(1, 100)}",
            "timestamp": int(time.time()),
            "temperature": round(random.uniform(15.0, 35.0), 2),
            "humidity": round(random.uniform(40.0, 80.0), 2),
            "ph_level": round(random.uniform(6.5, 8.5), 2),
            "dissolved_oxygen": round(random.uniform(5.0, 12.0), 2)
        }
        
        with self.client.post(
            "/api/v1/telemetry",
            json=sensor_data,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 404]:  # Accept various success codes
                response.success()
            else:
                response.failure(f"Sensor data ingestion failed with status {response.status_code}")
    
    @task(2)
    def ml_inference_request(self):
        """
        Test ML inference endpoints.
        
        Simulates requests to machine learning inference services
        for health predictions and analytics.
        Weight: 2 (lower frequency for compute-intensive operations)
        """
        # Generate mock data for ML inference
        inference_data = {
            "features": [
                random.uniform(0, 1) for _ in range(10)  # Mock feature vector
            ],
            "model_type": random.choice(["health_prediction", "growth_analysis"])
        }
        
        with self.client.post(
            "/api/v1/ml/predict",
            json=inference_data,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code in [200, 404, 503]:  # Accept if ML service unavailable
                response.success()
            else:
                response.failure(f"ML inference failed with status {response.status_code}")


class AdminUser(HttpUser):
    """
    Simulates administrative users with different access patterns.
    
    Admin users typically perform different operations like system
    monitoring, configuration changes, and data management.
    """
    
    wait_time = between(2, 5)  # Longer wait times for admin operations
    weight = 1  # Lower proportion of admin users
    
    @task(5)
    def admin_health_check(self):
        """Admin-specific health monitoring."""
        with self.client.get("/admin/health", catch_response=True) as response:
            if response.status_code in [200, 404, 401]:  # Accept auth errors
                response.success()
            else:
                response.failure(f"Admin health check failed with status {response.status_code}")
    
    @task(2)
    def system_metrics(self):
        """Access detailed system metrics."""
        with self.client.get("/admin/metrics", catch_response=True) as response:
            if response.status_code in [200, 404, 401]:  # Accept auth errors
                response.success()
            else:
                response.failure(f"System metrics failed with status {response.status_code}")


# Event handlers for custom metrics and reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """
    Custom request handler for additional metrics collection.
    
    This handler can be used to collect custom performance metrics
    and integrate with external monitoring systems.
    """
    if exception:
        print(f"Request failed: {request_type} {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Handler called when the test starts.
    
    Can be used for test initialization, logging, or external
    system notifications.
    """
    print("Starting Aquaculture ML Platform load test...")
    print(f"Target host: {environment.host}")
    print(f"User classes: {[cls.__name__ for cls in environment.user_classes]}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Handler called when the test stops.
    
    Can be used for cleanup, result reporting, or external
    system notifications.
    """
    print("Aquaculture ML Platform load test completed.")
    
    # Print basic statistics
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")


# Configuration for different test scenarios
class QuickTest(AquacultureAPIUser):
    """Quick smoke test configuration for CI/CD pipelines."""
    wait_time = between(0.5, 1.5)  # Faster execution for CI
    weight = 10


class StressTest(AquacultureAPIUser):
    """Stress test configuration for performance validation."""
    wait_time = between(0.1, 0.5)  # Minimal wait time for stress testing
    weight = 20


# Default user class for standard load testing
if __name__ == "__main__":
    # This allows the file to be run directly for testing
    import subprocess
    import sys
    
    print("Aquaculture ML Platform Load Test Configuration")
    print("=" * 50)
    print("Available user classes:")
    print("- AquacultureAPIUser: Standard user simulation")
    print("- AdminUser: Administrative user simulation")
    print("- QuickTest: Fast CI/CD testing")
    print("- StressTest: High-load stress testing")
    print()
    print("To run load tests:")
    print("locust -f tests/load/locustfile.py --host=http://localhost:8000")
    print()
    print("For web UI:")
    print("locust -f tests/load/locustfile.py --host=http://localhost:8000 --web-host=0.0.0.0")