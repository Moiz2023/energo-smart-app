#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Energo Energy Tracking App
Tests all authentication and energy tracking endpoints
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

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
    return "https://energo-premium.preview.emergentagent.com/api"

BASE_URL = get_backend_url()
print(f"Testing backend at: {BASE_URL}")

class EnergoBackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_email = "sarah.johnson@energotest.com"
        self.test_user_password = "SecurePass123!"
        self.test_user_name = "Sarah Johnson"
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

    def test_user_registration(self):
        """Test user registration endpoint"""
        print("\n🔐 Testing User Registration...")
        
        # Test successful registration
        registration_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "name": self.test_user_name
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=registration_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 201 or response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.auth_token = data["token"]
                    self.log_result("User Registration", True, f"User created with ID: {data['user']['id']}")
                    return True
                else:
                    self.log_result("User Registration", False, "Missing token or user in response")
            elif response.status_code == 400 and "already registered" in response.text:
                # User already exists, try to login instead
                self.log_result("User Registration", True, "User already exists (expected)")
                return True
            else:
                self.log_result("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("User Registration", False, f"Exception: {str(e)}")
            
        return False

    def test_user_login(self):
        """Test user login endpoint"""
        print("\n🔑 Testing User Login...")
        
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.auth_token = data["token"]
                    self.log_result("User Login", True, f"Login successful for user: {data['user']['name']}")
                    return True
                else:
                    self.log_result("User Login", False, "Missing token or user in response")
            else:
                self.log_result("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("User Login", False, f"Exception: {str(e)}")
            
        return False

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        print("\n🚫 Testing Invalid Login...")
        
        invalid_login_data = {
            "email": self.test_user_email,
            "password": "wrongpassword"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=invalid_login_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 401:
                self.log_result("Invalid Login Handling", True, "Correctly rejected invalid credentials")
                return True
            else:
                self.log_result("Invalid Login Handling", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Invalid Login Handling", False, f"Exception: {str(e)}")
            
        return False

    def test_dashboard_endpoint(self):
        """Test dashboard endpoint with authentication"""
        print("\n📊 Testing Dashboard Endpoint...")
        
        if not self.auth_token:
            self.log_result("Dashboard Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/dashboard",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["summary", "chart_data", "recent_readings"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check summary data structure
                    summary = data["summary"]
                    summary_fields = ["total_consumption_kwh", "total_cost_euros", "month_consumption_kwh", "month_cost_euros"]
                    
                    if all(field in summary for field in summary_fields):
                        self.log_result("Dashboard Data Structure", True, f"All required fields present")
                        
                        # Validate data types and values
                        if (isinstance(summary["total_consumption_kwh"], (int, float)) and 
                            isinstance(summary["total_cost_euros"], (int, float)) and
                            isinstance(data["chart_data"], list)):
                            self.log_result("Dashboard Data Validation", True, f"Data types correct, {len(data['chart_data'])} chart points")
                            return True
                        else:
                            self.log_result("Dashboard Data Validation", False, "Invalid data types")
                    else:
                        self.log_result("Dashboard Data Structure", False, f"Missing summary fields: {[f for f in summary_fields if f not in summary]}")
                else:
                    self.log_result("Dashboard Data Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_result("Dashboard Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Dashboard Access", False, f"Exception: {str(e)}")
            
        return False

    def test_ai_tips_endpoint(self):
        """Test AI tips endpoint"""
        print("\n💡 Testing AI Tips Endpoint...")
        
        if not self.auth_token:
            self.log_result("AI Tips Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/ai-tips",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "tips" in data and isinstance(data["tips"], list) and len(data["tips"]) > 0:
                    # Check tip structure
                    tip = data["tips"][0]
                    required_tip_fields = ["id", "title", "content", "category", "potential_savings"]
                    
                    if all(field in tip for field in required_tip_fields):
                        self.log_result("AI Tips Structure", True, f"Received {len(data['tips'])} tips with correct structure")
                        return True
                    else:
                        self.log_result("AI Tips Structure", False, f"Missing tip fields: {[f for f in required_tip_fields if f not in tip]}")
                else:
                    self.log_result("AI Tips Data", False, "No tips in response or invalid format")
            else:
                self.log_result("AI Tips Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("AI Tips Access", False, f"Exception: {str(e)}")
            
        return False

    def test_badges_endpoint(self):
        """Test badges endpoint"""
        print("\n🏆 Testing Badges Endpoint...")
        
        if not self.auth_token:
            self.log_result("Badges Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/badges",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "badges" in data and isinstance(data["badges"], list) and len(data["badges"]) > 0:
                    # Check badge structure
                    badge = data["badges"][0]
                    required_badge_fields = ["id", "name", "description", "icon"]
                    
                    if all(field in badge for field in required_badge_fields):
                        self.log_result("Badges Structure", True, f"Received {len(data['badges'])} badges with correct structure")
                        return True
                    else:
                        self.log_result("Badges Structure", False, f"Missing badge fields: {[f for f in required_badge_fields if f not in badge]}")
                else:
                    self.log_result("Badges Data", False, "No badges in response or invalid format")
            else:
                self.log_result("Badges Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Badges Access", False, f"Exception: {str(e)}")
            
        return False

    def test_notifications_endpoint(self):
        """Test notifications endpoint"""
        print("\n🔔 Testing Notifications Endpoint...")
        
        if not self.auth_token:
            self.log_result("Notifications Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/notifications",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "notifications" in data and isinstance(data["notifications"], list):
                    if len(data["notifications"]) > 0:
                        # Check notification structure
                        notification = data["notifications"][0]
                        required_notification_fields = ["id", "title", "message", "type", "timestamp"]
                        
                        if all(field in notification for field in required_notification_fields):
                            self.log_result("Notifications Structure", True, f"Received {len(data['notifications'])} notifications with correct structure")
                            return True
                        else:
                            self.log_result("Notifications Structure", False, f"Missing notification fields: {[f for f in required_notification_fields if f not in notification]}")
                    else:
                        self.log_result("Notifications Data", True, "No notifications (empty list is valid)")
                        return True
                else:
                    self.log_result("Notifications Data", False, "No notifications field in response or invalid format")
            else:
                self.log_result("Notifications Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Notifications Access", False, f"Exception: {str(e)}")
            
        return False

    def test_unauthorized_access(self):
        """Test accessing protected endpoints without authentication"""
        print("\n🔒 Testing Unauthorized Access...")
        
        endpoints = ["/dashboard", "/ai-tips", "/badges", "/notifications"]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=30
                )
                
                if response.status_code == 401 or response.status_code == 403:
                    self.log_result(f"Unauthorized Access Protection ({endpoint})", True, "Correctly rejected unauthorized request")
                else:
                    self.log_result(f"Unauthorized Access Protection ({endpoint})", False, f"Expected 401/403, got {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Unauthorized Access Protection ({endpoint})", False, f"Exception: {str(e)}")

    def test_invalid_token_access(self):
        """Test accessing protected endpoints with invalid token"""
        print("\n🔐 Testing Invalid Token Access...")
        
        invalid_headers = {
            "Authorization": "Bearer invalid_token_here",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/dashboard",
                headers=invalid_headers,
                timeout=30
            )
            
            if response.status_code == 401:
                self.log_result("Invalid Token Protection", True, "Correctly rejected invalid token")
            else:
                self.log_result("Invalid Token Protection", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Invalid Token Protection", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Energo Backend API Tests")
        print("=" * 50)
        
        # Test authentication flow
        registration_success = self.test_user_registration()
        # Always try login to get token for protected endpoint tests
        login_success = self.test_user_login()
            
        # Test invalid login
        self.test_invalid_login()
        
        # Test protected endpoints (only if we have auth)
        if self.auth_token:
            self.test_dashboard_endpoint()
            self.test_ai_tips_endpoint()
            self.test_badges_endpoint()
            self.test_notifications_endpoint()
        else:
            print("⚠️  Skipping protected endpoint tests - no authentication token")
            
        # Test security
        self.test_unauthorized_access()
        self.test_invalid_token_access()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        
        if self.results['errors']:
            print("\n❌ FAILED TESTS:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Backend tests mostly successful!")
        elif success_rate >= 60:
            print("⚠️  Backend has some issues that need attention")
        else:
            print("🚨 Backend has significant issues that need immediate attention")
            
        return success_rate >= 80

if __name__ == "__main__":
    tester = EnergoBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)