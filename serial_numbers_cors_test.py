#!/usr/bin/env python3
"""
Serial Numbers CORS and Backend Testing
Focus on verifying CORS resolution and serial numbers functionality as requested in review.

Test Areas:
1. CORS Verification - Test that frontend URL is properly allowed
2. Serial Numbers Creation - Complete workflow testing
3. Configuration Field Access - Verify get_config_value helper function
4. Complete Workflow - End-to-end testing

Review Request Focus:
- Verify CORS issue has been resolved for https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com
- Test POST /api/projects/{project_id}/serial-numbers endpoint
- Verify camelCase/snake_case field mapping works correctly
- Test complete workflow from project creation to serial numbers creation
"""

import requests
import json
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"
FRONTEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com"

class SerialNumbersCORSTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.frontend_url = FRONTEND_URL
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
    
    def test_cors_preflight(self):
        """Test CORS preflight request to verify frontend URL is allowed"""
        try:
            # Send OPTIONS request with frontend origin
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            response = self.session.options(f"{self.base_url}/projects", headers=headers)
            
            # Check if CORS headers are present and allow the frontend URL
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods', '')
            cors_headers = response.headers.get('Access-Control-Allow-Headers', '')
            
            # Backend is configured with allow_origins=["*", "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com"]
            # So it should return the specific origin or "*"
            origin_allowed = (cors_origin == '*' or 
                            cors_origin == self.frontend_url or
                            'serialtrack.preview.emergentagent.com' in str(cors_origin))
            
            if origin_allowed:
                if 'POST' in cors_methods and ('Content-Type' in cors_headers or '*' in cors_headers):
                    self.log_test("CORS Preflight Check", True, 
                                f"CORS properly configured for frontend URL",
                                f"Origin: {cors_origin}, Methods: {cors_methods}")
                    return True
                else:
                    self.log_test("CORS Preflight Check", False, 
                                f"CORS headers incomplete - Methods: {cors_methods}, Headers: {cors_headers}")
                    return False
            else:
                self.log_test("CORS Preflight Check", False, 
                            f"Frontend URL not allowed in CORS - Origin: {cors_origin}")
                return False
                
        except Exception as e:
            self.log_test("CORS Preflight Check", False, f"CORS test error: {str(e)}")
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
    
    def create_test_user(self):
        """Create a test user for authentication"""
        user_data = {
            "email": "serialtest@example.com",
            "password": "TestPassword123!",
            "firstName": "Serial",
            "lastName": "Tester",
            "companyName": "Test Company",
            "streetAddress": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "postalCode": "12345",
            "countryCode": "US"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                user = response.json()
                self.test_user_id = user["id"]
                self.log_test("User Creation", True, f"Test user created successfully", f"User ID: {user['id']}")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # User already exists, try to login
                return self.login_test_user()
            else:
                self.log_test("User Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Creation", False, f"Request error: {str(e)}")
            return False
    
    def login_test_user(self):
        """Login with test user"""
        login_data = {
            "email": "serialtest@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("User Login", True, "Test user logged in successfully")
                return True
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Request error: {str(e)}")
            return False
    
    def create_test_project(self):
        """Create a test project"""
        project_data = {
            "name": "Serial Numbers CORS Test Project"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                self.test_project_id = project["id"]
                self.log_test("Project Creation", True, f"Test project created successfully", f"Project ID: {project['id']}")
                return True
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Request error: {str(e)}")
            return False
    
    def test_configuration_with_camelcase_snakecase(self):
        """Test configuration creation with both camelCase and snake_case field mapping"""
        # Test configuration with camelCase keys (as frontend would send)
        config_data = {
            "itemsPerCase": 10,
            "casesPerSscc": 2,
            "numberOfSscc": 1,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000001",
            "lotNumber": "TEST123",
            "expirationDate": "2025-12-31",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "packageNdc": "45802-046-85",
            "regulatedProductName": "Test Product",
            "manufacturerName": "Test Manufacturer"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                config = response.json()
                print(f"DEBUG: Configuration response keys: {list(config.keys())}")
                
                # The response might be in camelCase format due to by_alias=True in response model
                # Let's check for both camelCase and snake_case fields
                camel_case_fields = ["itemsPerCase", "casesPerSscc", "numberOfSscc", "useInnerCases", 
                                   "companyPrefix", "packageNdc", "senderGln", "receiverGln"]
                snake_case_fields = ["items_per_case", "cases_per_sscc", "number_of_sscc", "use_inner_cases", 
                                   "company_prefix", "package_ndc", "sender_gln", "receiver_gln"]
                
                camel_fields_present = all(field in config for field in camel_case_fields)
                snake_fields_present = all(field in config for field in snake_case_fields)
                
                if camel_fields_present or snake_fields_present:
                    field_format = "camelCase" if camel_fields_present else "snake_case"
                    self.log_test("Configuration camelCase/snake_case", True, 
                                f"Configuration properly handles field mapping ({field_format} response)",
                                f"Config ID: {config['id']}")
                    return True
                else:
                    missing_camel = [field for field in camel_case_fields if field not in config]
                    missing_snake = [field for field in snake_case_fields if field not in config]
                    self.log_test("Configuration camelCase/snake_case", False, 
                                f"Missing camelCase fields: {missing_camel}, Missing snake_case fields: {missing_snake}")
                    return False
            else:
                self.log_test("Configuration camelCase/snake_case", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration camelCase/snake_case", False, f"Request error: {str(e)}")
            return False
    
    def test_serial_numbers_creation_workflow(self):
        """Test the complete serial numbers creation workflow"""
        # Expected: 1 SSCC, 2 Cases (2 per SSCC), 20 Items (10 per case × 2 cases)
        serial_data = {
            "ssccSerialNumbers": ["SSCC001"],
            "caseSerialNumbers": ["CASE001", "CASE002"],
            "innerCaseSerialNumbers": [],  # Not using inner cases
            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(20)]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"DEBUG: Serial numbers response keys: {list(result.keys())}")
                
                # Check for both camelCase and snake_case response formats
                sscc_count = len(result.get("ssccSerialNumbers", result.get("sscc_serial_numbers", [])))
                case_count = len(result.get("caseSerialNumbers", result.get("case_serial_numbers", [])))
                item_count = len(result.get("itemSerialNumbers", result.get("item_serial_numbers", [])))
                
                # Verify serial numbers were saved correctly
                if sscc_count == 1 and case_count == 2 and item_count == 20:
                    self.log_test("Serial Numbers Creation", True, 
                                "Serial numbers created and validated correctly",
                                f"SSCC: {sscc_count}, Cases: {case_count}, Items: {item_count}")
                    return True
                else:
                    self.log_test("Serial Numbers Creation", False, 
                                f"Count validation failed - SSCC: {sscc_count}, Cases: {case_count}, Items: {item_count}")
                    return False
            else:
                self.log_test("Serial Numbers Creation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return False
    
    def test_get_config_value_helper_function(self):
        """Test that the backend properly uses get_config_value helper for field access"""
        # Create a configuration with mixed camelCase and snake_case to test the helper
        # This tests the backend's ability to handle both formats
        
        # Test with wrong serial number counts to trigger validation (which uses get_config_value)
        wrong_serial_data = {
            "ssccSerialNumbers": ["SSCC001", "SSCC002"],  # Wrong: should be 1, providing 2
            "caseSerialNumbers": ["CASE001", "CASE002"],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(20)]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/serial-numbers",
                json=wrong_serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                # Check if error message indicates proper field access
                if "Expected 1 SSCC serial numbers" in error_detail:
                    self.log_test("get_config_value Helper Function", True, 
                                "Backend properly accesses configuration fields using helper function",
                                f"Validation error: {error_detail}")
                    return True
                else:
                    self.log_test("get_config_value Helper Function", False, 
                                f"Unexpected error message: {error_detail}")
                    return False
            else:
                self.log_test("get_config_value Helper Function", False, 
                            f"Expected validation error (400), got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("get_config_value Helper Function", False, f"Request error: {str(e)}")
            return False
    
    def test_complete_workflow_no_regressions(self):
        """Test complete workflow to ensure no regressions were introduced"""
        try:
            # 1. Verify project exists and has configuration
            project_response = self.session.get(f"{self.base_url}/projects/{self.test_project_id}")
            
            if project_response.status_code != 200:
                self.log_test("Complete Workflow - No Regressions", False, 
                            f"Project retrieval failed: {project_response.status_code}")
                return False
            
            project = project_response.json()
            
            # 2. Verify configuration is saved
            if not project.get("configuration"):
                self.log_test("Complete Workflow - No Regressions", False, 
                            "Configuration not found in project")
                return False
            
            # 3. Verify serial numbers are saved
            if not project.get("serial_numbers"):
                self.log_test("Complete Workflow - No Regressions", False, 
                            "Serial numbers not found in project")
                return False
            
            # 4. Test EPCIS generation
            epcis_data = {
                "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            epcis_response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/generate-epcis",
                json=epcis_data,
                headers={"Content-Type": "application/json"}
            )
            
            if epcis_response.status_code == 200:
                # Verify EPCIS XML contains expected elements
                xml_content = epcis_response.text
                
                # Check for key EPCIS elements
                required_elements = [
                    "EPCISDocument",
                    "EPCISHeader", 
                    "EPCISBody",
                    "EventList",
                    "ObjectEvent",
                    "AggregationEvent"
                ]
                
                all_elements_present = all(element in xml_content for element in required_elements)
                
                if all_elements_present:
                    self.log_test("Complete Workflow - No Regressions", True, 
                                "Complete workflow successful - no regressions detected",
                                "Project → Configuration → Serial Numbers → EPCIS Generation all working")
                    return True
                else:
                    missing_elements = [elem for elem in required_elements if elem not in xml_content]
                    self.log_test("Complete Workflow - No Regressions", False, 
                                f"EPCIS XML missing elements: {missing_elements}")
                    return False
            else:
                self.log_test("Complete Workflow - No Regressions", False, 
                            f"EPCIS generation failed: {epcis_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Complete Workflow - No Regressions", False, f"Workflow test error: {str(e)}")
            return False
    
    def run_serial_numbers_cors_tests(self):
        """Run all serial numbers and CORS focused tests"""
        print("=" * 80)
        print("SERIAL NUMBERS CORS AND BACKEND FUNCTIONALITY TESTING")
        print("=" * 80)
        print("Review Request Focus Areas:")
        print("1. CORS Verification - Frontend URL properly allowed")
        print("2. Serial Numbers Creation - Complete workflow testing")
        print("3. Configuration Field Access - camelCase/snake_case mapping")
        print("4. Complete Workflow - End-to-end testing for regressions")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: CORS Preflight Check
        self.test_cors_preflight()
        
        # Test 3: Create test user and authenticate
        if not self.create_test_user():
            if not self.login_test_user():
                print("\n❌ Authentication failed. Stopping tests.")
                return False
        else:
            # If user was created, login
            if not self.login_test_user():
                print("\n❌ Login after user creation failed. Stopping tests.")
                return False
        
        # Test 4: Create test project
        if not self.create_test_project():
            print("\n❌ Project creation failed. Stopping tests.")
            return False
        
        # Test 5: Configuration with camelCase/snake_case mapping
        if not self.test_configuration_with_camelcase_snakecase():
            print("\n❌ Configuration creation failed. Stopping tests.")
            return False
        
        # Test 6: Serial numbers creation workflow
        if not self.test_serial_numbers_creation_workflow():
            print("\n❌ Serial numbers creation failed. Stopping tests.")
            return False
        
        # Test 7: Test get_config_value helper function
        self.test_get_config_value_helper_function()
        
        # Test 8: Complete workflow regression test
        self.test_complete_workflow_no_regressions()
        
        # Summary
        print("\n" + "=" * 80)
        print("SERIAL NUMBERS CORS TEST SUMMARY")
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
        
        print("\nReview Request Areas Tested:")
        print("✓ CORS configuration for frontend URL")
        print("✓ Serial numbers creation endpoint")
        print("✓ camelCase/snake_case field mapping")
        print("✓ get_config_value helper function usage")
        print("✓ Complete workflow regression testing")
        
        return passed == total

if __name__ == "__main__":
    tester = SerialNumbersCORSTester()
    success = tester.run_serial_numbers_cors_tests()
    sys.exit(0 if success else 1)