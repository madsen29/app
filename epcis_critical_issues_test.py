#!/usr/bin/env python3
"""
EPCIS Critical Issues Testing - USER REPORTED THREE CRITICAL ISSUES

This test specifically addresses the three critical issues reported by the user:

1. **Inner case not getting defined in EPCClass vocabulary** like other packaging levels
2. **Product code showing 'None' instead of actual values** in SGTINs throughout, and showing '.' on inner packaging level  
3. **Extension digit on SSCC showing 'None'** instead of actual value in `<epc>urn:epc:id:sscc:shipperPrefix.None{serialNumber}</epc>`

CRITICAL FIXES APPLIED:
1. Fixed Product Code Mapping: Changed from looking for separate `itemProductCode`, `caseProductCode`, `innerCaseProductCode` fields to using a single `productCode` field for all packaging levels
2. Fixed SSCC Extension Digit Mapping: Changed from looking for `ssccIndicatorDigit` to `ssccExtensionDigit` to match the frontend configuration field
3. Ensured Inner Case EPCClass Generation: The inner case EPCClass generation logic was already correct, but should now work properly with the fixed product code mapping

Test configuration:
- company_prefix: "1234567" 
- product_code: "000000"
- sscc_extension_digit: "3"
- item_indicator_digit: "1"
- case_indicator_digit: "2"  
- inner_case_indicator_digit: "4"
- use_inner_cases: true

Expected results:
- Inner case EPCClass should appear in vocabulary with pattern: `urn:epc:idpat:sgtin:1234567.4000000.*`
- All SGTINs should show product code "000000" not "None"
- SSCC should show extension digit "3" not "None"
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

class EPCISCriticalIssuesTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        
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
    
    def setup_test_user(self):
        """Create a test user and get authentication token"""
        # Create test user
        user_data = {
            "email": "epcis_test@example.com",
            "password": "testpass123",
            "firstName": "EPCIS",
            "lastName": "Tester",
            "companyName": "Test Company",
            "streetAddress": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "postalCode": "12345",
            "countryCode": "US"
        }
        
        try:
            # Try to register (might fail if user exists)
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Login to get token
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("User Authentication", True, "Successfully authenticated test user")
                return True
            else:
                self.log_test("User Authentication", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Authentication error: {str(e)}")
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
    
    def create_test_project(self):
        """Create a test project for EPCIS testing"""
        try:
            project_data = {
                "name": "EPCIS Critical Issues Test Project"
            }
            
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                self.log_test("Project Creation", True, f"Created test project: {project['id']}")
                return project["id"]
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Request error: {str(e)}")
            return None
    
    def create_critical_issues_configuration(self, project_id):
        """Create configuration with the exact parameters from the review request"""
        if not project_id:
            self.log_test("Critical Issues Configuration", False, "No project ID available")
            return None
            
        # Configuration using current backend API structure but testing the fixes
        config_data = {
            "itemsPerCase": 0,  # Not used when inner cases enabled
            "casesPerSscc": 2,
            "numberOfSscc": 1,
            "useInnerCases": True,
            "innerCasesPerCase": 3,
            "itemsPerInnerCase": 4,
            "companyPrefix": "1234567",
            # Backend still expects separate product codes, but EPCIS generation should use single productCode
            "itemProductCode": "000000",
            "caseProductCode": "000000", 
            "innerCaseProductCode": "000000",
            "productCode": "000000",  # This should be used in EPCIS generation (CRITICAL FIX)
            "lotNumber": "LOT123456",
            "expirationDate": "2026-12-31",
            "ssccExtensionDigit": "3",  # Changed from ssccIndicatorDigit (CRITICAL FIX)
            "caseIndicatorDigit": "2",
            "innerCaseIndicatorDigit": "4",
            "itemIndicatorDigit": "1",
            # Business Document Information
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "senderName": "Test Sender Company",
            "senderStreetAddress": "123 Sender St",
            "senderCity": "Sender City",
            "senderState": "SC",
            "senderPostalCode": "12345",
            "senderCountryCode": "US",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Test Receiver Company",
            "receiverStreetAddress": "456 Receiver Ave",
            "receiverCity": "Receiver City",
            "receiverState": "RC",
            "receiverPostalCode": "67890",
            "receiverCountryCode": "US",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Test Shipper Corp",
            "shipperStreetAddress": "789 Shipper Blvd",
            "shipperCity": "Shipper City",
            "shipperState": "SH",
            "shipperPostalCode": "11111",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False,
            # EPCClass data
            "packageNdc": "45802-046-85",
            "regulatedProductName": "Test Pharmaceutical Product",
            "manufacturerName": "Test Pharma Inc",
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
                config = response.json()
                self.log_test("Critical Issues Configuration", True, 
                            "Configuration created with single productCode field and ssccExtensionDigit",
                            f"Project: {project_id}, Product Code: {config_data['productCode']}, SSCC Extension: {config_data['ssccExtensionDigit']}")
                return config
            else:
                self.log_test("Critical Issues Configuration", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Critical Issues Configuration", False, f"Request error: {str(e)}")
            return None
    
    def create_critical_issues_serial_numbers(self, project_id):
        """Create serial numbers for the critical issues test configuration"""
        if not project_id:
            self.log_test("Critical Issues Serial Numbers", False, "No project ID available")
            return None
            
        # For config: 1 SSCC, 2 Cases, 3 Inner Cases per Case, 4 Items per Inner Case
        # Expected: 1 SSCC, 2 Cases, 6 Inner Cases (2×3), 24 Items (4×3×2)
        serial_data = {
            "ssccSerialNumbers": ["TEST001"],
            "caseSerialNumbers": ["CASE001", "CASE002"],
            "innerCaseSerialNumbers": ["INNER001", "INNER002", "INNER003", "INNER004", "INNER005", "INNER006"],
            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(24)]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                serials = response.json()
                self.log_test("Critical Issues Serial Numbers", True, 
                            "Serial numbers created for 4-level hierarchy",
                            f"SSCC: {len(serials['sscc_serial_numbers'])}, Cases: {len(serials['case_serial_numbers'])}, Inner Cases: {len(serials['inner_case_serial_numbers'])}, Items: {len(serials['item_serial_numbers'])}")
                return serials
            else:
                self.log_test("Critical Issues Serial Numbers", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Critical Issues Serial Numbers", False, f"Request error: {str(e)}")
            return None
    
    def test_inner_case_epcclass_vocabulary(self, project_id):
        """Test Issue 1: Inner case not getting defined in EPCClass vocabulary"""
        if not project_id:
            self.log_test("Inner Case EPCClass Vocabulary", False, "No project ID available")
            return False
            
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json={
                    "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                    "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Parse XML to find EPCClass vocabulary elements
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find all VocabularyElement elements
                    vocabulary_elements = []
                    for elem in root.iter():
                        if elem.tag.endswith("VocabularyElement"):
                            vocab_id = elem.get("id")
                            if vocab_id and "sgtin" in vocab_id:
                                vocabulary_elements.append(vocab_id)
                    
                    # Expected inner case EPCClass pattern: urn:epc:idpat:sgtin:1234567.4000000.*
                    expected_inner_case_pattern = "urn:epc:idpat:sgtin:1234567.4000000.*"
                    
                    if expected_inner_case_pattern in vocabulary_elements:
                        self.log_test("Inner Case EPCClass Vocabulary", True, 
                                    "Inner case EPCClass vocabulary element found",
                                    f"Found pattern: {expected_inner_case_pattern}")
                        return True
                    else:
                        self.log_test("Inner Case EPCClass Vocabulary", False, 
                                    "CRITICAL: Inner case EPCClass vocabulary element missing",
                                    f"Expected: {expected_inner_case_pattern}, Found: {vocabulary_elements}")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("Inner Case EPCClass Vocabulary", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Inner Case EPCClass Vocabulary", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Inner Case EPCClass Vocabulary", False, f"Request error: {str(e)}")
            return False
    
    def test_product_code_none_values(self, project_id):
        """Test Issue 2: Product code showing 'None' instead of actual values in SGTINs"""
        if not project_id:
            self.log_test("Product Code None Values", False, "No project ID available")
            return False
            
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json={
                    "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                    "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Check for 'None' values in SGTINs
                none_found = "None" in xml_content
                dot_found = xml_content.count("sgtin:1234567..") > 0  # Check for double dots indicating missing product code
                
                # Check for correct product code "000000" in SGTINs
                correct_item_sgtin = "sgtin:1234567.1000000." in xml_content
                correct_case_sgtin = "sgtin:1234567.2000000." in xml_content
                correct_inner_case_sgtin = "sgtin:1234567.4000000." in xml_content
                
                if none_found or dot_found:
                    self.log_test("Product Code None Values", False, 
                                "CRITICAL: Product code showing 'None' or '.' in SGTINs",
                                f"None found: {none_found}, Double dots found: {dot_found}")
                    return False
                elif correct_item_sgtin and correct_case_sgtin and correct_inner_case_sgtin:
                    self.log_test("Product Code None Values", True, 
                                "Product code '000000' correctly populated in all SGTINs",
                                "Item, Case, and Inner Case SGTINs all show correct product code")
                    return True
                else:
                    self.log_test("Product Code None Values", False, 
                                "Product code not found in expected SGTIN patterns",
                                f"Item SGTIN: {correct_item_sgtin}, Case SGTIN: {correct_case_sgtin}, Inner Case SGTIN: {correct_inner_case_sgtin}")
                    return False
                    
            else:
                self.log_test("Product Code None Values", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Product Code None Values", False, f"Request error: {str(e)}")
            return False
    
    def test_sscc_extension_digit_none(self, project_id):
        """Test Issue 3: Extension digit on SSCC showing 'None' instead of actual value"""
        if not project_id:
            self.log_test("SSCC Extension Digit None", False, "No project ID available")
            return False
            
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json={
                    "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                    "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Check for 'None' in SSCC identifiers
                sscc_none_found = "sscc:0999888.None" in xml_content
                
                # Check for correct SSCC extension digit "3"
                correct_sscc = "sscc:0999888.3TEST001" in xml_content
                
                if sscc_none_found:
                    self.log_test("SSCC Extension Digit None", False, 
                                "CRITICAL: SSCC extension digit showing 'None'",
                                "Found 'sscc:shipperPrefix.None{serialNumber}' pattern")
                    return False
                elif correct_sscc:
                    self.log_test("SSCC Extension Digit None", True, 
                                "SSCC extension digit '3' correctly populated",
                                "Found correct SSCC pattern: urn:epc:id:sscc:0999888.3TEST001")
                    return True
                else:
                    self.log_test("SSCC Extension Digit None", False, 
                                "SSCC extension digit not found in expected pattern",
                                "Expected: sscc:0999888.3TEST001")
                    return False
                    
            else:
                self.log_test("SSCC Extension Digit None", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SSCC Extension Digit None", False, f"Request error: {str(e)}")
            return False
    
    def test_comprehensive_epcis_validation(self, project_id):
        """Comprehensive validation of all three critical issues in one EPCIS XML"""
        if not project_id:
            self.log_test("Comprehensive EPCIS Validation", False, "No project ID available")
            return False
            
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json={
                    "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                    "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Parse XML for comprehensive validation
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Issue 1: Check Inner Case EPCClass vocabulary
                    inner_case_epcclass_found = False
                    vocabulary_elements = []
                    for elem in root.iter():
                        if elem.tag.endswith("VocabularyElement"):
                            vocab_id = elem.get("id")
                            if vocab_id and "sgtin" in vocab_id:
                                vocabulary_elements.append(vocab_id)
                                if "urn:epc:idpat:sgtin:1234567.4000000.*" == vocab_id:
                                    inner_case_epcclass_found = True
                    
                    # Issue 2: Check for 'None' or missing product codes in SGTINs
                    none_in_sgtin = "None" in xml_content and "sgtin" in xml_content
                    dot_in_sgtin = xml_content.count("sgtin:1234567..") > 0
                    correct_product_codes = (
                        "sgtin:1234567.1000000." in xml_content and  # Item
                        "sgtin:1234567.2000000." in xml_content and  # Case
                        "sgtin:1234567.4000000." in xml_content      # Inner Case
                    )
                    
                    # Issue 3: Check for 'None' in SSCC extension digit
                    none_in_sscc = "sscc:0999888.None" in xml_content
                    correct_sscc_extension = "sscc:0999888.3TEST001" in xml_content
                    
                    # Validation results
                    issue1_resolved = inner_case_epcclass_found
                    issue2_resolved = correct_product_codes and not none_in_sgtin and not dot_in_sgtin
                    issue3_resolved = correct_sscc_extension and not none_in_sscc
                    
                    all_issues_resolved = issue1_resolved and issue2_resolved and issue3_resolved
                    
                    if all_issues_resolved:
                        self.log_test("Comprehensive EPCIS Validation", True, 
                                    "ALL THREE CRITICAL ISSUES RESOLVED",
                                    f"Issue 1 (Inner Case EPCClass): ✅, Issue 2 (Product Code): ✅, Issue 3 (SSCC Extension): ✅")
                        return True
                    else:
                        issues_status = []
                        issues_status.append(f"Issue 1 (Inner Case EPCClass): {'✅' if issue1_resolved else '❌'}")
                        issues_status.append(f"Issue 2 (Product Code): {'✅' if issue2_resolved else '❌'}")
                        issues_status.append(f"Issue 3 (SSCC Extension): {'✅' if issue3_resolved else '❌'}")
                        
                        self.log_test("Comprehensive EPCIS Validation", False, 
                                    "SOME CRITICAL ISSUES STILL PRESENT",
                                    ", ".join(issues_status))
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("Comprehensive EPCIS Validation", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Comprehensive EPCIS Validation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Comprehensive EPCIS Validation", False, f"Request error: {str(e)}")
            return False
    
    def run_critical_issues_tests(self):
        """Run all critical issues tests"""
        print("=" * 80)
        print("EPCIS CRITICAL ISSUES TESTING")
        print("=" * 80)
        print("Testing the three critical issues reported by the user:")
        print("1. Inner case not getting defined in EPCClass vocabulary")
        print("2. Product code showing 'None' instead of actual values in SGTINs")
        print("3. Extension digit on SSCC showing 'None' instead of actual value")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: User Authentication
        if not self.setup_test_user():
            print("\n❌ User authentication failed. Stopping tests.")
            return False
        
        # Test 3: Create Test Project
        project_id = self.create_test_project()
        if not project_id:
            print("\n❌ Project creation failed. Stopping tests.")
            return False
        
        # Test 4: Create Critical Issues Configuration
        config = self.create_critical_issues_configuration(project_id)
        if not config:
            print("\n❌ Configuration creation failed. Stopping tests.")
            return False
        
        # Test 5: Create Serial Numbers
        serials = self.create_critical_issues_serial_numbers(project_id)
        if not serials:
            print("\n❌ Serial numbers creation failed. Stopping tests.")
            return False
        
        # Test 6: Test Individual Critical Issues
        issue1_resolved = self.test_inner_case_epcclass_vocabulary(project_id)
        issue2_resolved = self.test_product_code_none_values(project_id)
        issue3_resolved = self.test_sscc_extension_digit_none(project_id)
        
        # Test 7: Comprehensive Validation
        all_resolved = self.test_comprehensive_epcis_validation(project_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("CRITICAL ISSUES TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical Issues Status
        print("\n" + "=" * 50)
        print("CRITICAL ISSUES RESOLUTION STATUS")
        print("=" * 50)
        print(f"Issue 1 - Inner Case EPCClass Vocabulary: {'✅ RESOLVED' if issue1_resolved else '❌ STILL FAILING'}")
        print(f"Issue 2 - Product Code 'None' Values: {'✅ RESOLVED' if issue2_resolved else '❌ STILL FAILING'}")
        print(f"Issue 3 - SSCC Extension Digit 'None': {'✅ RESOLVED' if issue3_resolved else '❌ STILL FAILING'}")
        print(f"Overall Status: {'✅ ALL ISSUES RESOLVED' if all_resolved else '❌ SOME ISSUES REMAIN'}")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nTest Configuration Used:")
        print("- company_prefix: '1234567'")
        print("- product_code: '000000' (single field for all packaging levels)")
        print("- sscc_extension_digit: '3' (changed from ssccIndicatorDigit)")
        print("- item_indicator_digit: '1'")
        print("- case_indicator_digit: '2'")
        print("- inner_case_indicator_digit: '4'")
        print("- use_inner_cases: true")
        print("- 4-level hierarchy: 1 SSCC → 2 Cases → 6 Inner Cases → 24 Items")
        
        return all_resolved

if __name__ == "__main__":
    tester = EPCISCriticalIssuesTester()
    success = tester.run_critical_issues_tests()
    sys.exit(0 if success else 1)