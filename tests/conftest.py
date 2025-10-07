"""
Pytest Configuration and Fixtures

Provides shared fixtures for all test modules.

Industry Standards:
    - Fixture-based test setup
    - Database isolation per test
    - Mock external dependencies
    - Cleanup after tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.api.main import app
from services.api.core.database import Base, get_db
from services.api.core.security import create_access_token


# Test Database Configuration
# Uses in-memory SQLite for fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Database Session Fixture
    
    Provides isolated database session for each test.
    Automatically rolls back after test completion.
    
    Yields:
        Session: Test database session
        
    Note:
        Each test gets fresh database state.
        No test pollution between tests.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Test Client Fixture
    
    Provides FastAPI test client with database override.
    
    Yields:
        TestClient: FastAPI test client
        
    Example:
        def test_endpoint(client):
            response = client.get("/health")
            assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_token():
    """
    Authentication Token Fixture
    
    Provides valid JWT token for authenticated endpoints.
    
    Returns:
        str: Valid JWT access token
        
    Example:
        def test_protected_endpoint(client, auth_token):
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
    """
    token_data = {
        "sub": "test-user-id",
        "username": "testuser",
        "is_active": True
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def sample_user_data():
    """
    Sample User Data Fixture
    
    Provides sample user data for testing.
    
    Returns:
        dict: User registration data
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture(scope="function")
def sample_image_base64():
    """
    Sample Image Fixture
    
    Provides base64-encoded sample image for testing.
    
    Returns:
        str: Base64-encoded image
    """
    # 1x1 red pixel PNG
    return (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8"
        "DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    )
