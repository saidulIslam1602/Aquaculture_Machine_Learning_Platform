"""
Load Testing with Locust

Performance and load testing for API endpoints.

Industry Standards:
    - Realistic user behavior simulation
    - Gradual load increase
    - Performance metrics collection
    - Failure rate monitoring
    - Response time percentiles
    
Test Scenarios:
    - Single image prediction
    - Batch prediction
    - Authentication flow
    - Concurrent users
"""

from locust import HttpUser, task, between, events
import base64
import random
import logging

logger = logging.getLogger(__name__)


class AquacultureAPIUser(HttpUser):
    """
    Simulated API User
    
    Simulates realistic user behavior for load testing.
    
    Behavior:
        - Authenticates on start
        - Performs predictions with realistic timing
        - Varies request patterns
        
    Wait Time:
        Between 1-3 seconds between requests (realistic user behavior)
    """
    
    # Wait time between tasks (realistic user behavior)
    wait_time = between(1, 3)
    
    # Authentication token
    token = None
    
    def on_start(self):
        """
        On Start Hook
        
        Called when user starts. Performs authentication.
        """
        # Register and login
        self.register_and_login()
    
    def register_and_login(self):
        """
        Register and Login User
        
        Creates test user and obtains authentication token.
        """
        # Generate unique username
        username = f"loadtest_{random.randint(1000, 9999)}"
        
        # Register
        register_data = {
            "email": f"{username}@loadtest.com",
            "username": username,
            "password": "loadtest123",
            "full_name": "Load Test User"
        }
        
        response = self.client.post(
            "/api/v1/auth/register",
            json=register_data,
            name="/api/v1/auth/register"
        )
        
        if response.status_code != 201:
            logger.warning(f"Registration failed: {response.text}")
            return
        
        # Login
        login_data = {
            "username": username,
            "password": "loadtest123"
        }
        
        response = self.client.post(
            "/api/v1/auth/login",
            data=login_data,
            name="/api/v1/auth/login"
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            logger.info(f"User authenticated: {username}")
        else:
            logger.error(f"Login failed: {response.text}")
    
    def get_auth_headers(self):
        """Get authentication headers"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(10)
    def health_check(self):
        """
        Task: Health Check
        
        Performs health check request.
        Weight: 10 (frequently called)
        """
        self.client.get("/health", name="/health")
    
    @task(5)
    def predict_single_image(self):
        """
        Task: Single Image Prediction
        
        Performs single image prediction.
        Weight: 5 (common operation)
        """
        if not self.token:
            return
        
        # Generate sample image (1x1 red pixel)
        sample_image_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8"
            "DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        
        payload = {
            "image_base64": sample_image_b64,
            "return_probabilities": False
        }
        
        self.client.post(
            "/api/v1/ml/predict",
            json=payload,
            headers=self.get_auth_headers(),
            name="/api/v1/ml/predict"
        )
    
    @task(2)
    def predict_batch(self):
        """
        Task: Batch Prediction
        
        Performs batch prediction with multiple images.
        Weight: 2 (less frequent, resource-intensive)
        """
        if not self.token:
            return
        
        # Generate batch of sample images
        sample_image_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8"
            "DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        
        batch_size = random.randint(5, 20)
        payload = {
            "images_base64": [sample_image_b64] * batch_size,
            "batch_size": 16
        }
        
        self.client.post(
            "/api/v1/ml/predict/batch",
            json=payload,
            headers=self.get_auth_headers(),
            name="/api/v1/ml/predict/batch"
        )
    
    @task(3)
    def list_models(self):
        """
        Task: List Available Models
        
        Retrieves list of available models.
        Weight: 3 (moderate frequency)
        """
        if not self.token:
            return
        
        self.client.get(
            "/api/v1/ml/models",
            headers=self.get_auth_headers(),
            name="/api/v1/ml/models"
        )
    
    @task(1)
    def get_model_info(self):
        """
        Task: Get Model Information
        
        Retrieves detailed model information.
        Weight: 1 (infrequent)
        """
        if not self.token:
            return
        
        self.client.get(
            "/api/v1/ml/models/v1.0.0",
            headers=self.get_auth_headers(),
            name="/api/v1/ml/models/{version}"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Test Start Event Handler
    
    Called when load test starts.
    """
    logger.info("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Test Stop Event Handler
    
    Called when load test stops. Logs final statistics.
    """
    logger.info("Load test completed")
    
    # Log statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Requests per second: {stats.total.total_rps:.2f}")
