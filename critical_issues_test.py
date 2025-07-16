#!/usr/bin/env python3
"""
Critical Issues Testing for EPCIS Serial Number Aggregation App
Tests the three specific issues reported in the review request:

1. **Location vocabulary elements** - Should be populated with complete address information
2. **SSCC using shipper company prefix** - Should use shipper_company_prefix for SSCC generation
3. **SBDH structure** - Should have proper business document header with sender/receiver GLN

Test Configuration (from review request):
- itemsPerCase: 2, casesPerSscc: 1, numberOfSscc: 1, useInnerCases: false
- shipperCompanyPrefix: "0999888" (should be used for SSCC generation)
- Complete address information for sender, receiver, and shipper
- Serial numbers: ssccSerialNumbers: ["TEST001"], caseSerialNumbers: ["CASE001"], itemSerialNumbers: ["ITEM001", "ITEM002"]
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://443af6fc-0d8a-42dd-a86d-aab66f8c129f.preview.emergentagent.com/api"

class CriticalIssuesTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        
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
    
    def create_review_request_configuration(self):
        """Create configuration with exact review request parameters"""
        test_data = {
            "itemsPerCase": 2,
            "casesPerSscc": 1,
            "numberOfSscc": 1,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000001",
            "lotNumber": "LOT123",
            "expirationDate": "2025-12-31",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "senderName": "Padagis US LLC",
            "senderStreetAddress": "1251 Lincoln Rd",
            "senderCity": "Allegan",
            "senderState": "MI",
            "senderPostalCode": "49010",
            "senderCountryCode": "US",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Pharmacy Corp",
            "receiverStreetAddress": "123 Main St",
            "receiverCity": "New York",
            "receiverState": "NY",
            "receiverPostalCode": "10001",
            "receiverCountryCode": "US",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Shipping Corp",
            "shipperStreetAddress": "456 Shipping Ave",
            "shipperCity": "Chicago",
            "shipperState": "IL",
            "shipperPostalCode": "60007",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False,
            "packageNdc": "45802-046-85"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Verify key fields are stored correctly
                if (data.get("shipperCompanyPrefix") == "0999888" and 
                    data.get("senderGln") == "0345802000014" and
                    data.get("receiverGln") == "0567890000021"):
                    self.log_test("Review Request Configuration", True, "Configuration created with business document fields", 
                                f"ID: {data['id']}, Shipper Prefix: {data['shipperCompanyPrefix']}")
                    return data["id"]
                else:
                    self.log_test("Review Request Configuration", False, f"Business document fields mismatch")
                    return None
            else:
                self.log_test("Review Request Configuration", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Review Request Configuration", False, f"Request error: {str(e)}")
            return None

    def create_review_request_serial_numbers(self, config_id):
        """Create serial numbers with exact review request data"""
        if not config_id:
            self.log_test("Review Request Serial Numbers", False, "No configuration ID available")
            return None
            
        test_data = {
            "configurationId": config_id,
            "ssccSerialNumbers": ["TEST001"],
            "caseSerialNumbers": ["CASE001"],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": ["ITEM001", "ITEM002"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (len(data["ssccSerialNumbers"]) == 1 and 
                    len(data["caseSerialNumbers"]) == 1 and
                    len(data["itemSerialNumbers"]) == 2):
                    self.log_test("Review Request Serial Numbers", True, "Serial numbers saved correctly",
                                f"SSCC: {data['ssccSerialNumbers']}, Case: {data['caseSerialNumbers']}, Items: {data['itemSerialNumbers']}")
                    return data["id"]
                else:
                    self.log_test("Review Request Serial Numbers", False, f"Serial count mismatch")
                    return None
            else:
                self.log_test("Review Request Serial Numbers", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Review Request Serial Numbers", False, f"Request error: {str(e)}")
            return None

    def test_location_vocabulary_elements(self, config_id):
        """Test that location vocabulary elements are populated with complete address information"""
        if not config_id:
            self.log_test("Location Vocabulary Elements", False, "No configuration ID available")
            return False
            
        test_data = {
            "configurationId": config_id,
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find Location vocabulary
                    location_vocabulary_found = False
                    location_elements = []
                    
                    for elem in root.iter():
                        if elem.tag.endswith("Vocabulary") and elem.get("type") == "urn:epcglobal:epcis:vtype:Location":
                            location_vocabulary_found = True
                            # Find VocabularyElementList
                            for child in elem.iter():
                                if child.tag.endswith("VocabularyElement"):
                                    element_id = child.get("id")
                                    if element_id:
                                        location_elements.append(element_id)
                    
                    if not location_vocabulary_found:
                        self.log_test("Location Vocabulary Elements", False, "Location vocabulary not found in EPCIS XML")
                        return False
                    
                    # Expected location elements (6 total: sender_gln, sender_sgln, receiver_gln, receiver_sgln, shipper_gln, shipper_sgln)
                    expected_elements = [
                        "urn:epc:id:sgln:0345802000014",      # sender_gln
                        "urn:epc:id:sgln:0345802000014.001",  # sender_sgln
                        "urn:epc:id:sgln:0567890000021",      # receiver_gln
                        "urn:epc:id:sgln:0567890000021.001",  # receiver_sgln
                        "urn:epc:id:sgln:0999888000028",      # shipper_gln
                        "urn:epc:id:sgln:0999888000028.001"   # shipper_sgln
                    ]
                    
                    missing_elements = []
                    for expected in expected_elements:
                        if expected not in location_elements:
                            missing_elements.append(expected)
                    
                    if len(missing_elements) == 0:
                        # Now check for complete address information
                        address_complete = self.verify_complete_address_information(root)
                        if address_complete:
                            self.log_test("Location Vocabulary Elements", True, f"All 6 location elements present with complete address information",
                                        f"Found: {location_elements}")
                            return True
                        else:
                            self.log_test("Location Vocabulary Elements", False, "Location elements missing complete address information")
                            return False
                    else:
                        self.log_test("Location Vocabulary Elements", False, f"Missing location elements: {missing_elements}",
                                    f"Found: {location_elements}")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("Location Vocabulary Elements", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Location Vocabulary Elements", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Location Vocabulary Elements", False, f"Request error: {str(e)}")
            return False

    def verify_complete_address_information(self, root):
        """Verify that location vocabulary elements contain complete address information"""
        try:
            # Expected address attributes for each location
            expected_attributes = [
                "urn:epcglobal:cbv:mda#name",
                "urn:epcglobal:cbv:mda#streetAddressOne", 
                "urn:epcglobal:cbv:mda#city",
                "urn:epcglobal:cbv:mda#state",
                "urn:epcglobal:cbv:mda#postalCode",
                "urn:epcglobal:cbv:mda#countryCode"
            ]
            
            location_elements_with_addresses = 0
            
            for elem in root.iter():
                if elem.tag.endswith("VocabularyElement") and elem.get("id", "").startswith("urn:epc:id:sgln:"):
                    # Count attributes for this location element
                    found_attributes = []
                    for child in elem:
                        if child.tag.endswith("attribute"):
                            attr_id = child.get("id")
                            if attr_id in expected_attributes:
                                found_attributes.append(attr_id)
                    
                    # Check if this location has complete address information
                    if len(found_attributes) >= 5:  # At least name, street, city, state, postal, country
                        location_elements_with_addresses += 1
            
            # We expect 6 location elements, all with complete address information
            return location_elements_with_addresses >= 6
            
        except Exception as e:
            print(f"Error verifying address information: {str(e)}")
            return False

    def test_sscc_using_shipper_company_prefix(self, config_id):
        """Test that SSCC uses shipper company prefix for generation"""
        if not config_id:
            self.log_test("SSCC Using Shipper Company Prefix", False, "No configuration ID available")
            return False
            
        test_data = {
            "configurationId": config_id,
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Expected SSCC format: urn:epc:id:sscc:0999888.3TEST001 (shipper prefix)
                expected_sscc = "urn:epc:id:sscc:0999888.3TEST001"
                
                if expected_sscc in xml_content:
                    # Also verify it's NOT using the regular company prefix
                    wrong_sscc = "urn:epc:id:sscc:1234567.3TEST001"
                    if wrong_sscc not in xml_content:
                        self.log_test("SSCC Using Shipper Company Prefix", True, "SSCC correctly uses shipper company prefix",
                                    f"Found: {expected_sscc}")
                        return True
                    else:
                        self.log_test("SSCC Using Shipper Company Prefix", False, "SSCC uses regular company prefix instead of shipper prefix")
                        return False
                else:
                    self.log_test("SSCC Using Shipper Company Prefix", False, f"Expected SSCC not found: {expected_sscc}")
                    return False
            else:
                self.log_test("SSCC Using Shipper Company Prefix", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SSCC Using Shipper Company Prefix", False, f"Request error: {str(e)}")
            return False

    def test_sbdh_structure(self, config_id):
        """Test that SBDH structure has proper business document header with sender/receiver GLN"""
        if not config_id:
            self.log_test("SBDH Structure", False, "No configuration ID available")
            return False
            
        test_data = {
            "configurationId": config_id,
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Check root element is StandardBusinessDocument (with or without namespace)
                    if not root.tag.endswith("StandardBusinessDocument"):
                        self.log_test("SBDH Structure", False, f"Root element should be StandardBusinessDocument, found: {root.tag}")
                        return False
                    
                    # Check for proper namespaces
                    expected_namespaces = [
                        "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader",
                        "urn:epcglobal:epcis:xsd:1",
                        "http://www.w3.org/2001/XMLSchema-instance"
                    ]
                    
                    # Get the full XML content as string to check namespaces
                    namespace_check = True
                    for ns in expected_namespaces:
                        if ns not in xml_content:
                            namespace_check = False
                            break
                    
                    if not namespace_check:
                        self.log_test("SBDH Structure", False, "Missing required namespaces in root element")
                        return False
                    
                    # Check for StandardBusinessDocumentHeader
                    sbdh_found = False
                    sender_gln_found = False
                    receiver_gln_found = False
                    
                    for elem in root.iter():
                        if elem.tag.endswith("StandardBusinessDocumentHeader"):
                            sbdh_found = True
                        elif elem.tag.endswith("Sender"):
                            for child in elem:
                                if child.tag.endswith("Identifier") and child.text == "0345802000014":
                                    sender_gln_found = True
                        elif elem.tag.endswith("Receiver"):
                            for child in elem:
                                if child.tag.endswith("Identifier") and child.text == "0567890000021":
                                    receiver_gln_found = True
                    
                    if sbdh_found and sender_gln_found and receiver_gln_found:
                        self.log_test("SBDH Structure", True, "SBDH structure correct with proper sender/receiver GLN",
                                    "StandardBusinessDocumentHeader present with sender GLN (0345802000014) and receiver GLN (0567890000021)")
                        return True
                    else:
                        missing_parts = []
                        if not sbdh_found:
                            missing_parts.append("StandardBusinessDocumentHeader")
                        if not sender_gln_found:
                            missing_parts.append("Sender GLN (0345802000014)")
                        if not receiver_gln_found:
                            missing_parts.append("Receiver GLN (0567890000021)")
                        
                        self.log_test("SBDH Structure", False, f"SBDH structure incomplete. Missing: {missing_parts}")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("SBDH Structure", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("SBDH Structure", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SBDH Structure", False, f"Request error: {str(e)}")
            return False

    def run_critical_issues_tests(self):
        """Run tests focused on the three critical issues from review request"""
        print("=" * 80)
        print("CRITICAL ISSUES TESTING - REVIEW REQUEST VERIFICATION")
        print("=" * 80)
        print("Testing the three specific issues reported:")
        print("1. Location vocabulary elements - Should be populated with complete address information")
        print("2. SSCC using shipper company prefix - Should use shipper_company_prefix for SSCC generation")
        print("3. SBDH structure - Should have proper business document header with sender/receiver GLN")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Create Review Request Configuration
        config_id = self.create_review_request_configuration()
        if not config_id:
            print("\n❌ Could not create configuration. Stopping tests.")
            return False
        
        # Test 3: Create Review Request Serial Numbers
        serial_id = self.create_review_request_serial_numbers(config_id)
        if not serial_id:
            print("\n❌ Could not create serial numbers. Stopping tests.")
            return False
        
        # Test 4: CRITICAL ISSUE 1 - Location vocabulary elements
        location_vocab_success = self.test_location_vocabulary_elements(config_id)
        
        # Test 5: CRITICAL ISSUE 2 - SSCC using shipper company prefix
        sscc_prefix_success = self.test_sscc_using_shipper_company_prefix(config_id)
        
        # Test 6: CRITICAL ISSUE 3 - SBDH structure
        sbdh_structure_success = self.test_sbdh_structure(config_id)
        
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
        print("CRITICAL ISSUES STATUS")
        print("=" * 50)
        print(f"1. Location Vocabulary Elements: {'✅ WORKING' if location_vocab_success else '❌ FAILING'}")
        print(f"2. SSCC Using Shipper Company Prefix: {'✅ WORKING' if sscc_prefix_success else '❌ FAILING'}")
        print(f"3. SBDH Structure: {'✅ WORKING' if sbdh_structure_success else '❌ FAILING'}")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nTest Configuration Used:")
        print("- itemsPerCase: 2, casesPerSscc: 1, numberOfSscc: 1, useInnerCases: false")
        print("- shipperCompanyPrefix: '0999888' (should be used for SSCC generation)")
        print("- Complete address information for sender, receiver, and shipper")
        print("- Serial numbers: ssccSerialNumbers: ['TEST001'], caseSerialNumbers: ['CASE001'], itemSerialNumbers: ['ITEM001', 'ITEM002']")
        
        # Overall result
        all_critical_issues_resolved = location_vocab_success and sscc_prefix_success and sbdh_structure_success
        
        print(f"\n{'✅ ALL CRITICAL ISSUES RESOLVED' if all_critical_issues_resolved else '❌ SOME CRITICAL ISSUES STILL FAILING'}")
        
        return all_critical_issues_resolved

if __name__ == "__main__":
    tester = CriticalIssuesTester()
    success = tester.run_critical_issues_tests()
    sys.exit(0 if success else 1)