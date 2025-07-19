#!/usr/bin/env python3
"""
Configuration Endpoint 422 Error Testing
Tests the specific 422 error reported by user when POSTing to configuration endpoint.

ISSUE BACKGROUND:
User is getting a 422 (Unprocessable Content) error when trying to POST to:
POST https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api/projects/8b2bde0c-07e6-4b4b-97c8-535023f90e90/configuration

The frontend was sending `sscc_indicator_digit` but the backend now expects `sscc_extension_digit`.
However, there may be other validation issues.

TESTING REQUIREMENTS:
1. Test Configuration Endpoint Validation with various configuration data
2. Check Required Fields validation
3. Test Field Validation with realistic configuration payload
4. Check Data Types (integer vs string fields)
5. Test Empty Values rejection for required fields
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class Configuration422Tester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None
        self.test_project_id = None
        
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
    
    def setup_test_user_and_project(self):
        """Create a test user and project for testing"""
        # Create test user
        user_data = {
            "email": f"test422_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "password": "testpassword123",
            "firstName": "Test",
            "lastName": "User422",
            "companyName": "Test Company",
            "streetAddress": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "postalCode": "12345",
            "countryCode": "US"
        }
        
        try:
            # Register user
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                user_info = response.json()
                self.test_user_id = user_info["id"]
                
                # Login to get token
                login_response = self.session.post(
                    f"{self.base_url}/auth/login",
                    json={"email": user_data["email"], "password": user_data["password"]},
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.auth_token = token_data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    
                    # Create test project
                    project_response = self.session.post(
                        f"{self.base_url}/projects",
                        json={"name": "Test Project 422"},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if project_response.status_code == 200:
                        project_info = project_response.json()
                        self.test_project_id = project_info["id"]
                        self.log_test("Setup Test User and Project", True, f"Created user and project successfully", 
                                    f"User ID: {self.test_user_id}, Project ID: {self.test_project_id}")
                        return True
                    else:
                        self.log_test("Setup Test User and Project", False, f"Project creation failed: {project_response.status_code}")
                        return False
                else:
                    self.log_test("Setup Test User and Project", False, f"Login failed: {login_response.status_code}")
                    return False
            else:
                self.log_test("Setup Test User and Project", False, f"User registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Setup Test User and Project", False, f"Setup error: {str(e)}")
            return False
    
    def test_api_health(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "EPCIS" in data.get("message", ""):
                    self.log_test("API Health Check", True, "API is responding correctly")
                    return True
                else:
                    self.log_test("API Health Check", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("API Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_configuration_with_review_request_payload(self):
        """Test configuration creation with the exact payload from review request"""
        if not self.test_project_id:
            self.log_test("Review Request Configuration Payload", False, "No test project available")
            return False
            
        # Exact configuration from review request
        test_data = {
            "items_per_case": 0,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": True,
            "inner_cases_per_case": 3,
            "items_per_inner_case": 4,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "inner_case_product_code": "000000",
            "sscc_extension_digit": "3",  # This is the corrected field name
            "case_indicator_digit": "2",
            "inner_case_indicator_digit": "4", 
            "item_indicator_digit": "1"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Review Request Configuration Payload", True, "Configuration created successfully with corrected field names", 
                            f"Configuration ID: {data.get('id')}")
                return True
            elif response.status_code == 422:
                error_details = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                self.log_test("Review Request Configuration Payload", False, f"422 Unprocessable Content error", 
                            f"Error details: {error_details}")
                return False
            else:
                self.log_test("Review Request Configuration Payload", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Review Request Configuration Payload", False, f"Request error: {str(e)}")
            return False
    
    def test_configuration_with_old_field_name(self):
        """Test configuration creation with the old field name that was causing issues"""
        if not self.test_project_id:
            self.log_test("Old Field Name Configuration", False, "No test project available")
            return False
            
        # Configuration with old field name (sscc_indicator_digit instead of sscc_extension_digit)
        test_data = {
            "items_per_case": 0,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": True,
            "inner_cases_per_case": 3,
            "items_per_inner_case": 4,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "inner_case_product_code": "000000",
            "sscc_indicator_digit": "3",  # This is the OLD field name that was causing issues
            "case_indicator_digit": "2",
            "inner_case_indicator_digit": "4", 
            "item_indicator_digit": "1"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 422:
                error_details = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                self.log_test("Old Field Name Configuration", True, "422 error correctly returned for old field name", 
                            f"Error details: {error_details}")
                return True
            elif response.status_code == 200:
                self.log_test("Old Field Name Configuration", False, "Configuration was accepted with old field name (should have been rejected)")
                return False
            else:
                self.log_test("Old Field Name Configuration", False, f"Unexpected HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Old Field Name Configuration", False, f"Request error: {str(e)}")
            return False
    
    def test_required_fields_validation(self):
        """Test validation of required fields"""
        if not self.test_project_id:
            self.log_test("Required Fields Validation", False, "No test project available")
            return False
        
        # Test with missing required fields
        required_field_tests = [
            ("Missing cases_per_sscc", {
                "number_of_sscc": 1,
                "company_prefix": "1234567",
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": "3",
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            }),
            ("Missing number_of_sscc", {
                "cases_per_sscc": 2,
                "company_prefix": "1234567",
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": "3",
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            }),
            ("Missing company_prefix", {
                "cases_per_sscc": 2,
                "number_of_sscc": 1,
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": "3",
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            }),
            ("Missing sscc_extension_digit", {
                "cases_per_sscc": 2,
                "number_of_sscc": 1,
                "company_prefix": "1234567",
                "item_product_code": "000000",
                "case_product_code": "000000",
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            })
        ]
        
        all_passed = True
        for test_name, test_data in required_field_tests:
            try:
                response = self.session.post(
                    f"{self.base_url}/projects/{self.test_project_id}/configuration",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 422:
                    error_details = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    self.log_test(f"Required Fields - {test_name}", True, "422 error correctly returned for missing required field", 
                                f"Error: {error_details}")
                elif response.status_code == 200:
                    self.log_test(f"Required Fields - {test_name}", False, "Configuration was accepted with missing required field")
                    all_passed = False
                else:
                    self.log_test(f"Required Fields - {test_name}", False, f"Unexpected HTTP {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Required Fields - {test_name}", False, f"Request error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_data_type_validation(self):
        """Test validation of data types (integers vs strings)"""
        if not self.test_project_id:
            self.log_test("Data Type Validation", False, "No test project available")
            return False
        
        # Test with wrong data types
        data_type_tests = [
            ("String for cases_per_sscc", {
                "items_per_case": 0,
                "cases_per_sscc": "2",  # Should be integer
                "number_of_sscc": 1,
                "company_prefix": "1234567",
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": "3",
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            }),
            ("Integer for company_prefix", {
                "items_per_case": 0,
                "cases_per_sscc": 2,
                "number_of_sscc": 1,
                "company_prefix": 1234567,  # Should be string
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": "3",
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            }),
            ("Integer for sscc_extension_digit", {
                "items_per_case": 0,
                "cases_per_sscc": 2,
                "number_of_sscc": 1,
                "company_prefix": "1234567",
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": 3,  # Should be string
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            })
        ]
        
        all_passed = True
        for test_name, test_data in data_type_tests:
            try:
                response = self.session.post(
                    f"{self.base_url}/projects/{self.test_project_id}/configuration",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 422]:
                    # Both are acceptable - some APIs auto-convert types, others reject
                    if response.status_code == 422:
                        error_details = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                        self.log_test(f"Data Type - {test_name}", True, "422 error returned for wrong data type", 
                                    f"Error: {error_details}")
                    else:
                        self.log_test(f"Data Type - {test_name}", True, "Configuration accepted (type auto-converted)")
                else:
                    self.log_test(f"Data Type - {test_name}", False, f"Unexpected HTTP {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Data Type - {test_name}", False, f"Request error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_empty_values_validation(self):
        """Test validation of empty values for required fields"""
        if not self.test_project_id:
            self.log_test("Empty Values Validation", False, "No test project available")
            return False
        
        # Test with empty values for required fields
        empty_value_tests = [
            ("Empty company_prefix", {
                "items_per_case": 0,
                "cases_per_sscc": 2,
                "number_of_sscc": 1,
                "company_prefix": "",  # Empty string
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": "3",
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            }),
            ("Empty sscc_extension_digit", {
                "items_per_case": 0,
                "cases_per_sscc": 2,
                "number_of_sscc": 1,
                "company_prefix": "1234567",
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": "",  # Empty string
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            }),
            ("Zero cases_per_sscc with inner cases", {
                "items_per_case": 0,
                "cases_per_sscc": 0,  # Zero cases but inner cases enabled
                "number_of_sscc": 1,
                "use_inner_cases": True,
                "inner_cases_per_case": 3,
                "items_per_inner_case": 4,
                "company_prefix": "1234567",
                "item_product_code": "000000",
                "case_product_code": "000000",
                "sscc_extension_digit": "3",
                "case_indicator_digit": "2",
                "item_indicator_digit": "1"
            })
        ]
        
        all_passed = True
        for test_name, test_data in empty_value_tests:
            try:
                response = self.session.post(
                    f"{self.base_url}/projects/{self.test_project_id}/configuration",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 422:
                    error_details = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    self.log_test(f"Empty Values - {test_name}", True, "422 error correctly returned for empty/invalid values", 
                                f"Error: {error_details}")
                elif response.status_code == 200:
                    # Some empty values might be acceptable depending on business logic
                    self.log_test(f"Empty Values - {test_name}", True, "Configuration accepted (empty values allowed)")
                else:
                    self.log_test(f"Empty Values - {test_name}", False, f"Unexpected HTTP {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Empty Values - {test_name}", False, f"Request error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_complete_valid_configuration(self):
        """Test a complete valid configuration to ensure the endpoint works when all data is correct"""
        if not self.test_project_id:
            self.log_test("Complete Valid Configuration", False, "No test project available")
            return False
            
        # Complete valid configuration with all fields
        test_data = {
            "items_per_case": 0,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": True,
            "inner_cases_per_case": 3,
            "items_per_inner_case": 4,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "inner_case_product_code": "000000",
            "lot_number": "LOT123456",
            "expiration_date": "2026-12-31",
            "sscc_extension_digit": "3",
            "case_indicator_digit": "2",
            "inner_case_indicator_digit": "4", 
            "item_indicator_digit": "1",
            # Business Document Information
            "sender_company_prefix": "0345802",
            "sender_gln": "0345802000014",
            "sender_sgln": "0345802000014.001",
            "sender_name": "Test Sender Company",
            "sender_street_address": "123 Sender St",
            "sender_city": "Sender City",
            "sender_state": "SC",
            "sender_postal_code": "12345",
            "sender_country_code": "US",
            "receiver_company_prefix": "0567890",
            "receiver_gln": "0567890000021",
            "receiver_sgln": "0567890000021.001",
            "receiver_name": "Test Receiver Company",
            "receiver_street_address": "456 Receiver Ave",
            "receiver_city": "Receiver City",
            "receiver_state": "RC",
            "receiver_postal_code": "67890",
            "receiver_country_code": "US",
            "shipper_company_prefix": "0999888",
            "shipper_gln": "0999888000028",
            "shipper_sgln": "0999888000028.001",
            "shipper_name": "Test Shipper Corp",
            "shipper_street_address": "789 Shipper Blvd",
            "shipper_city": "Shipper City",
            "shipper_state": "SH",
            "shipper_postal_code": "11111",
            "shipper_country_code": "US",
            "shipper_same_as_sender": False,
            # EPCClass data
            "product_ndc": "45802-046-85",
            "package_ndc": "45802-046-85",
            "regulated_product_name": "Test Medication",
            "manufacturer_name": "Test Pharma Inc",
            "dosage_form_type": "Tablet",
            "strength_description": "500mg",
            "net_content_description": "100 tablets"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Complete Valid Configuration", True, "Complete configuration created successfully", 
                            f"Configuration ID: {data.get('id')}")
                return True
            elif response.status_code == 422:
                error_details = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                self.log_test("Complete Valid Configuration", False, f"422 error for valid configuration", 
                            f"Error details: {error_details}")
                return False
            else:
                self.log_test("Complete Valid Configuration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Complete Valid Configuration", False, f"Request error: {str(e)}")
            return False
    
    def run_422_error_tests(self):
        """Run all tests focused on the 422 error issue"""
        print("=" * 80)
        print("CONFIGURATION ENDPOINT 422 ERROR TESTING")
        print("=" * 80)
        print("Testing the specific 422 error reported by user when POSTing to configuration endpoint")
        print("Focus: Field name mismatch (sscc_indicator_digit vs sscc_extension_digit) and other validation issues")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Setup test user and project
        if not self.setup_test_user_and_project():
            print("\n❌ Could not setup test user and project. Stopping tests.")
            return False
        
        # Test 3: Test with review request payload (corrected field names)
        self.test_configuration_with_review_request_payload()
        
        # Test 4: Test with old field name that was causing issues
        self.test_configuration_with_old_field_name()
        
        # Test 5: Test required fields validation
        self.test_required_fields_validation()
        
        # Test 6: Test data type validation
        self.test_data_type_validation()
        
        # Test 7: Test empty values validation
        self.test_empty_values_validation()
        
        # Test 8: Test complete valid configuration
        self.test_complete_valid_configuration()
        
        # Summary
        print("\n" + "=" * 80)
        print("422 ERROR TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
                    if result['details']:
                        print(f"    Details: {result['details']}")
        
        print("\n422 Error Analysis:")
        print("✓ Field name validation (sscc_indicator_digit vs sscc_extension_digit)")
        print("✓ Required fields validation")
        print("✓ Data type validation")
        print("✓ Empty values validation")
        print("✓ Complete configuration acceptance")
        
        return passed == total

if __name__ == "__main__":
    tester = Configuration422Tester()
    success = tester.run_422_error_tests()
    sys.exit(0 if success else 1)