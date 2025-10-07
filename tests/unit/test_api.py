"""
API Unit Tests

Tests for API endpoints including authentication, health checks, and ML operations.

Industry Standards:
    - AAA pattern (Arrange, Act, Assert)
    - Descriptive test names
    - Isolated test cases
    - Comprehensive coverage
    - Mock external dependencies
"""

import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test suite for health check endpoints"""
    
    def test_health_check_returns_200(self, client):
        """
        Test: Health check endpoint returns 200 OK
        
        Verifies basic health endpoint functionality.
        """
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "healthy"
    
    def test_detailed_health_includes_dependencies(self, client):
        """
        Test: Detailed health check includes dependency status
        
        Verifies that detailed health endpoint reports on all dependencies.
        """
        # Act
        response = client.get("/health/detailed")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "checks" in data
        assert "database" in data["checks"]
    
    def test_readiness_probe(self, client):
        """
        Test: Readiness probe for Kubernetes
        
        Verifies readiness endpoint for K8s health checks.
        """
        # Act
        response = client.get("/ready")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ready"
    
    def test_liveness_probe(self, client):
        """
        Test: Liveness probe for Kubernetes
        
        Verifies liveness endpoint for K8s health checks.
        """
        # Act
        response = client.get("/live")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "alive"


class TestAuthenticationEndpoints:
    """Test suite for authentication endpoints"""
    
    def test_register_user_success(self, client, sample_user_data):
        """
        Test: User registration with valid data
        
        Verifies successful user registration flow.
        """
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=sample_user_data
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned
    
    def test_register_duplicate_user_fails(self, client, sample_user_data):
        """
        Test: Duplicate user registration fails
        
        Verifies that duplicate email/username is rejected.
        """
        # Arrange - Register first user
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Act - Try to register again
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_with_valid_credentials(self, client, sample_user_data):
        """
        Test: Login with valid credentials
        
        Verifies successful login and token generation.
        """
        # Arrange - Register user
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Act - Login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": sample_user_data["username"],
                "password": sample_user_data["password"]
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_invalid_credentials_fails(self, client, sample_user_data):
        """
        Test: Login with invalid credentials fails
        
        Verifies that wrong password is rejected.
        """
        # Arrange - Register user
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Act - Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": sample_user_data["username"],
                "password": "wrongpassword"
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMLEndpoints:
    """Test suite for ML inference endpoints"""
    
    def test_predict_requires_authentication(self, client, sample_image_base64):
        """
        Test: Prediction endpoint requires authentication
        
        Verifies that unauthenticated requests are rejected.
        """
        # Act - Request without token
        response = client.post(
            "/api/v1/ml/predict",
            json={"image_base64": sample_image_base64}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_predict_with_valid_image(self, client, auth_token, sample_image_base64):
        """
        Test: Prediction with valid image
        
        Verifies successful prediction flow.
        """
        # Act
        response = client.post(
            "/api/v1/ml/predict",
            json={"image_base64": sample_image_base64},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "species" in data
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1
    
    def test_predict_with_invalid_base64_fails(self, client, auth_token):
        """
        Test: Prediction with invalid base64 fails
        
        Verifies input validation.
        """
        # Act
        response = client.post(
            "/api/v1/ml/predict",
            json={"image_base64": "invalid-base64!!!"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_list_models_requires_authentication(self, client):
        """
        Test: List models requires authentication
        
        Verifies authentication requirement.
        """
        # Act
        response = client.get("/api/v1/ml/models")
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_models_returns_available_models(self, client, auth_token):
        """
        Test: List models returns available models
        
        Verifies model listing functionality.
        """
        # Act
        response = client.get(
            "/api/v1/ml/models",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "version" in data[0]
            assert "architecture" in data[0]
