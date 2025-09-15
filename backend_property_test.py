#!/usr/bin/env python3
"""
Property & Device Management Backend Testing for Energo Smart App
Tests the newly implemented Property & Device Management backend endpoints as requested:

1. Device Templates & Scenarios endpoints
2. Property Management CRUD operations  
3. Device Management operations
4. Advanced Features like setup-scenario, CSV upload, consumption analysis
5. Mock Data & Analysis functionality

Test Flow:
1. Create a property
2. Setup with a scenario (e.g., "family" or "ev_owner")
3. Add/modify devices
4. Get property details with analysis
5. Test CSV upload functionality
"""

import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta
import uuid

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
print(f"Testing Property Management at: {BASE_URL}")

class PropertyManagementTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.demo_user_email = "demo@energo.com"
        self.demo_user_password = "password123"
        self.property_id = None
        self.device_id = None
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

    def authenticate_demo_user(self):
        """Authenticate with demo user to get auth token"""
        print("\n🔐 Authenticating Demo User...")
        
        login_data = {
            "email": self.demo_user_email,
            "password": self.demo_user_password
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
                if "token" in data:
                    self.auth_token = data["token"]
                    self.log_result("Demo User Authentication", True, "Successfully authenticated")
                    return True
                else:
                    self.log_result("Demo User Authentication", False, "No token in response")
            else:
                self.log_result("Demo User Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Demo User Authentication", False, f"Exception: {str(e)}")
            
        return False

    def test_property_management_status(self):
        """Test if property management features are enabled"""
        print("\n🏠 Testing Property Management Status...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/property-management-status",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("enabled", False):
                    self.log_result("Property Management Status", True, "Property management features are enabled")
                    return True
                else:
                    self.log_result("Property Management Status", False, f"Property management disabled: {data.get('message', 'Unknown')}")
            else:
                self.log_result("Property Management Status", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Property Management Status", False, f"Exception: {str(e)}")
            
        return False

    def test_device_templates(self):
        """Test GET /api/device-templates endpoint"""
        print("\n📱 Testing Device Templates Endpoint...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/device-templates",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "common_devices" in data and isinstance(data["common_devices"], list):
                    device_count = len(data["common_devices"])
                    self.log_result("Device Templates", True, f"Retrieved {device_count} common devices")
                    
                    # Check if we have categories
                    if "by_category" in data:
                        category_count = len(data["by_category"])
                        print(f"  📂 Found {category_count} device categories")
                    
                    return True
                else:
                    self.log_result("Device Templates", False, "Missing or invalid common_devices in response")
            else:
                self.log_result("Device Templates", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Device Templates", False, f"Exception: {str(e)}")
            
        return False

    def test_usage_scenarios(self):
        """Test GET /api/usage-scenarios endpoint"""
        print("\n🏘️ Testing Usage Scenarios Endpoint...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/usage-scenarios",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "scenarios" in data and isinstance(data["scenarios"], dict):
                    scenario_count = len(data["scenarios"])
                    self.log_result("Usage Scenarios", True, f"Retrieved {scenario_count} usage scenarios")
                    
                    # Print scenario details
                    for scenario_key, scenario_info in data["scenarios"].items():
                        print(f"  🏠 {scenario_key}: {scenario_info.get('name', 'Unknown')}")
                    
                    return True
                else:
                    self.log_result("Usage Scenarios", False, "Missing or invalid scenarios in response")
            else:
                self.log_result("Usage Scenarios", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Usage Scenarios", False, f"Exception: {str(e)}")
            
        return False

    def test_create_property(self):
        """Test POST /api/properties endpoint"""
        print("\n🏗️ Testing Create Property...")
        
        if not self.auth_token:
            self.log_result("Create Property", False, "No auth token available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        property_data = {
            "name": "Test Family Home",
            "address": "123 Test Street, Brussels, Belgium",
            "property_type": "house",
            "size_m2": 150.0,
            "bedrooms": 3,
            "occupants": 4,
            "construction_year": 1995,
            "energy_label": "C",
            "heating_type": "gas",
            "meter_id": f"TEST_METER_{int(time.time())}"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/properties",
                json=property_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if "id" in data:
                    self.property_id = data["id"]
                    self.log_result("Create Property", True, f"Property created with ID: {self.property_id}")
                    return True
                else:
                    self.log_result("Create Property", False, "No property ID in response")
            else:
                self.log_result("Create Property", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Create Property", False, f"Exception: {str(e)}")
            
        return False

    def test_get_user_properties(self):
        """Test GET /api/properties endpoint"""
        print("\n📋 Testing Get User Properties...")
        
        if not self.auth_token:
            self.log_result("Get User Properties", False, "No auth token available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/properties",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    property_count = len(data)
                    self.log_result("Get User Properties", True, f"Retrieved {property_count} properties")
                    
                    # If we have properties, use the first one if we don't have a property_id yet
                    if property_count > 0 and not self.property_id:
                        self.property_id = data[0].get("id")
                        print(f"  🏠 Using property ID: {self.property_id}")
                    
                    return True
                else:
                    self.log_result("Get User Properties", False, "Response is not a list")
            else:
                self.log_result("Get User Properties", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Get User Properties", False, f"Exception: {str(e)}")
            
        return False

    def test_setup_scenario(self):
        """Test POST /api/properties/{property_id}/setup-scenario endpoint"""
        print("\n🎭 Testing Setup Property Scenario...")
        
        if not self.auth_token or not self.property_id:
            self.log_result("Setup Scenario", False, "No auth token or property ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        scenario_data = {
            "scenario": "family",
            "generate_mock_data": True
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/properties/{self.property_id}/setup-scenario",
                json=scenario_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if "devices_created" in data:
                    devices_created = data["devices_created"]
                    scenario_name = data.get("scenario", {}).get("name", "Unknown")
                    self.log_result("Setup Scenario", True, f"Set up '{scenario_name}' scenario with {devices_created} devices")
                    return True
                else:
                    self.log_result("Setup Scenario", False, "Missing devices_created in response")
            else:
                self.log_result("Setup Scenario", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Setup Scenario", False, f"Exception: {str(e)}")
            
        return False

    def test_add_device(self):
        """Test POST /api/properties/{property_id}/devices endpoint"""
        print("\n🔌 Testing Add Device to Property...")
        
        if not self.auth_token or not self.property_id:
            self.log_result("Add Device", False, "No auth token or property ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        device_data = {
            "name": "Test Smart TV",
            "device_type": "entertainment",
            "brand": "Samsung",
            "model": "QE55Q80A",
            "power_rating_watts": 150,
            "usage_hours_per_day": 6.0,
            "location": "Living Room",
            "purchase_date": "2023-01-15",
            "energy_efficiency_class": "A"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/properties/{self.property_id}/devices",
                json=device_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if "id" in data:
                    self.device_id = data["id"]
                    device_name = data.get("name", "Unknown")
                    self.log_result("Add Device", True, f"Device '{device_name}' added with ID: {self.device_id}")
                    return True
                else:
                    self.log_result("Add Device", False, "No device ID in response")
            else:
                self.log_result("Add Device", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Add Device", False, f"Exception: {str(e)}")
            
        return False

    def test_get_property_devices(self):
        """Test GET /api/properties/{property_id}/devices endpoint"""
        print("\n📱 Testing Get Property Devices...")
        
        if not self.auth_token or not self.property_id:
            self.log_result("Get Property Devices", False, "No auth token or property ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/properties/{self.property_id}/devices",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    device_count = len(data)
                    self.log_result("Get Property Devices", True, f"Retrieved {device_count} devices")
                    
                    # If we don't have a device_id yet, use the first device
                    if device_count > 0 and not self.device_id:
                        self.device_id = data[0].get("id")
                        print(f"  🔌 Using device ID: {self.device_id}")
                    
                    return True
                else:
                    self.log_result("Get Property Devices", False, "Response is not a list")
            else:
                self.log_result("Get Property Devices", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Get Property Devices", False, f"Exception: {str(e)}")
            
        return False

    def test_update_device(self):
        """Test PUT /api/properties/{property_id}/devices/{device_id} endpoint"""
        print("\n✏️ Testing Update Device...")
        
        if not self.auth_token or not self.property_id or not self.device_id:
            self.log_result("Update Device", False, "Missing auth token, property ID, or device ID")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        update_data = {
            "usage_hours_per_day": 8.0,
            "location": "Master Bedroom",
            "notes": "Moved to bedroom, increased usage"
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/properties/{self.property_id}/devices/{self.device_id}",
                json=update_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "device" in data and "message" in data:
                    updated_device = data["device"]
                    new_usage = updated_device.get("usage_hours_per_day", 0)
                    self.log_result("Update Device", True, f"Device updated - new usage: {new_usage} hours/day")
                    return True
                else:
                    self.log_result("Update Device", False, "Missing device or message in response")
            else:
                self.log_result("Update Device", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Update Device", False, f"Exception: {str(e)}")
            
        return False

    def test_get_property_details(self):
        """Test GET /api/properties/{property_id} endpoint with analysis"""
        print("\n🔍 Testing Get Property Details with Analysis...")
        
        if not self.auth_token or not self.property_id:
            self.log_result("Get Property Details", False, "No auth token or property ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/properties/{self.property_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                required_keys = ["property", "devices", "summary"]
                
                if all(key in data for key in required_keys):
                    property_info = data["property"]
                    devices = data["devices"]
                    summary = data["summary"]
                    
                    device_count = len(devices)
                    total_readings = summary.get("total_readings", 0)
                    has_mock_data = summary.get("has_mock_data", False)
                    
                    self.log_result("Get Property Details", True, 
                                  f"Property: {property_info.get('name', 'Unknown')}, "
                                  f"Devices: {device_count}, Readings: {total_readings}, "
                                  f"Mock Data: {has_mock_data}")
                    
                    # Check for analysis data
                    if "device_estimates" in data:
                        estimates_count = len(data["device_estimates"])
                        print(f"  📊 Device consumption estimates: {estimates_count}")
                    
                    if "alerts" in data:
                        alerts_count = len(data["alerts"])
                        print(f"  🚨 Alerts generated: {alerts_count}")
                    
                    return True
                else:
                    missing_keys = [key for key in required_keys if key not in data]
                    self.log_result("Get Property Details", False, f"Missing keys: {missing_keys}")
            else:
                self.log_result("Get Property Details", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Get Property Details", False, f"Exception: {str(e)}")
            
        return False

    def test_csv_upload(self):
        """Test POST /api/properties/{property_id}/upload-csv endpoint"""
        print("\n📄 Testing CSV Upload...")
        
        if not self.auth_token or not self.property_id:
            self.log_result("CSV Upload", False, "No auth token or property ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        # Generate sample CSV data
        csv_content = "timestamp,consumption_kwh,production_kwh\n"
        base_time = datetime.utcnow() - timedelta(days=7)
        
        for i in range(168):  # 1 week of hourly data
            timestamp = base_time + timedelta(hours=i)
            consumption = round(0.5 + (i % 24) * 0.1, 2)  # Realistic hourly pattern
            production = round(max(0, (i % 24 - 6) * 0.05), 2) if 6 <= i % 24 <= 18 else 0  # Solar production
            csv_content += f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')},{consumption},{production}\n"
        
        file_data = {
            "csv_content": csv_content,
            "data_format": "hourly"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/properties/{self.property_id}/upload-csv",
                json=file_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if "readings_imported" in data:
                    readings_imported = data["readings_imported"]
                    data_format = data.get("data_format", "unknown")
                    self.log_result("CSV Upload", True, f"Imported {readings_imported} {data_format} readings")
                    return True
                else:
                    self.log_result("CSV Upload", False, "Missing readings_imported in response")
            else:
                self.log_result("CSV Upload", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("CSV Upload", False, f"Exception: {str(e)}")
            
        return False

    def test_delete_device(self):
        """Test DELETE /api/properties/{property_id}/devices/{device_id} endpoint (soft delete)"""
        print("\n🗑️ Testing Delete Device (Soft Delete)...")
        
        if not self.auth_token or not self.property_id or not self.device_id:
            self.log_result("Delete Device", False, "Missing auth token, property ID, or device ID")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.delete(
                f"{self.base_url}/properties/{self.property_id}/devices/{self.device_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_result("Delete Device", True, "Device soft deleted successfully")
                    return True
                else:
                    self.log_result("Delete Device", False, "Missing message in response")
            else:
                self.log_result("Delete Device", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Delete Device", False, f"Exception: {str(e)}")
            
        return False

    def run_all_tests(self):
        """Run all property management tests"""
        print("🏠 Starting Property & Device Management Testing")
        print("=" * 70)
        print("Testing areas as requested:")
        print("1. Device Templates & Scenarios")
        print("2. Property Management CRUD")
        print("3. Device Management")
        print("4. Advanced Features (setup-scenario, CSV upload)")
        print("5. Mock Data & Analysis")
        print("=" * 70)
        
        # Step 0: Authenticate
        if not self.authenticate_demo_user():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 1: Test property management status
        self.test_property_management_status()
        
        # Step 2: Test device templates and scenarios
        self.test_device_templates()
        self.test_usage_scenarios()
        
        # Step 3: Test property CRUD
        self.test_create_property()
        self.test_get_user_properties()
        
        # Step 4: Test scenario setup (creates devices and mock data)
        if self.property_id:
            self.test_setup_scenario()
        
        # Step 5: Test device management
        if self.property_id:
            self.test_add_device()
            self.test_get_property_devices()
            
            if self.device_id:
                self.test_update_device()
        
        # Step 6: Test property details with analysis
        if self.property_id:
            self.test_get_property_details()
        
        # Step 7: Test CSV upload
        if self.property_id:
            self.test_csv_upload()
        
        # Step 8: Test device deletion (soft delete)
        if self.property_id and self.device_id:
            self.test_delete_device()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📋 PROPERTY MANAGEMENT TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        
        if self.results['errors']:
            print("\n❌ FAILED TESTS:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Test flow summary
        print("\n🎯 TEST FLOW COMPLETION:")
        if self.property_id:
            print(f"✅ Property created: {self.property_id}")
        else:
            print("❌ Property creation failed")
            
        if success_rate >= 80:
            print("🎉 Property & Device Management features are working well!")
        elif success_rate >= 60:
            print("⚠️  Property & Device Management has some issues")
        else:
            print("🚨 Property & Device Management has significant issues")
            
        return success_rate >= 80

if __name__ == "__main__":
    tester = PropertyManagementTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)