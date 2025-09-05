#!/usr/bin/env python3
"""
Quick dashboard test to debug the issue
"""

import requests
import json

BASE_URL = "https://energo-fix.preview.emergentagent.com/api"

# First login to get token
login_data = {
    "email": "sarah.johnson@energotest.com",
    "password": "SecurePass123!"
}

print("Logging in...")
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Login status: {response.status_code}")

if response.status_code == 200:
    token = response.json()["token"]
    print(f"Got token: {token[:20]}...")
    
    # Test dashboard
    headers = {"Authorization": f"Bearer {token}"}
    print("\nTesting dashboard...")
    dashboard_response = requests.get(f"{BASE_URL}/dashboard", headers=headers)
    print(f"Dashboard status: {dashboard_response.status_code}")
    print(f"Dashboard response: {dashboard_response.text}")
else:
    print(f"Login failed: {response.text}")