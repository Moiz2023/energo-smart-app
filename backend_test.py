#!/usr/bin/env python3
"""
Backend Testing for Energo Smart App - Review Request Testing
Tests specific areas mentioned in the review request:
1. Health Check: Test /api/health endpoint
2. Authentication Endpoints: Test /api/auth/register and /api/auth/login 
3. Demo User Creation: Create a demo user (demo@energo.com / password123) if it doesn't exist
4. Database Connection: Verify MongoDB connection is working
5. Environment Variables: Check that EMERGENT_LLM_KEY is properly loaded
6. API Endpoint Structure: Verify all /api/* routes are working
7. CORS Configuration: Ensure frontend can communicate with backend
"""

import requests
import json
import time
import os
import sys
from datetime import datetime

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                    base_url = line.split('=')[1].strip().strip('"')
                    return f"{base_url}/api"
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    return "https://smart-energo.preview.emergentagent.com/api"

BASE_URL = get_backend_url()
print(f"Testing backend at: {BASE_URL}")

class EnergoBackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.demo_user_email = "demo@energo.com"
        self.demo_user_password = "password123"
        self.demo_user_name = "Demo User"
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def log_result(self, test_name, success, message=""):
        self.results["total_tests"] += 1
        if success:
            self.results["passed"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED {message}")

    def test_health_check(self):
        """Test /api/health endpoint"""
        print("\n🏥 Testing Health Check Endpoint...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_result("Health Check", True, f"Backend is healthy, timestamp: {data.get('timestamp', 'N/A')}")
                    return True
                else:
                    self.log_result("Health Check", False, f"Unexpected response format: {data}")
            else:
                self.log_result("Health Check", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Health Check", False, f"Exception: {str(e)}")
            
        return False

    def test_cors_configuration(self):
        """Test CORS configuration by checking headers"""
        print("\n🌐 Testing CORS Configuration...")
        
        try:
            # Test preflight request
            response = self.session.options(
                f"{self.base_url}/health",
                headers={
                    "Origin": "https://smart-energo.preview.emergentagent.com",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                },
                timeout=30
            )
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
            }
            
            if (cors_headers["Access-Control-Allow-Origin"] in ["*", "https://smart-energo.preview.emergentagent.com"] and
                cors_headers["Access-Control-Allow-Methods"] and
                cors_headers["Access-Control-Allow-Headers"]):
                self.log_result("CORS Configuration", True, "CORS headers properly configured")
                return True
            else:
                self.log_result("CORS Configuration", False, f"CORS headers: {cors_headers}")
                
        except Exception as e:
            self.log_result("CORS Configuration", False, f"Exception: {str(e)}")
            
        return False

    def test_demo_user_creation(self):
        """Create demo user (demo@energo.com / password123) if it doesn't exist"""
        print("\n👤 Testing Demo User Creation...")
        
        # First try to login with demo user
        login_data = {
            "email": self.demo_user_email,
            "password": self.demo_user_password
        }
        
        try:
            login_response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                if "token" in data:
                    self.auth_token = data["token"]
                    self.log_result("Demo User Login", True, "Demo user already exists and login successful")
                    return True
            
            # If login failed, try to create demo user
            registration_data = {
                "email": self.demo_user_email,
                "password": self.demo_user_password,
                "name": self.demo_user_name
            }
            
            register_response = self.session.post(
                f"{self.base_url}/auth/register",
                json=registration_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if register_response.status_code in [200, 201]:
                data = register_response.json()
                if "token" in data:
                    self.auth_token = data["token"]
                    self.log_result("Demo User Creation", True, f"Demo user created successfully with ID: {data['user']['id']}")
                    return True
                else:
                    self.log_result("Demo User Creation", False, "Registration successful but no token returned")
            elif register_response.status_code == 400 and "already registered" in register_response.text:
                # User exists but login failed - password might be wrong
                self.log_result("Demo User Creation", False, "Demo user exists but login failed - check password")
            else:
                self.log_result("Demo User Creation", False, f"Registration failed: {register_response.status_code}, {register_response.text}")
                
        except Exception as e:
            self.log_result("Demo User Creation", False, f"Exception: {str(e)}")
            
        return False

    def test_authentication_endpoints(self):
        """Test authentication endpoints with various scenarios"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test registration with new user
        test_email = f"test_{int(time.time())}@energotest.com"
        registration_data = {
            "email": test_email,
            "password": "TestPass123!",
            "name": "Test User"
        }
        
        try:
            # Test registration
            register_response = self.session.post(
                f"{self.base_url}/auth/register",
                json=registration_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if register_response.status_code in [200, 201]:
                data = register_response.json()
                if "token" in data and "user" in data:
                    self.log_result("User Registration", True, f"New user registered successfully")
                    
                    # Test login with the new user
                    login_data = {
                        "email": test_email,
                        "password": "TestPass123!"
                    }
                    
                    login_response = self.session.post(
                        f"{self.base_url}/auth/login",
                        json=login_data,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if login_response.status_code == 200:
                        login_data_resp = login_response.json()
                        if "token" in login_data_resp:
                            self.log_result("User Login", True, "Login successful with new user")
                            
                            # Test invalid login
                            invalid_login = {
                                "email": test_email,
                                "password": "wrongpassword"
                            }
                            
                            invalid_response = self.session.post(
                                f"{self.base_url}/auth/login",
                                json=invalid_login,
                                headers={"Content-Type": "application/json"},
                                timeout=30
                            )
                            
                            if invalid_response.status_code == 401:
                                self.log_result("Invalid Login Handling", True, "Invalid credentials correctly rejected")
                                return True
                            else:
                                self.log_result("Invalid Login Handling", False, f"Expected 401, got {invalid_response.status_code}")
                        else:
                            self.log_result("User Login", False, "Login response missing token")
                    else:
                        self.log_result("User Login", False, f"Login failed: {login_response.status_code}")
                else:
                    self.log_result("User Registration", False, "Registration response missing token or user")
            else:
                self.log_result("User Registration", False, f"Registration failed: {register_response.status_code}, {register_response.text}")
                
        except Exception as e:
            self.log_result("Authentication Endpoints", False, f"Exception: {str(e)}")
            
        return False

    def test_database_connection(self):
        """Test MongoDB connection by attempting to access user data"""
        print("\n🗄️ Testing Database Connection...")
        
        if not self.auth_token:
            self.log_result("Database Connection", False, "No auth token available for testing")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Test database by accessing dashboard (requires DB queries)
            response = self.session.get(
                f"{self.base_url}/dashboard",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "summary" in data and "recent_readings" in data:
                    self.log_result("Database Connection", True, "Database queries successful - MongoDB connection working")
                    return True
                else:
                    self.log_result("Database Connection", False, "Database response missing expected data")
            else:
                self.log_result("Database Connection", False, f"Database query failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Database Connection", False, f"Exception: {str(e)}")
            
        return False

    def test_environment_variables(self):
        """Test that EMERGENT_LLM_KEY is properly loaded by testing AI chat"""
        print("\n🔑 Testing Environment Variables (EMERGENT_LLM_KEY)...")
        
        if not self.auth_token:
            self.log_result("Environment Variables", False, "No auth token available for testing")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Test AI chat which requires EMERGENT_LLM_KEY
            chat_data = {
                "message": "Hello, can you help me with energy saving tips?",
                "session_id": None
            }
            
            response = self.session.post(
                f"{self.base_url}/ai-chat",
                json=chat_data,
                headers=headers,
                timeout=45  # AI responses may take longer
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data and data["response"] and len(data["response"]) > 10:
                    self.log_result("Environment Variables (EMERGENT_LLM_KEY)", True, "AI chat working - EMERGENT_LLM_KEY properly loaded")
                    return True
                else:
                    self.log_result("Environment Variables (EMERGENT_LLM_KEY)", False, "AI chat response empty or too short")
            elif response.status_code == 500:
                error_text = response.text
                if "AI service unavailable" in error_text or "EMERGENT_LLM_KEY" in error_text:
                    self.log_result("Environment Variables (EMERGENT_LLM_KEY)", False, "EMERGENT_LLM_KEY not properly configured")
                else:
                    self.log_result("Environment Variables (EMERGENT_LLM_KEY)", False, f"AI service error: {error_text}")
            else:
                self.log_result("Environment Variables (EMERGENT_LLM_KEY)", False, f"AI chat failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Environment Variables (EMERGENT_LLM_KEY)", False, f"Exception: {str(e)}")
            
        return False

    def test_api_endpoint_structure(self):
        """Test that all /api/* routes are working"""
        print("\n🛣️ Testing API Endpoint Structure...")
        
        if not self.auth_token:
            self.log_result("API Endpoint Structure", False, "No auth token available for testing")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        # Test key API endpoints
        endpoints_to_test = [
            ("/dashboard", "Dashboard"),
            ("/ai-insights", "AI Insights"),
            ("/badges", "Badges"),
            ("/notifications", "Notifications"),
            ("/settings", "Settings"),
            ("/subscription", "Subscription"),
            ("/challenges", "Challenges")
        ]
        
        successful_endpoints = 0
        
        for endpoint, name in endpoints_to_test:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    successful_endpoints += 1
                    print(f"  ✅ {name} endpoint working")
                else:
                    print(f"  ❌ {name} endpoint failed: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {name} endpoint error: {str(e)}")
        
        if successful_endpoints >= len(endpoints_to_test) * 0.8:  # 80% success rate
            self.log_result("API Endpoint Structure", True, f"{successful_endpoints}/{len(endpoints_to_test)} endpoints working")
            return True
        else:
            self.log_result("API Endpoint Structure", False, f"Only {successful_endpoints}/{len(endpoints_to_test)} endpoints working")
            
        return False

    def test_protected_endpoints_security(self):
        """Test that protected endpoints require authentication"""
        print("\n🔒 Testing Protected Endpoints Security...")
        
        protected_endpoints = ["/dashboard", "/ai-insights", "/badges", "/settings"]
        
        successful_protections = 0
        
        for endpoint in protected_endpoints:
            try:
                # Test without authorization header
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=30
                )
                
                if response.status_code in [401, 403]:
                    successful_protections += 1
                    print(f"  ✅ {endpoint} properly protected")
                else:
                    print(f"  ❌ {endpoint} not properly protected: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {endpoint} protection test error: {str(e)}")
        
        if successful_protections >= len(protected_endpoints) * 0.8:
            self.log_result("Protected Endpoints Security", True, f"{successful_protections}/{len(protected_endpoints)} endpoints properly protected")
            return True
        else:
            self.log_result("Protected Endpoints Security", False, f"Only {successful_protections}/{len(protected_endpoints)} endpoints properly protected")
            
        return False

    def run_all_tests(self):
        """Run all backend tests as specified in review request"""
        print("🚀 Starting Energo Smart App Backend Testing")
        print("=" * 60)
        print("Testing areas specified in review request:")
        print("1. Health Check")
        print("2. Authentication Endpoints") 
        print("3. Demo User Creation")
        print("4. Database Connection")
        print("5. Environment Variables")
        print("6. API Endpoint Structure")
        print("7. CORS Configuration")
        print("=" * 60)
        
        # Test 1: Health Check
        self.test_health_check()
        
        # Test 7: CORS Configuration
        self.test_cors_configuration()
        
        # Test 3: Demo User Creation (this also tests auth endpoints)
        demo_success = self.test_demo_user_creation()
        
        # Test 2: Authentication Endpoints (comprehensive testing)
        self.test_authentication_endpoints()
        
        # Test 4: Database Connection (requires auth token)
        if self.auth_token:
            self.test_database_connection()
            
            # Test 5: Environment Variables (EMERGENT_LLM_KEY)
            self.test_environment_variables()
            
            # Test 6: API Endpoint Structure
            self.test_api_endpoint_structure()
        else:
            print("⚠️  Skipping database and API tests - no authentication token available")
            
        # Additional security tests
        self.test_protected_endpoints_security()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 BACKEND TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        
        if self.results['errors']:
            print("\n❌ FAILED TESTS:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Specific feedback for review areas
        print("\n🎯 REVIEW REQUEST AREAS STATUS:")
        if demo_success:
            print("✅ Demo login (demo@energo.com / password123) should work")
        else:
            print("❌ Demo login needs attention")
            
        if success_rate >= 80:
            print("🎉 Backend is ready for demo!")
        elif success_rate >= 60:
            print("⚠️  Backend has some issues that may affect demo")
        else:
            print("🚨 Backend has significant issues that will prevent demo from working")
            
        return success_rate >= 80

if __name__ == "__main__":
    tester = EnergoBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)