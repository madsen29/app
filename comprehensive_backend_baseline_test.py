#!/usr/bin/env python3
"""
Comprehensive Backend API Baseline Testing for EPCIS Serial Number Aggregation App
Tests core backend functionality to establish baseline before scanner fixes testing.

Focus Areas (as per review request):
1. Authentication Endpoints: User registration, login, authentication flow
2. Project Management: Project creation, retrieval, basic CRUD operations  
3. Configuration API: Saving and retrieving project configuration
4. Scanner-related endpoints: Any endpoints used by scanner functionality

Test Configuration (as specified in review request):
- Items per case: 2
- Cases per SSCC: 1  
- Number of SSCCs: 1
- Company Prefix: 1234567
- Product Code: 000000
- Lot Number: LOT123
- Expiration Date: 2026-12-31

Goal: Ensure backend is solid before validating scanner modal fixes for mobile scrollability, 
2D code restriction, and item removal functionality.
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os
import time

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class ComprehensiveBackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_email = "baseline.tester@epcis.test"
        self.test_user_password = "SecureTestPass123!"
        
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
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "firstName": "Baseline",
            "lastName": "Tester",
            "companyName": "EPCIS Test Corp",
            "streetAddress": "123 Test Street",
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
                data = response.json()
                required_fields = ["id", "email", "first_name", "last_name", "company_name"]
                
                if all(field in data for field in required_fields):
                    if data["email"] == self.test_user_email:
                        self.log_test("User Registration", True, "User registered successfully", 
                                    f"User ID: {data['id']}, Email: {data['email']}")
                        return True
                    else:
                        self.log_test("User Registration", False, f"Email mismatch: {data['email']}")
                        return False
                else:
                    self.log_test("User Registration", False, "Missing required fields in response", data)
                    return False
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_test("User Registration", True, "User already exists (expected for repeat tests)")
                return True
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Request error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login endpoint and store auth token"""
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    self.auth_token = data["access_token"]
                    # Set authorization header for subsequent requests
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    self.log_test("User Login", True, "Login successful, token obtained", 
                                f"Token type: {data['token_type']}")
                    return True
                else:
                    self.log_test("User Login", False, "Missing token in response", data)
                    return False
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Request error: {str(e)}")
            return False
    
    def test_authentication_flow(self):
        """Test authenticated endpoint access"""
        if not self.auth_token:
            self.log_test("Authentication Flow", False, "No auth token available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == self.test_user_email:
                    self.log_test("Authentication Flow", True, "Authenticated access working", 
                                f"User: {data['first_name']} {data['last_name']}")
                    return True
                else:
                    self.log_test("Authentication Flow", False, f"Wrong user data: {data}")
                    return False
            else:
                self.log_test("Authentication Flow", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Flow", False, f"Request error: {str(e)}")
            return False
    
    def test_project_creation(self):
        """Test project creation endpoint"""
        if not self.auth_token:
            self.log_test("Project Creation", False, "No auth token available")
            return None
            
        project_data = {
            "name": f"Baseline Test Project - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "user_id", "status", "current_step"]
                
                if all(field in data for field in required_fields):
                    if data["name"] == project_data["name"] and data["status"] == "In Progress":
                        self.log_test("Project Creation", True, "Project created successfully", 
                                    f"Project ID: {data['id']}, Name: {data['name']}")
                        return data["id"]
                    else:
                        self.log_test("Project Creation", False, f"Data mismatch: {data}")
                        return None
                else:
                    self.log_test("Project Creation", False, "Missing required fields", data)
                    return None
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Request error: {str(e)}")
            return None
    
    def test_project_retrieval(self, project_id):
        """Test project retrieval endpoint"""
        if not project_id:
            self.log_test("Project Retrieval", False, "No project ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data["id"] == project_id:
                    self.log_test("Project Retrieval", True, "Project retrieved successfully", 
                                f"Project: {data['name']}, Status: {data['status']}")
                    return True
                else:
                    self.log_test("Project Retrieval", False, f"ID mismatch: {data}")
                    return False
            else:
                self.log_test("Project Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Retrieval", False, f"Request error: {str(e)}")
            return False
    
    def test_project_list(self):
        """Test project listing endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Project List", True, f"Projects listed successfully", 
                                f"Found {len(data)} projects")
                    return True
                else:
                    self.log_test("Project List", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_test("Project List", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project List", False, f"Request error: {str(e)}")
            return False
    
    def test_configuration_creation(self, project_id):
        """Test configuration creation with review request parameters"""
        if not project_id:
            self.log_test("Configuration Creation", False, "No project ID available")
            return False
            
        # Review request configuration:
        # Items per case: 2, Cases per SSCC: 1, Number of SSCCs: 1
        # Company Prefix: 1234567, Product Code: 000000
        # Lot Number: LOT123, Expiration Date: 2026-12-31
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
            # Business Document Information
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "senderName": "Baseline Test Sender",
            "senderStreetAddress": "123 Sender St",
            "senderCity": "Sender City",
            "senderState": "SC",
            "senderPostalCode": "12345",
            "senderCountryCode": "US",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Baseline Test Receiver",
            "receiverStreetAddress": "456 Receiver Ave",
            "receiverCity": "Receiver City",
            "receiverState": "RC",
            "receiverPostalCode": "67890",
            "receiverCountryCode": "US",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Baseline Test Shipper",
            "shipperStreetAddress": "789 Shipper Blvd",
            "shipperCity": "Shipper City",
            "shipperState": "SH",
            "shipperPostalCode": "11111",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False,
            # EPCClass data
            "packageNdc": "45802-046-85",
            "regulatedProductName": "Baseline Test Product",
            "manufacturerName": "Baseline Test Manufacturer",
            "dosageFormType": "Tablet",
            "strengthDescription": "500mg",
            "netContentDescription": "100 tablets"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Verify key configuration fields
                if (data.get("items_per_case") == 2 and 
                    data.get("cases_per_sscc") == 1 and
                    data.get("number_of_sscc") == 1 and
                    data.get("company_prefix") == "1234567" and
                    data.get("lot_number") == "LOT123"):
                    self.log_test("Configuration Creation", True, "Configuration saved successfully", 
                                f"Config ID: {data['id']}, Items/Case: {data['items_per_case']}")
                    return True
                else:
                    self.log_test("Configuration Creation", False, f"Configuration data mismatch: {data}")
                    return False
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Creation", False, f"Request error: {str(e)}")
            return False
    
    def test_configuration_retrieval(self, project_id):
        """Test configuration retrieval from project"""
        if not project_id:
            self.log_test("Configuration Retrieval", False, "No project ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                data = response.json()
                config = data.get("configuration")
                if config:
                    # Verify configuration fields are preserved
                    if (config.get("items_per_case") == 2 and 
                        config.get("company_prefix") == "1234567" and
                        config.get("lot_number") == "LOT123"):
                        self.log_test("Configuration Retrieval", True, "Configuration retrieved successfully", 
                                    f"Items/Case: {config['items_per_case']}, Lot: {config['lot_number']}")
                        return True
                    else:
                        self.log_test("Configuration Retrieval", False, f"Configuration data incorrect: {config}")
                        return False
                else:
                    self.log_test("Configuration Retrieval", False, "No configuration found in project")
                    return False
            else:
                self.log_test("Configuration Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Retrieval", False, f"Request error: {str(e)}")
            return False
    
    def test_serial_numbers_creation(self, project_id):
        """Test serial numbers creation for scanner functionality"""
        if not project_id:
            self.log_test("Serial Numbers Creation", False, "No project ID available")
            return False
            
        # For review request config: 1 SSCC, 1 Case, 2 Items
        serial_data = {
            "ssccSerialNumbers": ["BASELINE_SSCC_001"],
            "caseSerialNumbers": ["BASELINE_CASE_001"],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": ["BASELINE_ITEM_001", "BASELINE_ITEM_002"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (len(data["sscc_serial_numbers"]) == 1 and 
                    len(data["case_serial_numbers"]) == 1 and
                    len(data["item_serial_numbers"]) == 2):
                    self.log_test("Serial Numbers Creation", True, "Serial numbers saved successfully", 
                                f"SSCC: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
                    return True
                else:
                    self.log_test("Serial Numbers Creation", False, f"Serial count mismatch: {data}")
                    return False
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return False
    
    def test_serial_numbers_validation(self, project_id):
        """Test serial numbers validation (scanner error handling)"""
        if not project_id:
            self.log_test("Serial Numbers Validation", False, "No project ID available")
            return False
            
        # Test with wrong number of items (should be 2, providing 3)
        invalid_serial_data = {
            "ssccSerialNumbers": ["BASELINE_SSCC_001"],
            "caseSerialNumbers": ["BASELINE_CASE_001"],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": ["ITEM_001", "ITEM_002", "ITEM_003"]  # Wrong count
        }
        
        try:
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
    
    def test_epcis_generation(self, project_id):
        """Test EPCIS generation endpoint (scanner output functionality)"""
        if not project_id:
            self.log_test("EPCIS Generation", False, "No project ID available")
            return False
            
        epcis_request = {
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json=epcis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Basic XML validation
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Check for EPCIS structure
                    if root.tag.endswith("EPCISDocument"):
                        # Check for our test serial numbers
                        if ("BASELINE_SSCC_001" in xml_content and 
                            "BASELINE_CASE_001" in xml_content and
                            "BASELINE_ITEM_001" in xml_content):
                            
                            # Check filename in response headers
                            content_disposition = response.headers.get("Content-Disposition", "")
                            if "filename=" in content_disposition:
                                self.log_test("EPCIS Generation", True, "EPCIS XML generated successfully", 
                                            f"Contains test serials, Filename: {content_disposition}")
                                return True
                            else:
                                self.log_test("EPCIS Generation", True, "EPCIS XML generated (no filename header)", 
                                            "Contains test serials")
                                return True
                        else:
                            self.log_test("EPCIS Generation", False, "Test serial numbers not found in XML")
                            return False
                    else:
                        self.log_test("EPCIS Generation", False, f"Invalid XML root: {root.tag}")
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
    
    def test_project_update(self, project_id):
        """Test project update endpoint (basic CRUD)"""
        if not project_id:
            self.log_test("Project Update", False, "No project ID available")
            return False
            
        update_data = {
            "name": f"Updated Baseline Test Project - {datetime.now().strftime('%H%M%S')}"
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["name"] == update_data["name"]:
                    self.log_test("Project Update", True, "Project updated successfully", 
                                f"New name: {data['name']}")
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
    
    def test_scanner_related_endpoints(self, project_id):
        """Test endpoints that would be used by scanner functionality"""
        if not project_id:
            self.log_test("Scanner Related Endpoints", False, "No project ID available")
            return False
            
        # Test project status update (scanner would update project status)
        status_update = {
            "status": "Completed"
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=status_update,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "Completed":
                    self.log_test("Scanner Related Endpoints", True, "Project status update working", 
                                f"Status: {data['status']}")
                    return True
                else:
                    self.log_test("Scanner Related Endpoints", False, f"Status not updated: {data}")
                    return False
            else:
                self.log_test("Scanner Related Endpoints", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Scanner Related Endpoints", False, f"Request error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        # Test unauthorized access
        temp_session = requests.Session()
        
        try:
            response = temp_session.get(f"{self.base_url}/projects")
            
            if response.status_code == 401:
                self.log_test("Error Handling", True, "Unauthorized access properly rejected")
                return True
            else:
                self.log_test("Error Handling", False, f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Request error: {str(e)}")
            return False
    
    def run_comprehensive_baseline_tests(self):
        """Run comprehensive backend baseline tests"""
        print("=" * 80)
        print("COMPREHENSIVE BACKEND BASELINE TESTING")
        print("=" * 80)
        print("Testing core backend functionality before scanner fixes validation")
        print("Review Request Configuration:")
        print("- Items per case: 2")
        print("- Cases per SSCC: 1")
        print("- Number of SSCCs: 1")
        print("- Company Prefix: 1234567")
        print("- Product Code: 000000")
        print("- Lot Number: LOT123")
        print("- Expiration Date: 2026-12-31")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Authentication Endpoints
        print("\n" + "=" * 40)
        print("AUTHENTICATION ENDPOINTS")
        print("=" * 40)
        
        self.test_user_registration()
        if not self.test_user_login():
            print("❌ Login failed. Cannot continue with authenticated tests.")
            return False
        self.test_authentication_flow()
        
        # Test 3: Project Management
        print("\n" + "=" * 40)
        print("PROJECT MANAGEMENT")
        print("=" * 40)
        
        project_id = self.test_project_creation()
        if not project_id:
            print("❌ Project creation failed. Cannot continue with project tests.")
            return False
            
        self.test_project_retrieval(project_id)
        self.test_project_list()
        self.test_project_update(project_id)
        
        # Test 4: Configuration API
        print("\n" + "=" * 40)
        print("CONFIGURATION API")
        print("=" * 40)
        
        if not self.test_configuration_creation(project_id):
            print("❌ Configuration creation failed. Cannot continue with configuration tests.")
            return False
            
        self.test_configuration_retrieval(project_id)
        
        # Test 5: Scanner-related endpoints
        print("\n" + "=" * 40)
        print("SCANNER-RELATED ENDPOINTS")
        print("=" * 40)
        
        self.test_serial_numbers_creation(project_id)
        self.test_serial_numbers_validation(project_id)
        self.test_epcis_generation(project_id)
        self.test_scanner_related_endpoints(project_id)
        
        # Test 6: Error Handling
        print("\n" + "=" * 40)
        print("ERROR HANDLING")
        print("=" * 40)
        
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 80)
        print("COMPREHENSIVE BASELINE TEST SUMMARY")
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
        
        print("\nTested Functionality:")
        print("✓ Authentication Endpoints (register, login, auth flow)")
        print("✓ Project Management (create, retrieve, list, update)")
        print("✓ Configuration API (save, retrieve project configuration)")
        print("✓ Scanner-related endpoints (serial numbers, EPCIS generation)")
        print("✓ Error handling and validation")
        
        print(f"\nBaseline Status: {'✅ SOLID' if passed == total else '❌ ISSUES FOUND'}")
        print("Ready for scanner modal fixes testing." if passed == total else "Backend issues need resolution before scanner testing.")
        
        return passed == total

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    success = tester.run_comprehensive_baseline_tests()
    sys.exit(0 if success else 1)