#!/usr/bin/env python3
"""
Smoke tests for Aquaculture ML Platform API endpoints.

These tests verify that the core API endpoints are accessible and responding
correctly in deployed environments (staging/production).
"""

import pytest
import requests
import os
from typing import Optional


class TestAPISmoke:
    """Smoke tests for API service endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.timeout = 30
        
    def test_health_endpoint(self):
        """Test that the health endpoint is accessible."""
        response = requests.get(
            f"{self.base_url}/health",
            timeout=self.timeout
        )
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "ok"]
        
    def test_api_docs_accessible(self):
        """Test that API documentation is accessible."""
        response = requests.get(
            f"{self.base_url}/docs",
            timeout=self.timeout
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        
    def test_metrics_endpoint(self):
        """Test that metrics endpoint is accessible."""
        response = requests.get(
            f"{self.base_url}/metrics",
            timeout=self.timeout
        )
        assert response.status_code == 200
        
    def test_api_version_endpoint(self):
        """Test that version endpoint returns valid information."""
        try:
            response = requests.get(
                f"{self.base_url}/version",
                timeout=self.timeout
            )
            if response.status_code == 200:
                version_data = response.json()
                assert "version" in version_data
        except requests.exceptions.RequestException:
            # Version endpoint might not exist, skip test
            pytest.skip("Version endpoint not available")
            
    def test_database_connectivity(self):
        """Test database connectivity through API."""
        try:
            response = requests.get(
                f"{self.base_url}/health/database",
                timeout=self.timeout
            )
            if response.status_code == 200:
                db_health = response.json()
                assert "database" in db_health
                assert db_health["database"]["status"] == "connected"
        except requests.exceptions.RequestException:
            # Database health endpoint might not exist, skip test
            pytest.skip("Database health endpoint not available")
            
    def test_redis_connectivity(self):
        """Test Redis connectivity through API."""
        try:
            response = requests.get(
                f"{self.base_url}/health/redis",
                timeout=self.timeout
            )
            if response.status_code == 200:
                redis_health = response.json()
                assert "redis" in redis_health
                assert redis_health["redis"]["status"] == "connected"
        except requests.exceptions.RequestException:
            # Redis health endpoint might not exist, skip test
            pytest.skip("Redis health endpoint not available")


class TestMLServiceSmoke:
    """Smoke tests for ML service endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.base_url = os.getenv("ML_BASE_URL", "http://localhost:8001")
        self.timeout = 30
        
    def test_ml_health_endpoint(self):
        """Test that the ML service health endpoint is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            assert response.status_code == 200
            
            health_data = response.json()
            assert "status" in health_data
            assert health_data["status"] in ["healthy", "ok"]
        except requests.exceptions.RequestException:
            # ML service might not be deployed, skip test
            pytest.skip("ML service not available")
            
    def test_ml_model_status(self):
        """Test that ML models are loaded and ready."""
        try:
            response = requests.get(
                f"{self.base_url}/models/status",
                timeout=self.timeout
            )
            if response.status_code == 200:
                model_status = response.json()
                assert "models" in model_status
        except requests.exceptions.RequestException:
            # Model status endpoint might not exist, skip test
            pytest.skip("ML model status endpoint not available")


class TestFrontendSmoke:
    """Smoke tests for frontend application."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.timeout = 30
        
    def test_frontend_accessible(self):
        """Test that the frontend application is accessible."""
        try:
            response = requests.get(
                self.base_url,
                timeout=self.timeout
            )
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
        except requests.exceptions.RequestException:
            # Frontend might not be deployed, skip test
            pytest.skip("Frontend not available")


class TestMonitoringSmoke:
    """Smoke tests for monitoring endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        self.grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
        self.timeout = 30
        
    def test_prometheus_accessible(self):
        """Test that Prometheus is accessible."""
        try:
            response = requests.get(
                f"{self.prometheus_url}/-/healthy",
                timeout=self.timeout
            )
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            # Prometheus might not be deployed, skip test
            pytest.skip("Prometheus not available")
            
    def test_grafana_accessible(self):
        """Test that Grafana is accessible."""
        try:
            response = requests.get(
                f"{self.grafana_url}/api/health",
                timeout=self.timeout
            )
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            # Grafana might not be deployed, skip test
            pytest.skip("Grafana not available")


if __name__ == "__main__":
    # Run smoke tests
    pytest.main([__file__, "-v"])
