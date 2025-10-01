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
                if line.startswith('EXPO_PACKAGER_PROXY_URL='):
                    base_url = line.split('=')[1].strip().strip('"')
                    return f"{base_url}/api"
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    return "https://energo-reset.preview.emergentagent.com/api"

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
                    summary_fields = ["current_consumption_kwh", "current_cost_euros", "consumption_change_percent", "cost_change_percent"]
                    
                    if all(field in summary for field in summary_fields):
                        self.log_result("Dashboard Data Structure", True, f"All required fields present")
                        
                        # Validate data types and values
                        if (isinstance(summary["current_consumption_kwh"], (int, float)) and 
                            isinstance(summary["current_cost_euros"], (int, float)) and
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
        """Test AI insights endpoint (legacy ai-tips test)"""
        print("\n💡 Testing AI Insights Endpoint (Legacy AI Tips)...")
        
        if not self.auth_token:
            self.log_result("AI Tips Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/ai-insights",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "insights" in data and isinstance(data["insights"], list) and len(data["insights"]) > 0:
                    # Check insight structure
                    insight = data["insights"][0]
                    required_tip_fields = ["id", "title", "content", "category", "potential_savings"]
                    
                    if all(field in insight for field in required_tip_fields):
                        self.log_result("AI Tips Structure", True, f"Received {len(data['insights'])} insights with correct structure")
                        return True
                    else:
                        self.log_result("AI Tips Structure", False, f"Missing insight fields: {[f for f in required_tip_fields if f not in insight]}")
                else:
                    self.log_result("AI Tips Data", False, "No insights in response or invalid format")
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

    def test_ai_insights_endpoint(self):
        """Test AI insights endpoint"""
        print("\n🧠 Testing AI Insights Endpoint...")
        
        if not self.auth_token:
            self.log_result("AI Insights Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/ai-insights",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["insights", "patterns", "subsidies", "region"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check insights structure
                    if isinstance(data["insights"], list) and len(data["insights"]) > 0:
                        insight = data["insights"][0]
                        insight_fields = ["id", "title", "content", "category", "potential_savings"]
                        
                        if all(field in insight for field in insight_fields):
                            self.log_result("AI Insights Structure", True, f"Received {len(data['insights'])} insights with correct structure")
                            return True
                        else:
                            self.log_result("AI Insights Structure", False, f"Missing insight fields: {[f for f in insight_fields if f not in insight]}")
                    else:
                        self.log_result("AI Insights Data", False, "No insights in response or invalid format")
                else:
                    self.log_result("AI Insights Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_result("AI Insights Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("AI Insights Access", False, f"Exception: {str(e)}")
            
        return False

    def test_ai_chat_endpoint(self):
        """Test interactive AI chat endpoint"""
        print("\n💬 Testing AI Chat Endpoint...")
        
        if not self.auth_token:
            self.log_result("AI Chat Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Test basic chat message
            chat_data = {
                "message": "How can I reduce my energy consumption?",
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
                
                required_fields = ["response", "session_id", "timestamp"]
                if all(field in data for field in required_fields):
                    if data["response"] and len(data["response"]) > 10:  # Meaningful response
                        self.log_result("AI Chat Basic Response", True, f"Received response with session_id: {data['session_id'][:8]}...")
                        
                        # Test follow-up message with session_id
                        follow_up_data = {
                            "message": "What about solar panels?",
                            "session_id": data["session_id"]
                        }
                        
                        follow_up_response = self.session.post(
                            f"{self.base_url}/ai-chat",
                            json=follow_up_data,
                            headers=headers,
                            timeout=45
                        )
                        
                        if follow_up_response.status_code == 200:
                            follow_up_data_resp = follow_up_response.json()
                            if follow_up_data_resp["session_id"] == data["session_id"]:
                                self.log_result("AI Chat Session Continuity", True, "Session ID maintained across messages")
                                return True
                            else:
                                self.log_result("AI Chat Session Continuity", False, "Session ID not maintained")
                        else:
                            self.log_result("AI Chat Follow-up", False, f"Follow-up failed: {follow_up_response.status_code}")
                    else:
                        self.log_result("AI Chat Response Quality", False, "Response too short or empty")
                else:
                    self.log_result("AI Chat Structure", False, f"Missing fields: {[f for f in required_fields if f not in data]}")
            else:
                self.log_result("AI Chat Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("AI Chat Access", False, f"Exception: {str(e)}")
            
        return False

    def test_ai_chat_history_endpoint(self):
        """Test AI chat history endpoint"""
        print("\n📜 Testing AI Chat History Endpoint...")
        
        if not self.auth_token:
            self.log_result("AI Chat History Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/ai-chat/history",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "chat_history" in data and isinstance(data["chat_history"], list):
                    if len(data["chat_history"]) > 0:
                        # Check history structure
                        history_item = data["chat_history"][0]
                        required_fields = ["id", "message", "response", "timestamp", "session_id"]
                        
                        if all(field in history_item for field in required_fields):
                            self.log_result("AI Chat History Structure", True, f"Retrieved {len(data['chat_history'])} chat history items")
                            return True
                        else:
                            self.log_result("AI Chat History Structure", False, f"Missing fields: {[f for f in required_fields if f not in history_item]}")
                    else:
                        self.log_result("AI Chat History Data", True, "No chat history (empty list is valid)")
                        return True
                else:
                    self.log_result("AI Chat History Data", False, "No chat_history field in response")
            else:
                self.log_result("AI Chat History Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("AI Chat History Access", False, f"Exception: {str(e)}")
            
        return False

    def test_subscription_endpoint(self):
        """Test subscription endpoint"""
        print("\n💳 Testing Subscription Endpoint...")
        
        if not self.auth_token:
            self.log_result("Subscription Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/subscription",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["current_plan", "plans"]
                if all(field in data for field in required_fields):
                    # Check if user has premium access as configured
                    if data["current_plan"] == "premium":
                        self.log_result("Premium Access Configuration", True, "User has premium access as configured")
                        
                        # Check plans structure
                        if "free" in data["plans"] and "premium" in data["plans"]:
                            premium_plan = data["plans"]["premium"]
                            if "features" in premium_plan and isinstance(premium_plan["features"], list):
                                self.log_result("Subscription Plans Structure", True, f"Premium plan has {len(premium_plan['features'])} features")
                                return True
                            else:
                                self.log_result("Subscription Plans Structure", False, "Premium plan missing features")
                        else:
                            self.log_result("Subscription Plans Structure", False, "Missing free or premium plan")
                    else:
                        self.log_result("Premium Access Configuration", False, f"Expected premium, got {data['current_plan']}")
                else:
                    self.log_result("Subscription Structure", False, f"Missing fields: {[f for f in required_fields if f not in data]}")
            else:
                self.log_result("Subscription Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Subscription Access", False, f"Exception: {str(e)}")
            
        return False

    def test_settings_endpoint(self):
        """Test settings endpoint"""
        print("\n⚙️ Testing Settings Endpoint...")
        
        if not self.auth_token:
            self.log_result("Settings Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/settings",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "settings" in data:
                    settings = data["settings"]
                    required_settings = ["language", "currency_unit", "notifications_enabled", "subscription_plan", "region"]
                    
                    if all(field in settings for field in required_settings):
                        # Check if premium settings are configured
                        if settings["subscription_plan"] == "premium":
                            self.log_result("Premium Settings Configuration", True, "Settings show premium subscription")
                            return True
                        else:
                            self.log_result("Premium Settings Configuration", False, f"Expected premium subscription, got {settings['subscription_plan']}")
                    else:
                        self.log_result("Settings Structure", False, f"Missing settings: {[f for f in required_settings if f not in settings]}")
                else:
                    self.log_result("Settings Structure", False, "No settings field in response")
            else:
                self.log_result("Settings Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Settings Access", False, f"Exception: {str(e)}")
            
        return False

    def test_fluvius_data_endpoint(self):
        """Test Fluvius data endpoint for premium users"""
        print("\n🏭 Testing Fluvius Data Endpoint...")
        
        if not self.auth_token:
            self.log_result("Fluvius Data Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/fluvius-data",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if premium user gets real data access
                required_fields = ["data_source", "location", "data"]
                if all(field in data for field in required_fields):
                    if isinstance(data["data"], list) and len(data["data"]) > 0:
                        data_item = data["data"][0]
                        data_fields = ["municipality", "period"]
                        
                        if all(field in data_item for field in data_fields):
                            self.log_result("Fluvius Data Structure", True, f"Retrieved {len(data['data'])} data points from {data['data_source']}")
                            return True
                        else:
                            self.log_result("Fluvius Data Structure", False, f"Missing data fields: {[f for f in data_fields if f not in data_item]}")
                    else:
                        self.log_result("Fluvius Data Content", False, "No data items in response")
                else:
                    self.log_result("Fluvius Data Structure", False, f"Missing fields: {[f for f in required_fields if f not in data]}")
            else:
                self.log_result("Fluvius Data Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Fluvius Data Access", False, f"Exception: {str(e)}")
            
        return False

    def test_logout_endpoint(self):
        """Test logout endpoint"""
        print("\n🚪 Testing Logout Endpoint...")
        
        if not self.auth_token:
            self.log_result("Logout Access", False, "No auth token available")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/logout",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_result("Logout Functionality", True, "Logout successful")
                    return True
                else:
                    self.log_result("Logout Functionality", False, "No message in logout response")
            else:
                self.log_result("Logout Access", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Logout Access", False, f"Exception: {str(e)}")
            
        return False

    def test_ai_chat_with_various_messages(self):
        """Test AI chat with various message types"""
        print("\n🗨️ Testing AI Chat with Various Message Types...")
        
        if not self.auth_token:
            self.log_result("AI Chat Variety Test", False, "No auth token available")
            return False
            
        test_messages = [
            "What are the best energy saving tips for winter?",
            "Tell me about solar panel subsidies in Brussels",
            "How much can I save with better insulation?",
            "What's my current energy consumption pattern?",
            "Are there any new energy regulations in Belgium?"
        ]
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        successful_responses = 0
        
        for i, message in enumerate(test_messages):
            try:
                chat_data = {
                    "message": message,
                    "session_id": None
                }
                
                response = self.session.post(
                    f"{self.base_url}/ai-chat",
                    json=chat_data,
                    headers=headers,
                    timeout=45
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("response") and len(data["response"]) > 20:
                        successful_responses += 1
                        
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"  Message {i+1} failed: {str(e)}")
        
        if successful_responses >= len(test_messages) * 0.8:  # 80% success rate
            self.log_result("AI Chat Message Variety", True, f"{successful_responses}/{len(test_messages)} message types handled successfully")
            return True
        else:
            self.log_result("AI Chat Message Variety", False, f"Only {successful_responses}/{len(test_messages)} message types handled successfully")
            
        return False

    def test_property_management_status(self):
        """Test property management feature status"""
        print("\n🏠 Testing Property Management Status...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/property-management-status",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                enabled = data.get("enabled", False)
                message = data.get("message", "No message")
                
                self.log_result("Property Management Status", enabled, message)
                return enabled
            else:
                self.log_result("Property Management Status", False, f"Status check failed with {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Property Management Status", False, f"Status check failed: {str(e)}")
            return False

    def test_usage_scenarios_endpoint(self):
        """Test GET /api/usage-scenarios endpoint"""
        print("\n📋 Testing Usage Scenarios Endpoint...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/usage-scenarios",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                scenarios = data.get("scenarios", {})
                
                if scenarios:
                    scenario_count = len(scenarios)
                    scenario_names = list(scenarios.keys())
                    self.log_result("Usage Scenarios", True, 
                                  f"Retrieved {scenario_count} scenarios: {', '.join(scenario_names)}")
                    
                    # Check for expected demo scenarios
                    expected_scenarios = ["family_home", "ev_owner", "small_apartment", "large_house"]
                    found_scenarios = [s for s in expected_scenarios if s in scenarios]
                    if found_scenarios:
                        self.log_result("Demo Scenarios Available", True, 
                                      f"Found demo scenarios: {', '.join(found_scenarios)}")
                        return True
                    else:
                        self.log_result("Demo Scenarios Available", False, 
                                      f"No expected demo scenarios found. Available: {', '.join(scenario_names)}")
                        return False
                else:
                    self.log_result("Usage Scenarios", False, "No scenarios returned")
                    return False
            else:
                self.log_result("Usage Scenarios", False, 
                              f"Request failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Usage Scenarios", False, f"Request failed: {str(e)}")
            return False

    def test_device_templates_endpoint(self):
        """Test GET /api/device-templates endpoint"""
        print("\n🔌 Testing Device Templates Endpoint...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/device-templates",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                common_devices = data.get("common_devices", [])
                by_category = data.get("by_category", {})
                all_templates = data.get("all_templates", [])
                
                if common_devices or by_category or all_templates:
                    self.log_result("Device Templates", True, 
                                  f"Retrieved {len(common_devices)} common devices, "
                                  f"{len(by_category)} categories, {len(all_templates)} total templates")
                    
                    # Check categories
                    if by_category:
                        categories = list(by_category.keys())
                        self.log_result("Device Categories", True, 
                                      f"Available categories: {', '.join(categories)}")
                    
                    return True
                else:
                    self.log_result("Device Templates", False, "No device templates returned")
                    return False
            else:
                self.log_result("Device Templates", False, 
                              f"Request failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Device Templates", False, f"Request failed: {str(e)}")
            return False

    def test_properties_get_endpoint(self):
        """Test GET /api/properties endpoint (authenticated)"""
        print("\n🏠 Testing Properties GET Endpoint...")
        
        if not self.auth_token:
            self.log_result("Properties GET", False, "No authentication token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/properties",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                properties = data.get("properties", [])
                
                self.log_result("Properties GET", True, 
                              f"Retrieved {len(properties)} properties for user")
                
                if properties:
                    # Show details of first property
                    first_property = properties[0]
                    property_name = first_property.get("name", "Unknown")
                    property_type = first_property.get("property_type", "Unknown")
                    self.log_result("Property Details", True, 
                                  f"Sample property: {property_name} ({property_type})")
                
                return True
            elif response.status_code == 401:
                self.log_result("Properties GET", False, "Authentication failed - invalid token")
                return False
            else:
                self.log_result("Properties GET", False, 
                              f"Request failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Properties GET", False, f"Request failed: {str(e)}")
            return False

    def test_setup_scenario_endpoint(self):
        """Test POST /api/setup-scenario/{scenario_key} endpoint"""
        print("\n🎯 Testing Setup Scenario Endpoint...")
        
        if not self.auth_token:
            self.log_result("Setup Scenario", False, "No authentication token available")
            return False
        
        # Try to setup a family home scenario
        scenario_key = "family_home"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(
                f"{self.base_url}/setup-scenario/{scenario_key}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                property_id = data.get("property_id")
                devices_created = data.get("devices_created", 0)
                
                self.log_result("Setup Scenario", True, 
                              f"Successfully created {scenario_key} scenario with {devices_created} devices")
                
                if property_id:
                    self.log_result("Demo Property Creation", True, f"Created demo property with ID: {property_id}")
                
                return True
            elif response.status_code == 401:
                self.log_result("Setup Scenario", False, "Authentication failed - invalid token")
                return False
            elif response.status_code == 404:
                self.log_result("Setup Scenario", False, f"Scenario '{scenario_key}' not found")
                return False
            else:
                self.log_result("Setup Scenario", False, 
                              f"Request failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Setup Scenario", False, f"Request failed: {str(e)}")
            return False

    def test_create_property_endpoint(self):
        """Test POST /api/properties endpoint"""
        print("\n🏗️ Testing Create Property Endpoint...")
        
        if not self.auth_token:
            self.log_result("Create Property", False, "No authentication token available")
            return False
        
        # Create a test property
        property_data = {
            "name": "Test Property",
            "property_type": "house",
            "address": "123 Test Street, Brussels, Belgium",
            "size_m2": 120,
            "bedrooms": 3,
            "occupants": 2,
            "construction_year": 2010
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(
                f"{self.base_url}/properties",
                json=property_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                property_id = data.get("property_id") or data.get("id")
                
                self.log_result("Create Property", True, 
                              f"Successfully created property: {property_data['name']}")
                
                if property_id:
                    self.log_result("Property Creation ID", True, f"Property created with ID: {property_id}")
                
                return True
            elif response.status_code == 401:
                self.log_result("Create Property", False, "Authentication failed - invalid token")
                return False
            else:
                self.log_result("Create Property", False, 
                              f"Request failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create Property", False, f"Request failed: {str(e)}")
            return False

    def test_unauthorized_access(self):
        """Test accessing protected endpoints without authentication"""
        print("\n🔒 Testing Unauthorized Access...")
        
        endpoints = ["/dashboard", "/ai-insights", "/badges", "/notifications"]
        
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
        
        # Test property management features first (as requested by user)
        print("\n🔹 Testing Property Management Features...")
        property_mgmt_enabled = self.test_property_management_status()
        self.test_usage_scenarios_endpoint()
        self.test_device_templates_endpoint()
        
        # Test protected endpoints (only if we have auth)
        if self.auth_token:
            print("\n🔹 Testing Property Management (Authenticated)...")
            self.test_properties_get_endpoint()
            self.test_setup_scenario_endpoint()
            self.test_create_property_endpoint()
            
            print("\n🔹 Testing Existing Functionality...")
            self.test_dashboard_endpoint()
            self.test_ai_tips_endpoint()
            self.test_ai_insights_endpoint()
            self.test_badges_endpoint()
            self.test_notifications_endpoint()
            self.test_logout_endpoint()
            
            print("\n🔹 Testing Premium Features...")
            self.test_subscription_endpoint()
            self.test_settings_endpoint()
            self.test_fluvius_data_endpoint()
            
            print("\n🔹 Testing Interactive AI Chat...")
            self.test_ai_chat_endpoint()
            self.test_ai_chat_history_endpoint()
            self.test_ai_chat_with_various_messages()
        else:
            print("⚠️  Skipping protected endpoint tests - no authentication token")
            
        # Test security
        print("\n🔹 Testing Security...")
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