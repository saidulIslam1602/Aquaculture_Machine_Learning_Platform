#!/usr/bin/env python3
"""
API Testing Script - Test all backend endpoints

This script tests the complete Aquaculture ML Platform API functionality:
- Health checks
- User authentication 
- Fish species classification
- Model information
- Prediction history
"""

import requests
import json
import time
import os
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"
API_V1_URL = f"{API_BASE_URL}/api/v1"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_health_check(self):
        """Test basic health endpoint"""
        try:
            response = self.session.get(f"{API_BASE_URL}/health")
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Service: {data.get('service', 'Unknown')}"
        except Exception as e:
            success = False
            details = f"Error: {str(e)}"
        
        self.log_test("Health Check", success, details)
        return success
    
    def test_login(self, username: str = "demo", password: str = "demo12345"):
        """Test user login"""
        try:
            login_data = {
                "username": username,
                "password": password
            }
            
            response = self.session.post(
                f"{API_V1_URL}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            success = response.status_code == 200
            if success:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                details = f"Token received: {self.access_token[:20]}..."
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
        
        except Exception as e:
            success = False
            details = f"Error: {str(e)}"
        
        self.log_test("User Login", success, details)
        return success
    
    def test_user_info(self):
        """Test getting current user info"""
        try:
            response = self.session.get(f"{API_V1_URL}/auth/me")
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                details = f"User: {user_data.get('username')} ({user_data.get('email')})"
            else:
                details = f"Status: {response.status_code}"
        
        except Exception as e:
            success = False
            details = f"Error: {str(e)}"
        
        self.log_test("Get User Info", success, details)
        return success
    
    def test_model_info(self):
        """Test getting active model information"""
        try:
            response = self.session.get(f"{API_V1_URL}/models/active")
            success = response.status_code == 200
            
            if success:
                model_data = response.json()
                details = f"Model: {model_data.get('name')} v{model_data.get('version')}"
            else:
                details = f"Status: {response.status_code}"
        
        except Exception as e:
            success = False
            details = f"Error: {str(e)}"
        
        self.log_test("Get Model Info", success, details)
        return success
    
    def test_fish_species(self):
        """Test getting fish species list"""
        try:
            response = self.session.get(f"{API_V1_URL}/predictions/species")
            success = response.status_code == 200
            
            if success:
                species_data = response.json()
                details = f"Found {len(species_data)} species"
            else:
                details = f"Status: {response.status_code}"
        
        except Exception as e:
            success = False
            details = f"Error: {str(e)}"
        
        self.log_test("Get Fish Species", success, details)
        return success
    
    def test_prediction_history(self):
        """Test getting prediction history"""
        try:
            response = self.session.get(f"{API_V1_URL}/predictions/history")
            success = response.status_code == 200
            
            if success:
                history_data = response.json()
                details = f"Found {len(history_data)} predictions"
            else:
                details = f"Status: {response.status_code}"
        
        except Exception as e:
            success = False
            details = f"Error: {str(e)}"
        
        self.log_test("Get Prediction History", success, details)
        return success
    
    def test_model_health(self):
        """Test ML model health check"""
        try:
            response = self.session.get(f"{API_V1_URL}/models/health")
            success = response.status_code == 200
            
            if success:
                health_data = response.json()
                model_ready = health_data.get("ready_for_predictions", False)
                details = f"Status: {health_data.get('status')}, Ready: {model_ready}"
            else:
                details = f"Status: {response.status_code}"
        
        except Exception as e:
            success = False
            details = f"Error: {str(e)}"
        
        self.log_test("Model Health Check", success, details)
        return success
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Aquaculture ML Platform - API Test Suite")
        print("=" * 50)
        
        # Test without authentication
        print("\n📡 Basic API Tests:")
        self.test_health_check()
        
        # Test authentication
        print("\n🔐 Authentication Tests:")
        login_success = self.test_login()
        
        if login_success:
            print("\n👤 User Management Tests:")
            self.test_user_info()
            
            print("\n🤖 ML Model Tests:")
            self.test_model_info()
            self.test_model_health()
            
            print("\n🐟 Fish Classification Tests:")
            self.test_fish_species()
            self.test_prediction_history()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests:  {total_tests}")
        print(f"✅ Passed:    {passed_tests}")
        print(f"❌ Failed:    {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! The API is working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Check the details above.")
            
        success_rate = (passed_tests / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        return failed_tests == 0


def main():
    # Wait for API to be ready
    print("⏳ Waiting for API to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                break
        except:
            pass
        
        if i < max_retries - 1:
            time.sleep(2)
    else:
        print("❌ API not responding. Please check if the service is running.")
        return False
    
    # Run tests
    tester = APITester()
    return tester.run_all_tests()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)