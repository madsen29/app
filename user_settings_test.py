#!/usr/bin/env python3
"""
User Settings Management API Testing
Tests the new user settings management endpoints that were just implemented:

1. PUT /api/auth/profile - Test updating user profile information including:
   - Personal information (firstName, lastName, email)
   - Company information (companyName, streetAddress, city, state, postalCode, countryCode)
   - Email uniqueness validation
   - Field validation and error handling

2. PUT /api/auth/password - Test password update functionality including:
   - Current password verification
   - New password validation
   - Password change success

3. Complete User Settings Workflow:
   - Create a test user
   - Update their profile information
   - Change their password
   - Verify all changes are persisted correctly

4. Error Handling:
   - Test with invalid current password
   - Test with duplicate email
   - Test with missing required fields
"""

import requests
import json
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://cd63a717-b5ed-4c4d-b9fe-b518396e7591.preview.emergentagent.com/api"

class UserSettingsTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.test_user_token = None
        self.test_user_email = f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        self.test_user_password = "TestPassword123!"
        self.test_user_id = None
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_api_health(self):
        """Test if API is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_test("API Health Check", True, "API is accessible")
                return True
            else:
                self.log_test("API Health Check", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Failed to connect to API: {str(e)}")
            return False
    
    def create_test_user(self):
        """Create a test user for testing"""
        try:
            user_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "firstName": "John",
                "lastName": "Doe",
                "companyName": "Test Company Inc",
                "streetAddress": "123 Test Street",
                "city": "Test City",
                "state": "CA",
                "postalCode": "12345",
                "countryCode": "US"
            }
            
            response = self.session.post(f"{self.base_url}/auth/register", json=user_data)
            
            if response.status_code == 200:
                user_info = response.json()
                self.test_user_id = user_info.get('id')
                self.log_test("Create Test User", True, f"Test user created successfully with ID: {self.test_user_id}")
                return True
            else:
                self.log_test("Create Test User", False, f"Failed to create user: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Test User", False, f"Exception creating user: {str(e)}")
            return False
    
    def login_test_user(self):
        """Login the test user to get authentication token"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.test_user_token = token_data.get('access_token')
                # Set authorization header for future requests
                self.session.headers.update({'Authorization': f'Bearer {self.test_user_token}'})
                self.log_test("Login Test User", True, "Test user logged in successfully")
                return True
            else:
                self.log_test("Login Test User", False, f"Failed to login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Login Test User", False, f"Exception during login: {str(e)}")
            return False
    
    def test_get_current_user(self):
        """Test getting current user information"""
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            
            if response.status_code == 200:
                user_data = response.json()
                expected_fields = ['id', 'email', 'first_name', 'last_name', 'company_name', 'street_address', 'city', 'state', 'postal_code', 'country_code']
                
                missing_fields = [field for field in expected_fields if field not in user_data]
                if missing_fields:
                    self.log_test("Get Current User", False, f"Missing fields in user data: {missing_fields}")
                    return False
                
                if user_data['email'] != self.test_user_email:
                    self.log_test("Get Current User", False, f"Email mismatch: expected {self.test_user_email}, got {user_data['email']}")
                    return False
                
                self.log_test("Get Current User", True, "Current user information retrieved successfully")
                return True
            else:
                self.log_test("Get Current User", False, f"Failed to get user info: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Current User", False, f"Exception getting user info: {str(e)}")
            return False
    
    def test_update_profile_personal_info(self):
        """Test updating personal information (firstName, lastName)"""
        try:
            update_data = {
                "firstName": "Jane",
                "lastName": "Smith"
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", json=update_data)
            
            if response.status_code == 200:
                updated_user = response.json()
                
                if updated_user['first_name'] != "Jane" or updated_user['last_name'] != "Smith":
                    self.log_test("Update Personal Info", False, f"Personal info not updated correctly: {updated_user['first_name']} {updated_user['last_name']}")
                    return False
                
                self.log_test("Update Personal Info", True, "Personal information updated successfully")
                return True
            else:
                self.log_test("Update Personal Info", False, f"Failed to update personal info: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Personal Info", False, f"Exception updating personal info: {str(e)}")
            return False
    
    def test_update_profile_company_info(self):
        """Test updating company information"""
        try:
            update_data = {
                "companyName": "Updated Company LLC",
                "streetAddress": "456 Updated Avenue",
                "city": "New City",
                "state": "NY",
                "postalCode": "54321",
                "countryCode": "US"
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", json=update_data)
            
            if response.status_code == 200:
                updated_user = response.json()
                
                # Verify all company fields were updated
                if (updated_user['company_name'] != "Updated Company LLC" or
                    updated_user['street_address'] != "456 Updated Avenue" or
                    updated_user['city'] != "New City" or
                    updated_user['state'] != "NY" or
                    updated_user['postal_code'] != "54321"):
                    self.log_test("Update Company Info", False, f"Company info not updated correctly")
                    return False
                
                self.log_test("Update Company Info", True, "Company information updated successfully")
                return True
            else:
                self.log_test("Update Company Info", False, f"Failed to update company info: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Company Info", False, f"Exception updating company info: {str(e)}")
            return False
    
    def test_update_profile_email(self):
        """Test updating email address"""
        try:
            new_email = f"updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
            update_data = {
                "email": new_email
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", json=update_data)
            
            if response.status_code == 200:
                updated_user = response.json()
                
                if updated_user['email'] != new_email:
                    self.log_test("Update Email", False, f"Email not updated correctly: expected {new_email}, got {updated_user['email']}")
                    return False
                
                # Update our test email for future tests
                self.test_user_email = new_email
                
                self.log_test("Update Email", True, "Email updated successfully")
                return True
            else:
                self.log_test("Update Email", False, f"Failed to update email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Email", False, f"Exception updating email: {str(e)}")
            return False
    
    def test_email_uniqueness_validation(self):
        """Test email uniqueness validation by trying to use an existing email"""
        try:
            # First create another user using a new session (without auth)
            temp_session = requests.Session()
            another_user_email = f"another_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
            user_data = {
                "email": another_user_email,
                "password": "AnotherPassword123!",
                "firstName": "Another",
                "lastName": "User"
            }
            
            create_response = temp_session.post(f"{self.base_url}/auth/register", json=user_data)
            if create_response.status_code != 200:
                self.log_test("Email Uniqueness Validation", False, "Failed to create second user for testing")
                return False
            
            # Refresh token if needed
            if not self.refresh_auth_token():
                self.log_test("Email Uniqueness Validation", False, "Failed to refresh authentication token")
                return False
            
            # Now try to update our test user's email to the same email
            update_data = {
                "email": another_user_email
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", json=update_data)
            
            if response.status_code == 400:
                response_data = response.json()
                if "already registered" in response_data.get('detail', '').lower():
                    self.log_test("Email Uniqueness Validation", True, "Email uniqueness validation working correctly")
                    return True
                else:
                    self.log_test("Email Uniqueness Validation", False, f"Wrong error message: {response_data.get('detail')}")
                    return False
            elif response.status_code == 401:
                self.log_test("Email Uniqueness Validation", False, f"Authentication failed - token may have expired: {response.text}")
                return False
            else:
                self.log_test("Email Uniqueness Validation", False, f"Expected 400 error, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Email Uniqueness Validation", False, f"Exception testing email uniqueness: {str(e)}")
            return False
    
    def refresh_auth_token(self):
        """Refresh authentication token if needed"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            # Use a temporary session without auth header
            temp_session = requests.Session()
            response = temp_session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.test_user_token = token_data.get('access_token')
                # Update authorization header
                self.session.headers.update({'Authorization': f'Bearer {self.test_user_token}'})
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def test_update_profile_empty_request(self):
        """Test updating profile with empty request (should fail)"""
        try:
            # Refresh token if needed
            if not self.refresh_auth_token():
                self.log_test("Empty Profile Update", False, "Failed to refresh authentication token")
                return False
                
            update_data = {}
            
            response = self.session.put(f"{self.base_url}/auth/profile", json=update_data)
            
            if response.status_code == 400:
                response_data = response.json()
                if "no valid fields" in response_data.get('detail', '').lower():
                    self.log_test("Empty Profile Update", True, "Empty profile update correctly rejected")
                    return True
                else:
                    self.log_test("Empty Profile Update", False, f"Wrong error message: {response_data.get('detail')}")
                    return False
            elif response.status_code == 401:
                self.log_test("Empty Profile Update", False, f"Authentication failed: {response.text}")
                return False
            else:
                self.log_test("Empty Profile Update", False, f"Expected 400 error, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Empty Profile Update", False, f"Exception testing empty profile update: {str(e)}")
            return False
    
    def test_update_password_success(self):
        """Test successful password update"""
        try:
            # Refresh token if needed
            if not self.refresh_auth_token():
                self.log_test("Password Update Success", False, "Failed to refresh authentication token")
                return False
                
            new_password = "NewTestPassword456!"
            update_data = {
                "currentPassword": self.test_user_password,
                "newPassword": new_password
            }
            
            response = self.session.put(f"{self.base_url}/auth/password", json=update_data)
            
            if response.status_code == 200:
                response_data = response.json()
                if "successfully" in response_data.get('message', '').lower():
                    # Update our stored password
                    self.test_user_password = new_password
                    self.log_test("Password Update Success", True, "Password updated successfully")
                    return True
                else:
                    self.log_test("Password Update Success", False, f"Unexpected response message: {response_data.get('message')}")
                    return False
            elif response.status_code == 401:
                self.log_test("Password Update Success", False, f"Authentication failed: {response.text}")
                return False
            else:
                self.log_test("Password Update Success", False, f"Failed to update password: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Password Update Success", False, f"Exception updating password: {str(e)}")
            return False
    
    def test_update_password_wrong_current(self):
        """Test password update with wrong current password"""
        try:
            # Refresh token if needed
            if not self.refresh_auth_token():
                self.log_test("Wrong Current Password", False, "Failed to refresh authentication token")
                return False
                
            update_data = {
                "currentPassword": "WrongPassword123!",
                "newPassword": "AnotherNewPassword789!"
            }
            
            response = self.session.put(f"{self.base_url}/auth/password", json=update_data)
            
            if response.status_code == 400:
                response_data = response.json()
                if "incorrect" in response_data.get('detail', '').lower():
                    self.log_test("Wrong Current Password", True, "Wrong current password correctly rejected")
                    return True
                else:
                    self.log_test("Wrong Current Password", False, f"Wrong error message: {response_data.get('detail')}")
                    return False
            elif response.status_code == 401:
                self.log_test("Wrong Current Password", False, f"Authentication failed: {response.text}")
                return False
            else:
                self.log_test("Wrong Current Password", False, f"Expected 400 error, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Wrong Current Password", False, f"Exception testing wrong current password: {str(e)}")
            return False
    
    def test_login_with_new_password(self):
        """Test that login works with the new password"""
        try:
            # Clear current session
            self.session.headers.pop('Authorization', None)
            
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                new_token = token_data.get('access_token')
                if new_token:
                    # Restore authorization header
                    self.session.headers.update({'Authorization': f'Bearer {new_token}'})
                    self.log_test("Login with New Password", True, "Login successful with new password")
                    return True
                else:
                    self.log_test("Login with New Password", False, "No access token in response")
                    return False
            else:
                self.log_test("Login with New Password", False, f"Failed to login with new password: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Login with New Password", False, f"Exception testing login with new password: {str(e)}")
            return False
    
    def test_profile_persistence(self):
        """Test that profile changes are persisted by getting current user info"""
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Check that our updates are still there
                expected_values = {
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'company_name': 'Updated Company LLC',
                    'street_address': '456 Updated Avenue',
                    'city': 'New City',
                    'state': 'NY',
                    'postal_code': '54321',
                    'email': self.test_user_email
                }
                
                mismatches = []
                for field, expected_value in expected_values.items():
                    if user_data.get(field) != expected_value:
                        mismatches.append(f"{field}: expected '{expected_value}', got '{user_data.get(field)}'")
                
                if mismatches:
                    self.log_test("Profile Persistence", False, f"Profile changes not persisted: {'; '.join(mismatches)}")
                    return False
                
                self.log_test("Profile Persistence", True, "All profile changes persisted correctly")
                return True
            else:
                self.log_test("Profile Persistence", False, f"Failed to get user info: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Profile Persistence", False, f"Exception testing profile persistence: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all user settings management tests"""
        print("🚀 Starting User Settings Management API Tests")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_api_health():
            print("❌ API not accessible, stopping tests")
            return False
        
        # User creation and authentication
        if not self.create_test_user():
            print("❌ Failed to create test user, stopping tests")
            return False
        
        if not self.login_test_user():
            print("❌ Failed to login test user, stopping tests")
            return False
        
        # Test getting current user info
        self.test_get_current_user()
        
        # Profile update tests
        self.test_update_profile_personal_info()
        self.test_update_profile_company_info()
        self.test_update_profile_email()
        
        # Error handling tests
        self.test_email_uniqueness_validation()
        self.test_update_profile_empty_request()
        
        # Password update tests
        self.test_update_password_success()
        self.test_update_password_wrong_current()
        self.test_login_with_new_password()
        
        # Persistence test
        self.test_profile_persistence()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = UserSettingsTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)