#!/usr/bin/env python3
"""
Scanner Resume Fix Backend Regression Testing
Tests all backend APIs to verify no regressions after frontend scanner resume functionality changes.

Focus Areas (as requested in review):
1. Authentication Endpoints - verify login/logout still works
2. Project Management - ensure project creation and retrieval work  
3. Configuration API - test saving and retrieving project configuration
4. Serial Numbers API - verify serial number creation and validation work
5. EPCIS Generation - test the complete workflow from project creation to EPCIS file generation

This is a comprehensive regression test to ensure frontend scanner changes haven't broken backend functionality.
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://serial-tracker-1.preview.emergentagent.com/api"

class ScannerResumeRegressionTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_email = "epcis_test_user@test.com"
        self.test_user_password = "TestPassword123!"
        
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
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "EPCIS" in data.get("message", ""):
                    self.log_test("API Health Check", True, "Backend API is responding correctly")
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
    
    # ========== AUTHENTICATION ENDPOINTS TESTING ==========
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            user_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "firstName": "Scanner",
                "lastName": "TestUser"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == self.test_user_email:
                    self.log_test("User Registration", True, "User registration successful", 
                                f"User ID: {data.get('id')}")
                    return True
                else:
                    self.log_test("User Registration", False, f"Email mismatch: {data}")
                    return False
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_test("User Registration", True, "User already exists (expected for regression test)")
                return True
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Request error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token") and data.get("token_type") == "bearer":
                    self.auth_token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("User Login", True, "Login successful, JWT token received")
                    return True
                else:
                    self.log_test("User Login", False, f"Invalid token response: {data}")
                    return False
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Request error: {str(e)}")
            return False
    
    def test_authenticated_user_info(self):
        """Test getting current user info with JWT token"""
        try:
            if not self.auth_token:
                self.log_test("User Info", False, "No auth token available")
                return False
                
            response = self.session.get(f"{self.base_url}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == self.test_user_email:
                    self.log_test("User Info", True, "Authenticated user info retrieved successfully")
                    return True
                else:
                    self.log_test("User Info", False, f"Email mismatch: {data}")
                    return False
            else:
                self.log_test("User Info", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Info", False, f"Request error: {str(e)}")
            return False
    
    def test_logout(self):
        """Test logout endpoint"""
        try:
            response = self.session.post(f"{self.base_url}/auth/logout")
            
            if response.status_code == 200:
                data = response.json()
                if "logged out" in data.get("message", "").lower():
                    self.log_test("User Logout", True, "Logout successful")
                    return True
                else:
                    self.log_test("User Logout", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("User Logout", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Logout", False, f"Request error: {str(e)}")
            return False
    
    # ========== PROJECT MANAGEMENT TESTING ==========
    
    def test_project_creation(self):
        """Test project creation endpoint"""
        try:
            if not self.auth_token:
                self.log_test("Project Creation", False, "No auth token available")
                return None
                
            project_data = {
                "name": f"Scanner Regression Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("name") == project_data["name"] and data.get("id"):
                    self.log_test("Project Creation", True, "Project created successfully", 
                                f"Project ID: {data['id']}")
                    return data["id"]
                else:
                    self.log_test("Project Creation", False, f"Invalid project data: {data}")
                    return None
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Request error: {str(e)}")
            return None
    
    def test_project_retrieval(self, project_id):
        """Test project retrieval endpoint"""
        try:
            if not project_id:
                self.log_test("Project Retrieval", False, "No project ID available")
                return False
                
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == project_id:
                    self.log_test("Project Retrieval", True, "Project retrieved successfully")
                    return True
                else:
                    self.log_test("Project Retrieval", False, f"Project ID mismatch: {data}")
                    return False
            else:
                self.log_test("Project Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Retrieval", False, f"Request error: {str(e)}")
            return False
    
    def test_project_listing(self):
        """Test project listing endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Project Listing", True, f"Projects listed successfully ({len(data)} projects)")
                    return True
                else:
                    self.log_test("Project Listing", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_test("Project Listing", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Listing", False, f"Request error: {str(e)}")
            return False
    
    def test_project_update(self, project_id):
        """Test project update endpoint"""
        try:
            if not project_id:
                self.log_test("Project Update", False, "No project ID available")
                return False
                
            update_data = {
                "name": f"Updated Scanner Test Project {datetime.now().strftime('%H%M%S')}"
            }
            
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("name") == update_data["name"]:
                    self.log_test("Project Update", True, "Project updated successfully")
                    return True
                else:
                    self.log_test("Project Update", False, f"Name not updated: {data}")
                    return False
            else:
                self.log_test("Project Update", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Update", False, f"Request error: {str(e)}")
            return False
    
    # ========== CONFIGURATION API TESTING ==========
    
    def test_configuration_creation(self, project_id):
        """Test configuration creation for project"""
        try:
            if not project_id:
                self.log_test("Configuration Creation", False, "No project ID available")
                return False
                
            # Review request configuration: Items per case: 2, Cases per SSCC: 1, Number of SSCCs: 1
            config_data = {
                "itemsPerCase": 2,
                "casesPerSscc": 1,
                "numberOfSscc": 1,
                "useInnerCases": False,
                "companyPrefix": "1234567",
                "itemProductCode": "000000",
                "caseProductCode": "000000",
                "lotNumber": "LOT123",
                "expirationDate": "2026-12-31",
                "ssccExtensionDigit": "3",
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
                "regulatedProductName": "Metformin Hydrochloride Tablets",
                "manufacturerName": "Padagis US LLC",
                "dosageFormType": "Tablet",
                "strengthDescription": "500 mg",
                "netContentDescription": "100 tablets"
            }
            
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check both camelCase and snake_case field names (backend returns camelCase)
                items_per_case = data.get("itemsPerCase") or data.get("items_per_case")
                cases_per_sscc = data.get("casesPerSscc") or data.get("cases_per_sscc") 
                number_of_sscc = data.get("numberOfSscc") or data.get("number_of_sscc")
                
                if (items_per_case == 2 and cases_per_sscc == 1 and number_of_sscc == 1):
                    self.log_test("Configuration Creation", True, "Configuration saved successfully", 
                                f"Items per case: {items_per_case}, Cases per SSCC: {cases_per_sscc}")
                    return True
                else:
                    self.log_test("Configuration Creation", False, f"Configuration values incorrect - Items: {items_per_case}, Cases: {cases_per_sscc}, SSCCs: {number_of_sscc}")
                    return False
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Creation", False, f"Request error: {str(e)}")
            return False
    
    def test_configuration_retrieval(self, project_id):
        """Test configuration retrieval from project"""
        try:
            if not project_id:
                self.log_test("Configuration Retrieval", False, "No project ID available")
                return False
                
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                data = response.json()
                config = data.get("configuration")
                if config and config.get("items_per_case") == 2:
                    self.log_test("Configuration Retrieval", True, "Configuration retrieved successfully from project")
                    return True
                else:
                    self.log_test("Configuration Retrieval", False, f"Configuration not found or invalid: {config}")
                    return False
            else:
                self.log_test("Configuration Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Retrieval", False, f"Request error: {str(e)}")
            return False
    
    # ========== SERIAL NUMBERS API TESTING ==========
    
    def test_serial_numbers_creation(self, project_id):
        """Test serial numbers creation for project"""
        try:
            if not project_id:
                self.log_test("Serial Numbers Creation", False, "No project ID available")
                return False
                
            # For configuration: 1 SSCC, 1 Case, 2 Items
            serial_data = {
                "ssccSerialNumbers": ["BASELINE_SSCC_001"],
                "caseSerialNumbers": ["BASELINE_CASE_001"],
                "innerCaseSerialNumbers": [],
                "itemSerialNumbers": ["BASELINE_ITEM_001", "BASELINE_ITEM_002"]
            }
            
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check both camelCase and snake_case field names (backend returns camelCase)
                sscc_serials = data.get("ssccSerialNumbers") or data.get("sscc_serial_numbers", [])
                case_serials = data.get("caseSerialNumbers") or data.get("case_serial_numbers", [])
                item_serials = data.get("itemSerialNumbers") or data.get("item_serial_numbers", [])
                
                if (len(sscc_serials) == 1 and len(case_serials) == 1 and len(item_serials) == 2):
                    self.log_test("Serial Numbers Creation", True, "Serial numbers created successfully", 
                                f"SSCC: {len(sscc_serials)}, Cases: {len(case_serials)}, Items: {len(item_serials)}")
                    return True
                else:
                    self.log_test("Serial Numbers Creation", False, f"Serial count incorrect - SSCC: {len(sscc_serials)}, Cases: {len(case_serials)}, Items: {len(item_serials)}")
                    return False
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return False
    
    def test_serial_numbers_validation(self, project_id):
        """Test serial numbers validation with incorrect counts"""
        try:
            if not project_id:
                self.log_test("Serial Numbers Validation", False, "No project ID available")
                return False
                
            # Test with wrong number of items (should be 2, providing 3)
            invalid_serial_data = {
                "ssccSerialNumbers": ["SSCC_001"],
                "caseSerialNumbers": ["CASE_001"],
                "innerCaseSerialNumbers": [],
                "itemSerialNumbers": ["ITEM_001", "ITEM_002", "ITEM_003"]  # Wrong count
            }
            
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=invalid_serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                error_msg = response.json().get("detail", "")
                if "Expected 2 item serial numbers" in error_msg:
                    self.log_test("Serial Numbers Validation", True, "Validation correctly rejected wrong item count")
                    return True
                else:
                    self.log_test("Serial Numbers Validation", False, f"Wrong error message: {error_msg}")
                    return False
            else:
                self.log_test("Serial Numbers Validation", False, f"Expected 400 error, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Serial Numbers Validation", False, f"Request error: {str(e)}")
            return False
    
    # ========== EPCIS GENERATION TESTING ==========
    
    def test_epcis_generation(self, project_id):
        """Test EPCIS XML generation for project"""
        try:
            if not project_id:
                self.log_test("EPCIS Generation", False, "No project ID available")
                return False
                
            epcis_data = {
                "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json=epcis_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Validate it's proper XML
                try:
                    root = ET.fromstring(xml_content)
                    if root.tag.endswith("EPCISDocument"):
                        # Check for our test serial numbers
                        if ("BASELINE_SSCC_001" in xml_content and 
                            "BASELINE_CASE_001" in xml_content and 
                            "BASELINE_ITEM_001" in xml_content):
                            
                            # Check filename in response headers
                            content_disposition = response.headers.get("Content-Disposition", "")
                            if "epcis-" in content_disposition and ".xml" in content_disposition:
                                self.log_test("EPCIS Generation", True, "EPCIS XML generated successfully with proper filename", 
                                            f"Filename: {content_disposition}")
                                return True
                            else:
                                self.log_test("EPCIS Generation", False, f"Invalid filename header: {content_disposition}")
                                return False
                        else:
                            self.log_test("EPCIS Generation", False, "Test serial numbers not found in XML")
                            return False
                    else:
                        self.log_test("EPCIS Generation", False, f"Invalid XML root element: {root.tag}")
                        return False
                except ET.ParseError as e:
                    self.log_test("EPCIS Generation", False, f"Invalid XML: {str(e)}")
                    return False
            else:
                self.log_test("EPCIS Generation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("EPCIS Generation", False, f"Request error: {str(e)}")
            return False
    
    def test_complete_workflow(self):
        """Test complete workflow from project creation to EPCIS generation"""
        try:
            # Create project
            project_id = self.test_project_creation()
            if not project_id:
                self.log_test("Complete Workflow", False, "Project creation failed")
                return False
            
            # Add configuration
            if not self.test_configuration_creation(project_id):
                self.log_test("Complete Workflow", False, "Configuration creation failed")
                return False
            
            # Add serial numbers
            if not self.test_serial_numbers_creation(project_id):
                self.log_test("Complete Workflow", False, "Serial numbers creation failed")
                return False
            
            # Generate EPCIS
            if not self.test_epcis_generation(project_id):
                self.log_test("Complete Workflow", False, "EPCIS generation failed")
                return False
            
            self.log_test("Complete Workflow", True, "End-to-end workflow completed successfully", 
                        f"Project ID: {project_id}")
            return True
                
        except Exception as e:
            self.log_test("Complete Workflow", False, f"Workflow error: {str(e)}")
            return False
    
    def test_unauthorized_access(self):
        """Test that endpoints properly reject unauthorized access"""
        try:
            # Temporarily remove auth token
            original_headers = self.session.headers.copy()
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            response = self.session.get(f"{self.base_url}/projects")
            
            # Restore headers
            self.session.headers.update(original_headers)
            
            if response.status_code in [401, 403]:
                self.log_test("Unauthorized Access", True, f"Properly rejected unauthorized access (HTTP {response.status_code})")
                return True
            else:
                self.log_test("Unauthorized Access", False, f"Expected 401/403, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Unauthorized Access", False, f"Request error: {str(e)}")
            return False
    
    def run_comprehensive_regression_tests(self):
        """Run comprehensive backend regression tests"""
        print("=" * 80)
        print("SCANNER RESUME FIX BACKEND REGRESSION TESTING")
        print("=" * 80)
        print("Verifying that frontend scanner resume changes haven't caused backend regressions")
        print("Testing all core backend functionality:")
        print("1. Authentication Endpoints")
        print("2. Project Management")
        print("3. Configuration API")
        print("4. Serial Numbers API")
        print("5. EPCIS Generation")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ Backend API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Authentication Endpoints
        print("\n" + "=" * 40)
        print("TESTING AUTHENTICATION ENDPOINTS")
        print("=" * 40)
        
        self.test_user_registration()
        if not self.test_user_login():
            print("❌ Login failed. Cannot continue with authenticated tests.")
            return False
        
        self.test_authenticated_user_info()
        self.test_logout()
        
        # Re-login for remaining tests
        self.test_user_login()
        
        # Test 3: Project Management
        print("\n" + "=" * 40)
        print("TESTING PROJECT MANAGEMENT")
        print("=" * 40)
        
        project_id = self.test_project_creation()
        self.test_project_retrieval(project_id)
        self.test_project_listing()
        self.test_project_update(project_id)
        
        # Test 4: Configuration API
        print("\n" + "=" * 40)
        print("TESTING CONFIGURATION API")
        print("=" * 40)
        
        self.test_configuration_creation(project_id)
        self.test_configuration_retrieval(project_id)
        
        # Test 5: Serial Numbers API
        print("\n" + "=" * 40)
        print("TESTING SERIAL NUMBERS API")
        print("=" * 40)
        
        self.test_serial_numbers_creation(project_id)
        self.test_serial_numbers_validation(project_id)
        
        # Test 6: EPCIS Generation
        print("\n" + "=" * 40)
        print("TESTING EPCIS GENERATION")
        print("=" * 40)
        
        self.test_epcis_generation(project_id)
        
        # Test 7: Security & Error Handling
        print("\n" + "=" * 40)
        print("TESTING SECURITY & ERROR HANDLING")
        print("=" * 40)
        
        self.test_unauthorized_access()
        
        # Test 8: Complete Workflow
        print("\n" + "=" * 40)
        print("TESTING COMPLETE WORKFLOW")
        print("=" * 40)
        
        self.test_complete_workflow()
        
        # Summary
        print("\n" + "=" * 80)
        print("BACKEND REGRESSION TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        else:
            print("\n✅ ALL BACKEND TESTS PASSED - NO REGRESSIONS DETECTED")
        
        print("\nTested Functionality:")
        print("✓ Authentication (register, login, logout, JWT validation)")
        print("✓ Project Management (create, read, update, list)")
        print("✓ Configuration API (save and retrieve project configuration)")
        print("✓ Serial Numbers API (create and validate serial numbers)")
        print("✓ EPCIS Generation (complete workflow to XML file generation)")
        print("✓ Security (unauthorized access rejection)")
        print("✓ Error Handling (validation and error responses)")
        
        return passed == total

if __name__ == "__main__":
    tester = ScannerResumeRegressionTester()
    success = tester.run_comprehensive_regression_tests()
    sys.exit(0 if success else 1)