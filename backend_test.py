#!/usr/bin/env python3
"""
Backend API Testing Suite for Energo Smart Energy Management
Focus: Testing all user-reported issues after main agent fixes:
1. AI Chat functionality (POST /api/ai-chat, GET /api/ai-chat/history)
2. New scenario selection (POST /api/setup-scenario/{scenario_key})
3. Device/equipment addition (POST /api/properties/{property_id}/devices)
4. Property management (GET /api/properties)
"""

import requests
import json
import time
import uuid
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
print(f"🚀 Testing Energo Backend API at: {BASE_URL}")
print("Focus: POST /api/setup-scenario/family_home endpoint")
print("=" * 60)

# Demo user credentials as specified in the review request
DEMO_USER = {
    "email": "demo@energo.com",
    "password": "password123"
}

class EnergoBackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "critical_failures": []
        }

    def log_result(self, test_name, success, message="", is_critical=False):
        self.results["total_tests"] += 1
        if success:
            self.results["passed"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.results["failed"] += 1
            print(f"❌ {test_name}: FAILED {message}")
            self.results["errors"].append(f"{test_name}: {message}")
            if is_critical:
                self.results["critical_failures"].append(test_name)

    def test_demo_user_login(self):
        """Test login with demo user credentials"""
        print("\n🔐 Testing Demo User Login...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=DEMO_USER,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.auth_token = data["token"]
                    self.user_id = data["user"]["id"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_result("Demo User Login", True, f"Logged in as {DEMO_USER['email']}, User ID: {self.user_id}", is_critical=True)
                    return True
                else:
                    self.log_result("Demo User Login", False, "Missing token or user in response", is_critical=True)
            else:
                self.log_result("Demo User Login", False, f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("Demo User Login", False, f"Exception: {str(e)}", is_critical=True)
        
        return False

    def test_property_management_status(self):
        """Test property management status endpoint"""
        print("\n🏠 Testing Property Management Status...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/property-management-status",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                enabled = data.get("enabled", False)
                self.log_result("Property Management Status", enabled, f"Property management enabled: {enabled}")
                return enabled
            else:
                self.log_result("Property Management Status", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Property Management Status", False, f"Exception: {str(e)}")
        
        return False

    def test_get_usage_scenarios(self):
        """Test GET /api/usage-scenarios endpoint"""
        print("\n📋 Testing Usage Scenarios...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/usage-scenarios",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                scenarios = data.get("scenarios", {})
                family_home_exists = "family_home" in scenarios
                
                if family_home_exists:
                    family_home = scenarios["family_home"]
                    self.log_result("Get Usage Scenarios", True, f"Found {len(scenarios)} scenarios including family_home: '{family_home.get('name', 'N/A')}'")
                    print(f"   Family Home Details: {family_home.get('description', 'N/A')}")
                else:
                    self.log_result("Get Usage Scenarios", False, f"family_home scenario not found. Available: {list(scenarios.keys())}")
                
                return family_home_exists
            else:
                self.log_result("Get Usage Scenarios", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Get Usage Scenarios", False, f"Exception: {str(e)}")
        
        return False

    def test_setup_family_home_scenario(self):
        """Test POST /api/setup-scenario/family_home endpoint - MAIN TEST"""
        print("\n🎯 Testing Setup Family Home Scenario (MAIN TEST)...")
        
        if not self.auth_token:
            self.log_result("Setup Family Home Scenario", False, "No authentication token available", is_critical=True)
            return False, None
        
        try:
            response = self.session.post(
                f"{self.base_url}/setup-scenario/family_home",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                property_id = data.get("property_id")
                devices_created = data.get("devices_created", 0)
                readings_created = data.get("meter_readings_created", 0)
                message = data.get("message", "")
                
                if property_id:
                    self.log_result("Setup Family Home Scenario", True, 
                                  f"✨ SUCCESS! Property ID: {property_id}, Devices: {devices_created}, Readings: {readings_created}", 
                                  is_critical=True)
                    print(f"   Message: {message}")
                    return True, property_id
                else:
                    self.log_result("Setup Family Home Scenario", False, "No property_id in response", is_critical=True)
            else:
                self.log_result("Setup Family Home Scenario", False, 
                              f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("Setup Family Home Scenario", False, f"Exception: {str(e)}", is_critical=True)
        
        return False, None

    def test_get_properties(self):
        """Test GET /api/properties endpoint"""
        print("\n🏘️ Testing Get Properties...")
        
        if not self.auth_token:
            self.log_result("Get Properties", False, "No authentication token available", is_critical=True)
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/properties",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                properties = data.get("properties", [])
                
                if len(properties) > 0:
                    self.log_result("Get Properties", True, f"Found {len(properties)} properties", is_critical=True)
                    for i, prop in enumerate(properties[:3]):  # Show first 3 properties
                        print(f"   Property {i+1}: {prop.get('name', 'Unknown')} (ID: {prop.get('id', 'N/A')})")
                        print(f"      Address: {prop.get('address', 'N/A')}")
                        print(f"      Type: {prop.get('property_type', 'N/A')}, Size: {prop.get('size_m2', 'N/A')} m²")
                    return True
                else:
                    self.log_result("Get Properties", False, "No properties found for user", is_critical=True)
            else:
                self.log_result("Get Properties", False, f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("Get Properties", False, f"Exception: {str(e)}", is_critical=True)
        
        return False

    def test_get_devices_for_property(self, property_id):
        """Test GET /api/properties/{property_id}/devices endpoint"""
        print(f"\n🔌 Testing Get Devices for Property {property_id}...")
        
        if not property_id:
            self.log_result("Get Devices for Property", False, "No property ID provided")
            return False
        
        if not self.auth_token:
            self.log_result("Get Devices for Property", False, "No authentication token available")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/properties/{property_id}/devices",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                devices = data.get("devices", [])
                
                if len(devices) > 0:
                    self.log_result("Get Devices for Property", True, f"Found {len(devices)} devices")
                    for i, device in enumerate(devices[:5]):  # Show first 5 devices
                        print(f"   Device {i+1}: {device.get('name', 'Unknown')} ({device.get('device_type', 'N/A')})")
                        print(f"      Power: {device.get('power_rating_watts', 'N/A')}W, Usage: {device.get('daily_usage_hours', 'N/A')}h/day")
                    return True
                else:
                    self.log_result("Get Devices for Property", False, "No devices found for property")
            else:
                self.log_result("Get Devices for Property", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Get Devices for Property", False, f"Exception: {str(e)}")
        
        return False

    def test_direct_property_creation(self):
        """Test POST /api/properties endpoint directly"""
        print("\n🏗️ Testing Direct Property Creation...")
        
        if not self.auth_token:
            self.log_result("Direct Property Creation", False, "No authentication token available")
            return False
        
        test_property = {
            "name": "Test Property",
            "address": "123 Test Street, Brussels",
            "property_type": "house",
            "size_m2": 120,
            "occupants": 2
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/properties",
                json=test_property,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                property_id = data.get("property_id")
                if property_id:
                    self.log_result("Direct Property Creation", True, f"Created property {property_id}")
                    return True
                else:
                    self.log_result("Direct Property Creation", False, "No property_id in response")
            else:
                self.log_result("Direct Property Creation", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Direct Property Creation", False, f"Exception: {str(e)}")
        
        return False

    def test_device_templates(self):
        """Test GET /api/device-templates endpoint"""
        print("\n🔧 Testing Device Templates...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/device-templates",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                common_devices = data.get("common_devices", [])
                all_templates = data.get("all_templates", [])
                
                self.log_result("Get Device Templates", len(common_devices) > 0, 
                              f"Found {len(common_devices)} common devices, {len(all_templates)} total templates")
                return len(common_devices) > 0
            else:
                self.log_result("Get Device Templates", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Get Device Templates", False, f"Exception: {str(e)}")
        
        return False

    def test_ai_chat_functionality(self):
        """Test AI Chat functionality - POST /api/ai-chat (USER REPORTED ISSUE)"""
        print("\n🤖 Testing AI Chat Functionality (USER REPORTED ISSUE)...")
        
        if not self.auth_token:
            self.log_result("AI Chat Functionality", False, "No authentication token available", is_critical=True)
            return False
        
        # Test different types of messages
        test_messages = [
            {
                "message": "Hello, can you help me with energy saving tips for my home?",
                "description": "Basic greeting and energy advice request"
            },
            {
                "message": "What are the current energy subsidies available in Brussels?",
                "description": "Subsidy information request"
            },
            {
                "message": "How can I reduce my evening energy consumption?",
                "description": "Specific energy optimization question"
            }
        ]
        
        session_id = str(uuid.uuid4())
        success_count = 0
        
        for i, test_msg in enumerate(test_messages):
            try:
                payload = {
                    "message": test_msg["message"],
                    "session_id": session_id
                }
                
                response = self.session.post(
                    f"{self.base_url}/ai-chat",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("response") and data.get("session_id"):
                        self.log_result(f"AI Chat Message {i+1}", True, 
                                      f"{test_msg['description']} - Response: {data['response'][:100]}...")
                        success_count += 1
                    else:
                        self.log_result(f"AI Chat Message {i+1}", False, 
                                      "Missing response or session_id in response", is_critical=True)
                else:
                    self.log_result(f"AI Chat Message {i+1}", False, 
                                  f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                    
            except Exception as e:
                self.log_result(f"AI Chat Message {i+1}", False, f"Exception: {str(e)}", is_critical=True)
        
        # Overall AI Chat functionality assessment
        if success_count == len(test_messages):
            self.log_result("AI Chat Functionality Overall", True, 
                          f"All {success_count}/{len(test_messages)} AI chat messages successful", is_critical=True)
            return True
        elif success_count > 0:
            self.log_result("AI Chat Functionality Overall", False, 
                          f"Partial success: {success_count}/{len(test_messages)} messages worked", is_critical=True)
        else:
            self.log_result("AI Chat Functionality Overall", False, 
                          "All AI chat messages failed", is_critical=True)
        
        return False

    def test_ai_chat_history(self):
        """Test AI Chat History - GET /api/ai-chat/history (USER REPORTED ISSUE)"""
        print("\n📜 Testing AI Chat History (USER REPORTED ISSUE)...")
        
        if not self.auth_token:
            self.log_result("AI Chat History", False, "No authentication token available", is_critical=True)
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/ai-chat/history",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                chat_history = data.get("chat_history", [])
                
                if isinstance(chat_history, list):
                    self.log_result("AI Chat History", True, 
                                  f"Retrieved {len(chat_history)} chat history items", is_critical=True)
                    
                    # Check if history items have required fields
                    if chat_history:
                        first_item = chat_history[0]
                        required_fields = ["id", "message", "response", "timestamp", "session_id"]
                        missing_fields = [field for field in required_fields if field not in first_item]
                        
                        if not missing_fields:
                            self.log_result("AI Chat History Structure", True, 
                                          "All required fields present in history items")
                        else:
                            self.log_result("AI Chat History Structure", False, 
                                          f"Missing fields in history: {missing_fields}")
                    return True
                else:
                    self.log_result("AI Chat History", False, 
                                  "chat_history is not a list", is_critical=True)
            else:
                self.log_result("AI Chat History", False, 
                              f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("AI Chat History", False, f"Exception: {str(e)}", is_critical=True)
        
        return False

    def test_new_scenario_selection(self):
        """Test new scenario selection endpoints (USER REPORTED ISSUE)"""
        print("\n🏠 Testing New Scenario Selection (USER REPORTED ISSUE)...")
        
        if not self.auth_token:
            self.log_result("New Scenario Selection", False, "No authentication token available", is_critical=True)
            return False
        
        scenarios = ["ev_owner", "small_business", "smart_home"]
        success_count = 0
        
        for scenario in scenarios:
            try:
                response = self.session.post(
                    f"{self.base_url}/setup-scenario/{scenario}",
                    json={},
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("property_id"):
                        self.log_result(f"Setup Scenario: {scenario}", True, 
                                      f"Property created with ID: {data['property_id']}")
                        success_count += 1
                    else:
                        self.log_result(f"Setup Scenario: {scenario}", False, 
                                      "No property_id returned", is_critical=True)
                else:
                    self.log_result(f"Setup Scenario: {scenario}", False, 
                                  f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                    
            except Exception as e:
                self.log_result(f"Setup Scenario: {scenario}", False, f"Exception: {str(e)}", is_critical=True)
        
        # Overall assessment
        if success_count == len(scenarios):
            self.log_result("New Scenario Selection Overall", True, 
                          f"All {success_count}/{len(scenarios)} scenarios working", is_critical=True)
            return True
        elif success_count > 0:
            self.log_result("New Scenario Selection Overall", False, 
                          f"Partial success: {success_count}/{len(scenarios)} scenarios working", is_critical=True)
        else:
            self.log_result("New Scenario Selection Overall", False, 
                          "All scenario selections failed", is_critical=True)
        
        return False

    def test_device_equipment_addition(self, property_id):
        """Test device/equipment addition functionality (USER REPORTED ISSUE)"""
        print(f"\n⚡ Testing Device/Equipment Addition (USER REPORTED ISSUE)...")
        
        if not property_id:
            self.log_result("Device Equipment Addition", False, "No property ID available for testing", is_critical=True)
            return False
        
        if not self.auth_token:
            self.log_result("Device Equipment Addition", False, "No authentication token available", is_critical=True)
            return False
        
        # Test GET /api/properties/{property_id}/devices first
        try:
            get_url = f"{self.base_url}/properties/{property_id}/devices"
            response = self.session.get(
                get_url,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                devices = data.get("devices", [])
                self.log_result("Device Retrieval", True, 
                              f"Retrieved {len(devices)} devices for property {property_id}")
            else:
                self.log_result("Device Retrieval", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Device Retrieval", False, f"Exception: {str(e)}")
        
        # Test POST /api/properties/{property_id}/devices
        device_data = {
            "name": "Test Energy Monitor",
            "device_type": "energy_monitor",
            "power_rating": 5,
            "usage_hours_per_day": 24,
            "location": "Main Panel"
        }
        
        try:
            post_url = f"{self.base_url}/properties/{property_id}/devices"
            response = self.session.post(
                post_url,
                json=device_data,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("device_id"):
                    self.log_result("Device Creation", True, 
                                  f"Device created with ID: {data['device_id']}", is_critical=True)
                    return True
                else:
                    self.log_result("Device Creation", False, 
                                  "No device_id returned", is_critical=True)
            else:
                self.log_result("Device Creation", False, 
                              f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("Device Creation", False, f"Exception: {str(e)}", is_critical=True)
        
        return False

    def run_comprehensive_test(self):
        """Run all tests in sequence focusing on user-reported issues"""
        print("🎯 FOCUS: Testing All User-Reported Issues After Main Agent Fixes")
        print("1. AI Chat functionality (POST /api/ai-chat, GET /api/ai-chat/history)")
        print("2. New scenario selection (POST /api/setup-scenario/{scenario_key})")
        print("3. Device/equipment addition (POST /api/properties/{property_id}/devices)")
        print("4. Property management (GET /api/properties)")
        print()
        
        # Test 1: Login as demo user (CRITICAL)
        login_success = self.test_demo_user_login()
        if not login_success:
            print("\n❌ CRITICAL FAILURE: Cannot proceed without demo user authentication")
            return self.results
        
        # Test 2: AI Chat functionality (USER REPORTED ISSUE)
        print("\n" + "="*60)
        print("🤖 TESTING AI CHAT FUNCTIONALITY (USER REPORTED ISSUE)")
        print("="*60)
        self.test_ai_chat_functionality()
        self.test_ai_chat_history()
        
        # Test 3: New scenario selection (USER REPORTED ISSUE)
        print("\n" + "="*60)
        print("🏠 TESTING NEW SCENARIO SELECTION (USER REPORTED ISSUE)")
        print("="*60)
        self.test_new_scenario_selection()
        
        # Test 4: Property management (USER REPORTED ISSUE)
        print("\n" + "="*60)
        print("🏢 TESTING PROPERTY MANAGEMENT (USER REPORTED ISSUE)")
        print("="*60)
        properties_exist = self.test_get_properties()
        
        # Test 5: Device/equipment addition (USER REPORTED ISSUE)
        print("\n" + "="*60)
        print("⚡ TESTING DEVICE/EQUIPMENT ADDITION (USER REPORTED ISSUE)")
        print("="*60)
        
        # Get a property ID for device testing
        property_id = None
        if properties_exist:
            # Try to get properties to find a property ID
            try:
                response = self.session.get(
                    f"{self.base_url}/properties",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    properties = data.get("properties", [])
                    if properties:
                        property_id = properties[0].get("id")
            except:
                pass
        
        # If no property exists, create one for testing
        if not property_id:
            print("No existing property found, creating one for device testing...")
            scenario_success, property_id = self.test_setup_family_home_scenario()
        
        # Test device addition
        self.test_device_equipment_addition(property_id)
        
        # Additional supporting tests
        print("\n" + "="*60)
        print("🔧 ADDITIONAL SUPPORTING TESTS")
        print("="*60)
        self.test_property_management_status()
        self.test_get_usage_scenarios()
        self.test_device_templates()
        
        # Generate comprehensive summary
        self.print_test_summary()
        
        return self.results

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        passed = self.results["passed"]
        total = self.results["total_tests"]
        success_rate = (passed/total)*100 if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical test results
        critical_tests = [
            "Demo User Login",
            "Setup Family Home Scenario", 
            "Get Properties"
        ]
        
        print("🔍 CRITICAL TEST RESULTS:")
        all_critical_passed = True
        for test_name in critical_tests:
            if test_name in self.results["critical_failures"]:
                print(f"  ❌ FAIL {test_name}")
                all_critical_passed = False
            else:
                # Check if test was run and passed
                test_run = any(test_name in error for error in self.results["errors"]) or passed > 0
                if test_run:
                    print(f"  ✅ PASS {test_name}")
                else:
                    print(f"  ⚠️  SKIP {test_name}")
        
        print()
        
        # User issue analysis
        print("🎯 USER-REPORTED ISSUES ANALYSIS:")
        print("Testing all issues reported by user after main agent fixes:")
        print("1. AI Chat functionality")
        print("2. New scenario selection") 
        print("3. Device/equipment addition")
        print("4. Property management")
        print()
        
        # Check status of each user-reported issue
        ai_chat_failed = "AI Chat Functionality Overall" in self.results["critical_failures"]
        scenario_failed = "New Scenario Selection Overall" in self.results["critical_failures"]
        device_failed = "Device Creation" in self.results["critical_failures"]
        properties_failed = "Get Properties" in self.results["critical_failures"]
        login_failed = "Demo User Login" in self.results["critical_failures"]
        
        if login_failed:
            print("❌ ROOT CAUSE: Demo user authentication is failing")
            print("   SOLUTION: Fix demo user credentials or login endpoint")
        else:
            # Analyze each issue
            print("📊 ISSUE-BY-ISSUE STATUS:")
            
            if not ai_chat_failed:
                print("  ✅ AI Chat functionality: WORKING")
            else:
                print("  ❌ AI Chat functionality: FAILING")
                print("     - Check EMERGENT_LLM_KEY configuration")
                print("     - Verify AI chat endpoints are properly implemented")
            
            if not scenario_failed:
                print("  ✅ New scenario selection: WORKING")
            else:
                print("  ❌ New scenario selection: FAILING")
                print("     - Check POST /api/setup-scenario/{scenario_key} endpoints")
                print("     - Verify scenario creation logic")
            
            if not properties_failed:
                print("  ✅ Property management: WORKING")
            else:
                print("  ❌ Property management: FAILING")
                print("     - Check GET /api/properties endpoint")
                print("     - Verify property retrieval logic")
            
            if not device_failed:
                print("  ✅ Device/equipment addition: WORKING")
            else:
                print("  ❌ Device/equipment addition: FAILING")
                print("     - Check POST /api/properties/{property_id}/devices endpoint")
                print("     - Verify ObjectId serialization issues are fixed")
        
        print()
        
        if self.results["errors"]:
            print("🐛 DETAILED ERRORS:")
            for error in self.results["errors"]:
                print(f"  • {error}")
            print()

def main():
    """Main test execution"""
    tester = EnergoBackendTester()
    results = tester.run_comprehensive_test()
    
    # Return appropriate exit code
    critical_failures = len(results["critical_failures"])
    if critical_failures == 0:
        print("🎉 All critical tests passed!")
        sys.exit(0)
    else:
        print(f"❌ {critical_failures} critical test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()