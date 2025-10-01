#!/usr/bin/env python3
"""
Device Management Testing Suite for Energo Smart Energy Management API
Testing specific user-reported issue: Cannot add new equipment/devices
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
print(f"⚡ Testing Device Management Endpoints at: {BASE_URL}")
print("Focus: Device creation and management - Cannot add new equipment/devices")
print("=" * 70)

# Demo user credentials
DEMO_USER = {
    "email": "demo@energo.com",
    "password": "password123"
}

class DeviceManagementTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_property_id = None
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

    def authenticate(self):
        """Authenticate with demo user"""
        print("\n🔐 Authenticating Demo User...")
        
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
                    self.log_result("Authentication", True, f"Logged in as {DEMO_USER['email']}")
                    return True
                else:
                    self.log_result("Authentication", False, "Missing token or user in response", is_critical=True)
            else:
                self.log_result("Authentication", False, f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}", is_critical=True)
        
        return False

    def get_device_templates(self):
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
                by_category = data.get("by_category", {})
                
                self.log_result("Get Device Templates", True, 
                              f"Found {len(common_devices)} common devices, {len(all_templates)} total templates, {len(by_category)} categories")
                
                # Show sample devices
                print("   Sample Common Devices:")
                for i, device in enumerate(common_devices[:5]):
                    print(f"     {i+1}. {device.get('name', 'Unknown')} ({device.get('device_type', 'N/A')})")
                    print(f"        Power: {device.get('power_rating_watts', 'N/A')}W, Usage: {device.get('daily_usage_hours', 'N/A')}h/day")
                
                return common_devices, all_templates
            else:
                self.log_result("Get Device Templates", False, f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("Get Device Templates", False, f"Exception: {str(e)}", is_critical=True)
        
        return [], []

    def get_user_properties(self):
        """Get user properties to test device creation"""
        print("\n🏠 Getting User Properties...")
        
        if not self.auth_token:
            self.log_result("Get User Properties", False, "No authentication token", is_critical=True)
            return []
        
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
                    self.test_property_id = properties[0].get("id")
                    self.log_result("Get User Properties", True, f"Found {len(properties)} properties. Using property: {self.test_property_id}")
                    
                    # Show property details
                    for i, prop in enumerate(properties[:3]):
                        print(f"   Property {i+1}: {prop.get('name', 'Unknown')} (ID: {prop.get('id', 'N/A')})")
                        print(f"      Address: {prop.get('address', 'N/A')}")
                        print(f"      Type: {prop.get('property_type', 'N/A')}, Size: {prop.get('size_m2', 'N/A')} m²")
                    
                    return properties
                else:
                    self.log_result("Get User Properties", False, "No properties found for user", is_critical=True)
            else:
                self.log_result("Get User Properties", False, f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("Get User Properties", False, f"Exception: {str(e)}", is_critical=True)
        
        return []

    def test_add_device_to_property(self, device_templates):
        """Test POST /api/properties/{property_id}/devices endpoint"""
        print(f"\n⚡ Testing Add Device to Property {self.test_property_id}...")
        
        if not self.test_property_id:
            self.log_result("Add Device to Property", False, "No test property available", is_critical=True)
            return False
        
        if not device_templates:
            self.log_result("Add Device to Property", False, "No device templates available", is_critical=True)
            return False
        
        # Test adding multiple devices
        successful_devices = 0
        test_devices = device_templates[:3]  # Test first 3 devices
        
        for i, template in enumerate(test_devices):
            device_name = f"Test {template.get('name', 'Device')} {i+1}"
            print(f"\n   Testing device {i+1}: {device_name}")
            
            device_data = {
                "template_id": template.get("id"),
                "name": device_name,
                "location": f"Test Room {i+1}",
                "custom_power_rating": template.get("power_rating_watts"),
                "custom_usage_hours": template.get("daily_usage_hours")
            }
            
            try:
                response = self.session.post(
                    f"{self.base_url}/properties/{self.test_property_id}/devices",
                    json=device_data,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=30
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    data = response.json()
                    device_id = data.get("device_id")
                    if device_id:
                        successful_devices += 1
                        print(f"   ✅ Device created successfully: {device_id}")
                        print(f"      Name: {device_name}")
                        print(f"      Template: {template.get('name', 'Unknown')}")
                    else:
                        print(f"   ❌ No device_id in response: {data}")
                else:
                    print(f"   ❌ Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
        
        success_rate = (successful_devices / len(test_devices)) * 100
        if successful_devices == len(test_devices):
            self.log_result("Add Device to Property", True, f"All {successful_devices} devices created successfully (100%)")
            return True
        elif successful_devices > 0:
            self.log_result("Add Device to Property", False, f"Only {successful_devices}/{len(test_devices)} devices created ({success_rate:.1f}%)")
        else:
            self.log_result("Add Device to Property", False, "No devices were created successfully", is_critical=True)
        
        return False

    def test_get_property_devices(self):
        """Test GET /api/properties/{property_id}/devices endpoint"""
        print(f"\n📋 Testing Get Property Devices for {self.test_property_id}...")
        
        if not self.test_property_id:
            self.log_result("Get Property Devices", False, "No test property available")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/properties/{self.test_property_id}/devices",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                devices = data.get("devices", [])
                
                if len(devices) > 0:
                    self.log_result("Get Property Devices", True, f"Found {len(devices)} devices in property")
                    
                    # Show device details
                    print("   Property Devices:")
                    for i, device in enumerate(devices[:5]):  # Show first 5 devices
                        print(f"     {i+1}. {device.get('name', 'Unknown')} ({device.get('device_type', 'N/A')})")
                        print(f"        ID: {device.get('id', 'N/A')}")
                        print(f"        Location: {device.get('location', 'N/A')}")
                        print(f"        Power: {device.get('power_rating_watts', 'N/A')}W")
                        print(f"        Usage: {device.get('daily_usage_hours', 'N/A')}h/day")
                    
                    return True
                else:
                    self.log_result("Get Property Devices", False, "No devices found in property")
            else:
                self.log_result("Get Property Devices", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Get Property Devices", False, f"Exception: {str(e)}")
        
        return False

    def test_device_categories(self):
        """Test device templates by category"""
        print("\n📂 Testing Device Categories...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/device-templates",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                by_category = data.get("by_category", {})
                
                if by_category:
                    self.log_result("Device Categories", True, f"Found {len(by_category)} device categories")
                    
                    # Show categories and device counts
                    print("   Device Categories:")
                    for category, devices in by_category.items():
                        print(f"     {category}: {len(devices)} devices")
                        # Show sample devices in category
                        for device in devices[:2]:  # Show first 2 devices per category
                            print(f"       - {device.get('name', 'Unknown')} ({device.get('power_rating_watts', 'N/A')}W)")
                    
                    return True
                else:
                    self.log_result("Device Categories", False, "No device categories found")
            else:
                self.log_result("Device Categories", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Device Categories", False, f"Exception: {str(e)}")
        
        return False

    def run_all_tests(self):
        """Run all device management tests"""
        print("🎯 FOCUS: Testing Device Management Functionality")
        print("This addresses the user's issue: 'Cannot add new equipment/devices'")
        print()
        
        # Test 1: Authentication (CRITICAL)
        auth_success = self.authenticate()
        if not auth_success:
            print("\n❌ CRITICAL FAILURE: Cannot proceed without authentication")
            return self.results
        
        # Test 2: Get device templates (CRITICAL)
        common_devices, all_templates = self.get_device_templates()
        
        # Test 3: Get device categories
        self.test_device_categories()
        
        # Test 4: Get user properties (CRITICAL)
        properties = self.get_user_properties()
        
        # Test 5: Add devices to property (CRITICAL)
        if properties and common_devices:
            self.test_add_device_to_property(common_devices)
            
            # Test 6: Get property devices
            self.test_get_property_devices()
        else:
            print("\n⚠️  Skipping device creation tests due to missing properties or templates")
        
        # Generate summary
        self.print_summary()
        
        return self.results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 DEVICE MANAGEMENT TEST SUMMARY")
        print("=" * 70)
        
        passed = self.results["passed"]
        total = self.results["total_tests"]
        success_rate = (passed/total)*100 if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical analysis
        print("🔍 DEVICE MANAGEMENT ISSUE ANALYSIS:")
        print("User Issue: 'Cannot add new equipment/devices'")
        print()
        
        auth_failed = "Authentication" in self.results["critical_failures"]
        templates_failed = "Get Device Templates" in self.results["critical_failures"]
        properties_failed = "Get User Properties" in self.results["critical_failures"]
        add_device_failed = "Add Device to Property" in self.results["critical_failures"]
        
        if auth_failed:
            print("❌ ROOT CAUSE: Demo user authentication is failing")
            print("   SOLUTION: Fix demo user credentials or login endpoint")
        elif templates_failed:
            print("❌ ROOT CAUSE: Device templates are not available")
            print("   SOLUTION: Fix device templates endpoint or ensure templates are loaded")
        elif properties_failed:
            print("❌ ROOT CAUSE: User has no properties to add devices to")
            print("   SOLUTION: Ensure users can create properties first")
        elif add_device_failed:
            print("❌ ROOT CAUSE: Device creation endpoint is failing")
            print("   SOLUTION: Fix POST /api/properties/{property_id}/devices endpoint")
        elif passed == total:
            print("✅ ISSUE RESOLVED: Device management is working correctly!")
            print("   Users can now add new equipment/devices to their properties")
            print("   Device templates are available and device creation is functional")
        else:
            print("⚠️  PARTIAL SUCCESS: Some device management features working, some failing")
            print("   Review individual test results above for specific issues")
        
        print()
        
        if self.results["errors"]:
            print("🐛 DETAILED ERRORS:")
            for error in self.results["errors"]:
                print(f"  • {error}")

def main():
    """Main test execution"""
    tester = DeviceManagementTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    critical_failures = len(results["critical_failures"])
    if critical_failures == 0:
        print("\n🎉 All critical device management tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {critical_failures} critical device management test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()