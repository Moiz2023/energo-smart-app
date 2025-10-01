#!/usr/bin/env python3
"""
AI Chat Testing Suite for Energo Smart Energy Management API
Testing specific user-reported issue: AI Chat not working
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
print(f"🤖 Testing AI Chat Endpoints at: {BASE_URL}")
print("Focus: AI Chat functionality - POST /api/ai-chat and GET /api/ai-chat/history")
print("=" * 70)

# Demo user credentials
DEMO_USER = {
    "email": "demo@energo.com",
    "password": "password123"
}

class AIChatTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.session_id = None
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

    def check_emergent_llm_key(self):
        """Check if EMERGENT_LLM_KEY is configured by testing a simple AI chat"""
        print("\n🔑 Checking EMERGENT_LLM_KEY Configuration...")
        
        if not self.auth_token:
            self.log_result("EMERGENT_LLM_KEY Check", False, "No authentication token", is_critical=True)
            return False
        
        test_message = {
            "message": "Hello, this is a test message to check if AI is working.",
            "session_id": None
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/ai-chat",
                json=test_message,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "session_id" in data:
                    self.session_id = data["session_id"]
                    ai_response = data["response"]
                    self.log_result("EMERGENT_LLM_KEY Check", True, f"AI responded successfully. Session: {self.session_id}")
                    print(f"   AI Response: {ai_response[:100]}...")
                    return True
                else:
                    self.log_result("EMERGENT_LLM_KEY Check", False, "Missing response or session_id in response", is_critical=True)
            elif response.status_code == 500:
                error_text = response.text
                if "AI service unavailable" in error_text or "EMERGENT_LLM_KEY" in error_text:
                    self.log_result("EMERGENT_LLM_KEY Check", False, "EMERGENT_LLM_KEY not configured or AI service unavailable", is_critical=True)
                else:
                    self.log_result("EMERGENT_LLM_KEY Check", False, f"Server error: {error_text}", is_critical=True)
            else:
                self.log_result("EMERGENT_LLM_KEY Check", False, f"Status: {response.status_code}, Response: {response.text}", is_critical=True)
                
        except Exception as e:
            self.log_result("EMERGENT_LLM_KEY Check", False, f"Exception: {str(e)}", is_critical=True)
        
        return False

    def test_ai_chat_conversation(self):
        """Test a full AI chat conversation with multiple messages"""
        print("\n💬 Testing AI Chat Conversation...")
        
        if not self.auth_token:
            self.log_result("AI Chat Conversation", False, "No authentication token", is_critical=True)
            return False
        
        # Test messages covering different energy topics
        test_messages = [
            "Can you help me reduce my energy consumption?",
            "What are the best energy-saving tips for a family home?",
            "Tell me about energy subsidies available in Brussels.",
            "How can I optimize my heating costs?",
            "What's the best time to use appliances to save money?"
        ]
        
        successful_messages = 0
        
        for i, message in enumerate(test_messages):
            print(f"\n   Testing message {i+1}: '{message[:50]}...'")
            
            chat_data = {
                "message": message,
                "session_id": self.session_id  # Use same session for continuity
            }
            
            try:
                response = self.session.post(
                    f"{self.base_url}/ai-chat",
                    json=chat_data,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "response" in data:
                        ai_response = data["response"]
                        session_id = data.get("session_id", "N/A")
                        successful_messages += 1
                        print(f"   ✅ AI Response ({len(ai_response)} chars): {ai_response[:80]}...")
                        print(f"   Session ID: {session_id}")
                        
                        # Update session ID for continuity
                        if session_id != "N/A":
                            self.session_id = session_id
                    else:
                        print(f"   ❌ Missing response in data: {data}")
                else:
                    print(f"   ❌ Status: {response.status_code}, Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
        
        success_rate = (successful_messages / len(test_messages)) * 100
        if successful_messages == len(test_messages):
            self.log_result("AI Chat Conversation", True, f"All {successful_messages} messages successful (100%)")
            return True
        elif successful_messages > 0:
            self.log_result("AI Chat Conversation", False, f"Only {successful_messages}/{len(test_messages)} messages successful ({success_rate:.1f}%)")
        else:
            self.log_result("AI Chat Conversation", False, "No messages were successful", is_critical=True)
        
        return False

    def test_chat_history(self):
        """Test GET /api/ai-chat/history endpoint"""
        print("\n📜 Testing Chat History Retrieval...")
        
        if not self.auth_token:
            self.log_result("Chat History", False, "No authentication token")
            return False
        
        try:
            # Test getting all chat history
            response = self.session.get(
                f"{self.base_url}/ai-chat/history",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "chat_history" in data:
                    history = data["chat_history"]
                    self.log_result("Chat History", True, f"Retrieved {len(history)} chat history items")
                    
                    # Show sample history items
                    for i, item in enumerate(history[:3]):  # Show first 3 items
                        print(f"   History {i+1}: {item.get('message', 'N/A')[:50]}...")
                        print(f"      Response: {item.get('response', 'N/A')[:50]}...")
                        print(f"      Session: {item.get('session_id', 'N/A')}")
                        print(f"      Timestamp: {item.get('timestamp', 'N/A')}")
                    
                    # Test getting history for specific session
                    if self.session_id:
                        print(f"\n   Testing history for session {self.session_id}...")
                        session_response = self.session.get(
                            f"{self.base_url}/ai-chat/history?session_id={self.session_id}",
                            headers={"Authorization": f"Bearer {self.auth_token}"},
                            timeout=30
                        )
                        
                        if session_response.status_code == 200:
                            session_data = session_response.json()
                            session_history = session_data.get("chat_history", [])
                            print(f"   ✅ Session-specific history: {len(session_history)} items")
                        else:
                            print(f"   ❌ Session history failed: {session_response.status_code}")
                    
                    return True
                else:
                    self.log_result("Chat History", False, "Missing chat_history in response")
            else:
                self.log_result("Chat History", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Chat History", False, f"Exception: {str(e)}")
        
        return False

    def test_premium_features(self):
        """Test premium AI chat features"""
        print("\n💎 Testing Premium AI Chat Features...")
        
        if not self.auth_token:
            self.log_result("Premium Features", False, "No authentication token")
            return False
        
        # First check user's subscription status
        try:
            settings_response = self.session.get(
                f"{self.base_url}/settings",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if settings_response.status_code == 200:
                settings_data = settings_response.json()
                subscription_plan = settings_data.get("settings", {}).get("subscription_plan", "free")
                print(f"   User subscription: {subscription_plan}")
                
                # Test premium-specific AI features
                premium_message = {
                    "message": "Can you provide real-time energy data and advanced analysis for my consumption patterns?",
                    "session_id": self.session_id
                }
                
                response = self.session.post(
                    f"{self.base_url}/ai-chat",
                    json=premium_message,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("response", "")
                    
                    # Check if response includes premium features
                    has_real_time_data = "real-time" in ai_response.lower() or "fluvius" in ai_response.lower()
                    has_advanced_analysis = len(ai_response) > 200  # Premium responses should be more detailed
                    
                    if subscription_plan == "premium" and (has_real_time_data or has_advanced_analysis):
                        self.log_result("Premium Features", True, f"Premium AI features working (subscription: {subscription_plan})")
                        print(f"   Premium response length: {len(ai_response)} chars")
                    elif subscription_plan == "free":
                        self.log_result("Premium Features", True, f"Free tier working correctly (subscription: {subscription_plan})")
                    else:
                        self.log_result("Premium Features", False, f"Premium features not working as expected (subscription: {subscription_plan})")
                else:
                    self.log_result("Premium Features", False, f"Premium message failed: {response.status_code}")
            else:
                self.log_result("Premium Features", False, f"Could not get user settings: {settings_response.status_code}")
                
        except Exception as e:
            self.log_result("Premium Features", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all AI chat tests"""
        print("🎯 FOCUS: Testing AI Chat Functionality")
        print("This addresses the user's issue: 'AI Chat not working'")
        print()
        
        # Test 1: Authentication (CRITICAL)
        auth_success = self.authenticate()
        if not auth_success:
            print("\n❌ CRITICAL FAILURE: Cannot proceed without authentication")
            return self.results
        
        # Test 2: Check EMERGENT_LLM_KEY configuration (CRITICAL)
        key_configured = self.check_emergent_llm_key()
        
        # Test 3: Full conversation test
        if key_configured:
            self.test_ai_chat_conversation()
            
            # Test 4: Chat history
            self.test_chat_history()
            
            # Test 5: Premium features
            self.test_premium_features()
        else:
            print("\n⚠️  Skipping conversation tests due to AI service unavailability")
        
        # Generate summary
        self.print_summary()
        
        return self.results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 AI CHAT TEST SUMMARY")
        print("=" * 70)
        
        passed = self.results["passed"]
        total = self.results["total_tests"]
        success_rate = (passed/total)*100 if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical analysis
        print("🔍 AI CHAT ISSUE ANALYSIS:")
        print("User Issue: 'AI Chat not working'")
        print()
        
        key_failed = "EMERGENT_LLM_KEY Check" in self.results["critical_failures"]
        auth_failed = "Authentication" in self.results["critical_failures"]
        
        if auth_failed:
            print("❌ ROOT CAUSE: Demo user authentication is failing")
            print("   SOLUTION: Fix demo user credentials or login endpoint")
        elif key_failed:
            print("❌ ROOT CAUSE: EMERGENT_LLM_KEY is not configured or AI service is unavailable")
            print("   SOLUTION: Configure EMERGENT_LLM_KEY environment variable in backend")
            print("   DETAILS: The AI chat endpoints exist but cannot connect to the LLM service")
        elif passed == total:
            print("✅ ISSUE RESOLVED: AI Chat is working correctly!")
            print("   Users can now use the AI chat feature successfully")
            print("   Both chat messaging and history retrieval are functional")
        else:
            print("⚠️  PARTIAL SUCCESS: Some AI chat features working, some failing")
            print("   Review individual test results above for specific issues")
        
        print()
        
        if self.results["errors"]:
            print("🐛 DETAILED ERRORS:")
            for error in self.results["errors"]:
                print(f"  • {error}")

def main():
    """Main test execution"""
    tester = AIChatTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    critical_failures = len(results["critical_failures"])
    if critical_failures == 0:
        print("\n🎉 All critical AI chat tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {critical_failures} critical AI chat test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()