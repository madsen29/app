#!/usr/bin/env python3
"""
EPCIS Generation Fix Testing - KeyError: 'type' Resolution
Tests the specific fix implemented for the 500 Internal Server Error due to KeyError: 'type' in generate_epcis_xml function.

The issue was that the function expected serial_numbers in flat list format with 'type' fields,
but auto-save was storing them in hierarchical format (ssccSerialNumbers, caseSerialNumbers, etc.).

Test Focus:
1. Test POST /api/projects/{project_id}/generate-epcis endpoint
2. Verify the KeyError: 'type' is fixed and EPCIS XML generates successfully
3. Test with existing project data from test_result.md configuration
4. Verify both data structure formats are handled correctly
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://c77fc0ef-d782-494d-81fe-4e233a061567.preview.emergentagent.com/api"

class EPCISGenerationFixTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.user_id = None
        
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
    
    def setup_test_user(self):
        """Use existing approved test user"""
        # Use the approved test user we created
        user_credentials = {
            "email": "epcis_test_user@test.com",
            "password": "TestPassword123!"
        }
        
        try:
            # Login to get token
            login_response = self.session.post(
                f"{self.base_url}/auth/login",
                json=user_credentials,
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                self.auth_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                # Get user info
                me_response = self.session.get(f"{self.base_url}/auth/me")
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    self.user_id = user_info["id"]
                    self.log_test("User Authentication", True, f"Test user authenticated: {user_credentials['email']}")
                    return True
                else:
                    self.log_test("User Authentication", False, f"Failed to get user info: {me_response.status_code}")
                    return False
            else:
                self.log_test("User Authentication", False, f"Login failed: {login_response.status_code} - {login_response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def create_test_project(self):
        """Create a test project"""
        try:
            project_data = {
                "name": f"EPCIS Fix Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                self.log_test("Project Creation", True, f"Test project created: {project['name']}")
                return project["id"]
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Request error: {str(e)}")
            return None
    
    def create_test_configuration(self, project_id):
        """Create test configuration based on test_result.md data"""
        if not project_id:
            self.log_test("Configuration Creation", False, "No project ID available")
            return False
            
        # Configuration from test_result.md: Items per case: 2, Cases per SSCC: 1, Number of SSCCs: 1
        config_data = {
            "itemsPerCase": 2,
            "casesPerSscc": 1,
            "numberOfSscc": 1,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000001",
            "lotNumber": "LOT123",
            "expirationDate": "2026-12-31",
            "ssccExtensionDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            # Business Document Information
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "senderName": "Padagis US LLC",
            "senderStreetAddress": "123 Pharma Street",
            "senderCity": "Minneapolis",
            "senderState": "MN",
            "senderPostalCode": "55401",
            "senderCountryCode": "US",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Pharmacy Corp",
            "receiverStreetAddress": "456 Retail Ave",
            "receiverCity": "Chicago",
            "receiverState": "IL",
            "receiverPostalCode": "60601",
            "receiverCountryCode": "US",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Shipping Corp",
            "shipperStreetAddress": "789 Logistics Blvd",
            "shipperCity": "Dallas",
            "shipperState": "TX",
            "shipperPostalCode": "75201",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False,
            # EPCClass data
            "packageNdc": "45802-046-85",
            "regulatedProductName": "Metformin Hydrochloride Tablets",
            "manufacturerName": "Padagis US LLC",
            "dosageFormType": "Tablet",
            "strengthDescription": "500 mg",
            "netContentDescription": "100 tablets"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                config = response.json()
                self.log_test("Configuration Creation", True, "Test configuration created successfully")
                return True
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Creation", False, f"Request error: {str(e)}")
            return False
    
    def create_test_serial_numbers(self, project_id):
        """Create test serial numbers using POST endpoint (creates flat list format)"""
        if not project_id:
            self.log_test("Serial Numbers Creation", False, "No project ID available")
            return False
            
        # For config: 1 SSCC, 1 Case, 2 Items
        serial_data = {
            "ssccSerialNumbers": ["TEST_SSCC_001"],
            "caseSerialNumbers": ["TEST_CASE_001"],
            "itemSerialNumbers": ["TEST_ITEM_001", "TEST_ITEM_002"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                serials = response.json()
                self.log_test("Serial Numbers Creation", True, "Test serial numbers created successfully")
                return True
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return False
    
    def simulate_auto_save_format(self, project_id):
        """Simulate auto-save by updating project with hierarchical serial numbers format"""
        if not project_id:
            self.log_test("Auto-Save Simulation", False, "No project ID available")
            return False
            
        # Create hierarchical serial structure like the frontend does
        # For config: 1 SSCC, 1 Case, 2 Items
        hierarchical_structure = [
            {
                "ssccIndex": 0,
                "ssccSerial": "AUTO_SAVE_SSCC_001",
                "cases": [
                    {
                        "caseIndex": 0,
                        "caseSerial": "AUTO_SAVE_CASE_001",
                        "innerCases": [],
                        "items": [
                            {
                                "itemIndex": 0,
                                "itemSerial": "AUTO_SAVE_ITEM_001"
                            },
                            {
                                "itemIndex": 1,
                                "itemSerial": "AUTO_SAVE_ITEM_002"
                            }
                        ]
                    }
                ]
            }
        ]
        
        try:
            # Update project with hierarchical serial structure (auto-save format)
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json={"serial_numbers": hierarchical_structure},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                self.log_test("Auto-Save Simulation", True, "Project updated with hierarchical serial format")
                return True
            else:
                self.log_test("Auto-Save Simulation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Auto-Save Simulation", False, f"Request error: {str(e)}")
            return False
    
    def test_epcis_generation_with_flat_format(self, project_id):
        """Test EPCIS generation with flat list format (from POST /serial-numbers)"""
        if not project_id:
            self.log_test("EPCIS Generation (Flat Format)", False, "No project ID available")
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
                
                # Verify it's valid XML
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Check for EPCISDocument root
                    if root.tag.endswith("EPCISDocument"):
                        # Check for test serial numbers in XML
                        if "TEST_SSCC_001" in xml_content and "TEST_CASE_001" in xml_content and "TEST_ITEM_001" in xml_content:
                            self.log_test("EPCIS Generation (Flat Format)", True, "EPCIS XML generated successfully with flat format data")
                            return True
                        else:
                            self.log_test("EPCIS Generation (Flat Format)", False, "Test serial numbers not found in XML")
                            return False
                    else:
                        self.log_test("EPCIS Generation (Flat Format)", False, f"Invalid XML root: {root.tag}")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("EPCIS Generation (Flat Format)", False, f"Invalid XML generated: {str(e)}")
                    return False
            else:
                self.log_test("EPCIS Generation (Flat Format)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("EPCIS Generation (Flat Format)", False, f"Request error: {str(e)}")
            return False
    
    def test_epcis_generation_with_hierarchical_format(self, project_id):
        """Test EPCIS generation with hierarchical format (from auto-save) - This is the main fix test"""
        if not project_id:
            self.log_test("EPCIS Generation (Hierarchical Format)", False, "No project ID available")
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
                
                # Verify it's valid XML
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Check for EPCISDocument root
                    if root.tag.endswith("EPCISDocument"):
                        # Check for auto-save serial numbers in XML
                        if "AUTO_SAVE_SSCC_001" in xml_content and "AUTO_SAVE_CASE_001" in xml_content and "AUTO_SAVE_ITEM_001" in xml_content:
                            self.log_test("EPCIS Generation (Hierarchical Format)", True, "✅ CRITICAL FIX VERIFIED: EPCIS XML generated successfully with hierarchical format data - KeyError: 'type' is resolved!")
                            return True
                        else:
                            self.log_test("EPCIS Generation (Hierarchical Format)", False, "Auto-save serial numbers not found in XML")
                            return False
                    else:
                        self.log_test("EPCIS Generation (Hierarchical Format)", False, f"Invalid XML root: {root.tag}")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("EPCIS Generation (Hierarchical Format)", False, f"Invalid XML generated: {str(e)}")
                    return False
            elif response.status_code == 500:
                # This is what we're testing to fix
                error_text = response.text
                if "KeyError" in error_text and "'type'" in error_text:
                    self.log_test("EPCIS Generation (Hierarchical Format)", False, "❌ CRITICAL: KeyError: 'type' still occurring - fix not working!")
                    return False
                else:
                    self.log_test("EPCIS Generation (Hierarchical Format)", False, f"500 error but different cause: {error_text}")
                    return False
            else:
                self.log_test("EPCIS Generation (Hierarchical Format)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("EPCIS Generation (Hierarchical Format)", False, f"Request error: {str(e)}")
            return False
    
    def test_xml_content_validation(self, project_id):
        """Test that generated XML contains expected configuration data"""
        if not project_id:
            self.log_test("XML Content Validation", False, "No project ID available")
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
                
                # Check for key configuration elements
                validation_checks = [
                    ("Company Prefix", "1234567" in xml_content),
                    ("Sender GLN", "0345802000014" in xml_content),
                    ("Receiver GLN", "0567890000021" in xml_content),
                    ("Shipper GLN", "0999888000028" in xml_content),
                    ("Package NDC (cleaned)", "4580204685" in xml_content),
                    ("Lot Number", "LOT123" in xml_content),
                    ("Expiration Date", "2026-12-31" in xml_content),
                    ("Regulated Product Name", "Metformin Hydrochloride Tablets" in xml_content),
                    ("Manufacturer Name", "Padagis US LLC" in xml_content)
                ]
                
                passed_checks = sum(1 for _, check in validation_checks if check)
                total_checks = len(validation_checks)
                
                if passed_checks == total_checks:
                    self.log_test("XML Content Validation", True, f"All configuration data properly populated in XML ({passed_checks}/{total_checks})")
                    return True
                else:
                    failed_checks = [name for name, check in validation_checks if not check]
                    self.log_test("XML Content Validation", False, f"Some configuration data missing ({passed_checks}/{total_checks}). Failed: {failed_checks}")
                    return False
            else:
                self.log_test("XML Content Validation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("XML Content Validation", False, f"Request error: {str(e)}")
            return False
    
    def run_epcis_fix_tests(self):
        """Run focused tests for EPCIS generation fix"""
        print("=" * 80)
        print("EPCIS GENERATION FIX TESTING - KeyError: 'type' Resolution")
        print("=" * 80)
        print("Testing the fix for 500 Internal Server Error due to KeyError: 'type'")
        print("The issue: generate_epcis_xml function expected flat list format with 'type' fields,")
        print("but auto-save stored data in hierarchical format (ssccSerialNumbers, etc.)")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Setup test user and authentication
        if not self.setup_test_user():
            print("\n❌ Could not setup test user. Stopping tests.")
            return False
        
        # Test 3: Create test project
        project_id = self.create_test_project()
        if not project_id:
            print("\n❌ Could not create test project. Stopping tests.")
            return False
        
        # Test 4: Create test configuration
        if not self.create_test_configuration(project_id):
            print("\n❌ Could not create test configuration. Stopping tests.")
            return False
        
        # Test 5: Create serial numbers using POST endpoint (flat format)
        if not self.create_test_serial_numbers(project_id):
            print("\n❌ Could not create test serial numbers. Stopping tests.")
            return False
        
        # Test 6: Test EPCIS generation with flat format (should work)
        flat_format_success = self.test_epcis_generation_with_flat_format(project_id)
        
        # Test 7: Simulate auto-save format (hierarchical)
        if not self.simulate_auto_save_format(project_id):
            print("\n❌ Could not simulate auto-save format. Stopping tests.")
            return False
        
        # Test 8: Test EPCIS generation with hierarchical format (THE MAIN FIX TEST)
        hierarchical_format_success = self.test_epcis_generation_with_hierarchical_format(project_id)
        
        # Test 9: Validate XML content
        xml_validation_success = self.test_xml_content_validation(project_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("EPCIS GENERATION FIX TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical Fix Status
        print("\n" + "=" * 40)
        print("CRITICAL FIX STATUS")
        print("=" * 40)
        print(f"Flat Format EPCIS Generation: {'✅ WORKING' if flat_format_success else '❌ FAILING'}")
        print(f"Hierarchical Format EPCIS Generation: {'✅ FIXED' if hierarchical_format_success else '❌ STILL BROKEN'}")
        print(f"XML Content Validation: {'✅ WORKING' if xml_validation_success else '❌ FAILING'}")
        
        if hierarchical_format_success:
            print("\n🎉 SUCCESS: The KeyError: 'type' fix is working correctly!")
            print("   The generate_epcis_xml function now handles both data structure formats:")
            print("   ✓ Flat list format (from POST /serial-numbers)")
            print("   ✓ Hierarchical format (from auto-save)")
        else:
            print("\n❌ FAILURE: The KeyError: 'type' fix is NOT working!")
            print("   The 500 Internal Server Error is still occurring.")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return hierarchical_format_success

if __name__ == "__main__":
    tester = EPCISGenerationFixTester()
    success = tester.run_epcis_fix_tests()
    sys.exit(0 if success else 1)