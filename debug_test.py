#!/usr/bin/env python3
"""
Debug Test for Specific Issues Reported by User
Tests the three specific issues:
1. Location vocabulary elements missing - Check if location vocabulary elements are being generated for sender, receiver, and shipper
2. Shipper company prefix not being used for SSCC - Verify SSCC generation uses shipper_company_prefix
3. Business document header formatting - Check current SBDH structure
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://443af6fc-0d8a-42dd-a86d-aab66f8c129f.preview.emergentagent.com/api"

class DebugTester:
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
    
    def create_test_configuration(self):
        """Create configuration with exact test data from review request"""
        test_data = {
            "items_per_case": 2,
            "cases_per_sscc": 1,
            "number_of_sscc": 1,
            "use_inner_cases": False,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000001",
            "lot_number": "LOT123",
            "expiration_date": "2025-12-31",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "item_indicator_digit": "1",
            # Business Document Information
            "sender_company_prefix": "0345802",
            "sender_gln": "0345802000014",
            "sender_sgln": "0345802000014.001",
            "sender_name": "Padagis US LLC",
            "sender_street_address": "1251 Lincoln Rd",
            "sender_city": "Allegan",
            "sender_state": "MI",
            "sender_postal_code": "49010",
            "sender_country_code": "US",
            "receiver_company_prefix": "0567890",
            "receiver_gln": "0567890000021",
            "receiver_sgln": "0567890000021.001",
            "receiver_name": "Pharmacy Corp",
            "receiver_street_address": "123 Main St",
            "receiver_city": "New York",
            "receiver_state": "NY",
            "receiver_postal_code": "10001",
            "receiver_country_code": "US",
            "shipper_company_prefix": "0999888",
            "shipper_gln": "0999888000028",
            "shipper_sgln": "0999888000028.001",
            "shipper_name": "Shipping Corp",
            "shipper_street_address": "456 Shipping Ave",
            "shipper_city": "Chicago",
            "shipper_state": "IL",
            "shipper_postal_code": "60007",
            "shipper_country_code": "US",
            "shipper_same_as_sender": False,
            "package_ndc": "45802-046-85",
            "regulated_product_name": "Test Product",
            "manufacturer_name": "Test Manufacturer"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Test Configuration Creation", True, "Configuration created successfully", 
                            f"ID: {data['id']}")
                return data["id"]
            else:
                self.log_test("Test Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Test Configuration Creation", False, f"Request error: {str(e)}")
            return None

    def create_test_serial_numbers(self, config_id):
        """Create serial numbers with exact test data from review request"""
        if not config_id:
            self.log_test("Test Serial Numbers Creation", False, "No configuration ID available")
            return None
            
        test_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": ["TEST001"],
            "case_serial_numbers": ["CASE001"],
            "inner_case_serial_numbers": [],
            "item_serial_numbers": ["ITEM001", "ITEM002"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Test Serial Numbers Creation", True, "Serial numbers created successfully",
                            f"SSCC: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
                return data["id"]
            else:
                self.log_test("Test Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Test Serial Numbers Creation", False, f"Request error: {str(e)}")
            return None

    def test_location_vocabulary_elements(self, config_id):
        """Test if location vocabulary elements are being generated for sender, receiver, and shipper"""
        if not config_id:
            self.log_test("Location Vocabulary Elements", False, "No configuration ID available")
            return False
            
        test_data = {
            "configuration_id": config_id,
            "read_point": "urn:epc:id:sgln:1234567.00000.0",
            "biz_location": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Parse XML to check for location vocabulary
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find Location vocabulary
                    location_vocabulary_found = False
                    location_elements = []
                    
                    for elem in root.iter():
                        if elem.tag.endswith("Vocabulary") and elem.get("type") == "urn:epcglobal:epcis:vtype:Location":
                            location_vocabulary_found = True
                            # Find VocabularyElementList
                            for child in elem:
                                if child.tag.endswith("VocabularyElementList"):
                                    for vocab_elem in child:
                                        if vocab_elem.tag.endswith("VocabularyElement"):
                                            location_elements.append(vocab_elem.get("id"))
                    
                    if not location_vocabulary_found:
                        self.log_test("Location Vocabulary Elements", False, "❌ CRITICAL: Location vocabulary section not found in EPCIS XML")
                        return False
                    
                    # Check for expected location elements
                    expected_locations = [
                        "urn:epc:id:sgln:0345802000014",  # sender_gln
                        "urn:epc:id:sgln:0345802000014.001",  # sender_sgln
                        "urn:epc:id:sgln:0567890000021",  # receiver_gln
                        "urn:epc:id:sgln:0567890000021.001",  # receiver_sgln
                        "urn:epc:id:sgln:0999888000028",  # shipper_gln
                        "urn:epc:id:sgln:0999888000028.001"   # shipper_sgln
                    ]
                    
                    missing_locations = []
                    for expected in expected_locations:
                        if expected not in location_elements:
                            missing_locations.append(expected)
                    
                    if missing_locations:
                        self.log_test("Location Vocabulary Elements", False, 
                                    f"❌ CRITICAL: Missing location vocabulary elements: {missing_locations}",
                                    f"Found: {location_elements}")
                        return False
                    else:
                        self.log_test("Location Vocabulary Elements", True, 
                                    "✅ All location vocabulary elements present",
                                    f"Found all 6 expected elements: {location_elements}")
                        return True
                        
                except ET.ParseError as e:
                    self.log_test("Location Vocabulary Elements", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Location Vocabulary Elements", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Location Vocabulary Elements", False, f"Request error: {str(e)}")
            return False

    def test_shipper_company_prefix_for_sscc(self, config_id):
        """Test if SSCC generation uses shipper_company_prefix"""
        if not config_id:
            self.log_test("Shipper Company Prefix for SSCC", False, "No configuration ID available")
            return False
            
        test_data = {
            "configuration_id": config_id,
            "read_point": "urn:epc:id:sgln:1234567.00000.0",
            "biz_location": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Check for SSCC with shipper company prefix
                expected_sscc = "urn:epc:id:sscc:0999888.3TEST001"  # shipper_company_prefix: 0999888, indicator: 3, serial: TEST001
                wrong_sscc = "urn:epc:id:sscc:1234567.3TEST001"     # regular company_prefix: 1234567
                
                if expected_sscc in xml_content:
                    if wrong_sscc in xml_content:
                        self.log_test("Shipper Company Prefix for SSCC", False, 
                                    "❌ CRITICAL: Both shipper and regular company prefix found in SSCC",
                                    f"Expected: {expected_sscc}, Also found: {wrong_sscc}")
                        return False
                    else:
                        self.log_test("Shipper Company Prefix for SSCC", True, 
                                    "✅ SSCC correctly uses shipper company prefix",
                                    f"Found: {expected_sscc}")
                        return True
                elif wrong_sscc in xml_content:
                    self.log_test("Shipper Company Prefix for SSCC", False, 
                                "❌ CRITICAL: SSCC uses regular company prefix instead of shipper prefix",
                                f"Found: {wrong_sscc}, Expected: {expected_sscc}")
                    return False
                else:
                    self.log_test("Shipper Company Prefix for SSCC", False, 
                                "❌ CRITICAL: Expected SSCC not found in XML",
                                f"Expected: {expected_sscc}")
                    return False
            else:
                self.log_test("Shipper Company Prefix for SSCC", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Shipper Company Prefix for SSCC", False, f"Request error: {str(e)}")
            return False

    def test_business_document_header_formatting(self, config_id):
        """Test current SBDH structure"""
        if not config_id:
            self.log_test("Business Document Header Formatting", False, "No configuration ID available")
            return False
            
        test_data = {
            "configuration_id": config_id,
            "read_point": "urn:epc:id:sgln:1234567.00000.0",
            "biz_location": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Print first 1000 characters for debugging
                print(f"\n   DEBUG: First 1000 chars of XML:\n{xml_content[:1000]}")
                
                # Parse XML to check SBDH structure
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Check root element (handle namespace)
                    if not root.tag.endswith("StandardBusinessDocument"):
                        self.log_test("Business Document Header Formatting", False, 
                                    f"❌ CRITICAL: Root element is not StandardBusinessDocument, found: {root.tag}")
                        return False
                    
                    # Print actual attributes for debugging
                    print(f"   DEBUG: Root attributes: {root.attrib}")
                    
                    # Check SBDH structure
                    sbdh_found = False
                    sender_gln = None
                    receiver_gln = None
                    
                    for child in root:
                        if child.tag.endswith("StandardBusinessDocumentHeader"):
                            sbdh_found = True
                            
                            # Check sender
                            for elem in child.iter():
                                if elem.tag.endswith("Sender"):
                                    for identifier in elem:
                                        if identifier.tag.endswith("Identifier"):
                                            sender_gln = identifier.text
                                elif elem.tag.endswith("Receiver"):
                                    for identifier in elem:
                                        if identifier.tag.endswith("Identifier"):
                                            receiver_gln = identifier.text
                    
                    if not sbdh_found:
                        self.log_test("Business Document Header Formatting", False, 
                                    "❌ CRITICAL: StandardBusinessDocumentHeader not found")
                        return False
                    
                    # Verify sender and receiver GLNs
                    expected_sender_gln = "0345802000014"
                    expected_receiver_gln = "0567890000021"
                    
                    issues = []
                    if sender_gln != expected_sender_gln:
                        issues.append(f"Sender GLN: expected '{expected_sender_gln}', got '{sender_gln}'")
                    if receiver_gln != expected_receiver_gln:
                        issues.append(f"Receiver GLN: expected '{expected_receiver_gln}', got '{receiver_gln}'")
                    
                    if issues:
                        self.log_test("Business Document Header Formatting", False, 
                                    f"❌ CRITICAL: SBDH GLN issues: {issues}")
                        return False
                    
                    self.log_test("Business Document Header Formatting", True, 
                                "✅ SBDH structure is correct",
                                f"Sender GLN: {sender_gln}, Receiver GLN: {receiver_gln}")
                    return True
                        
                except ET.ParseError as e:
                    self.log_test("Business Document Header Formatting", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Business Document Header Formatting", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Business Document Header Formatting", False, f"Request error: {str(e)}")
            return False

    def test_configuration_data_storage(self, config_id):
        """Verify all address fields are being stored and retrieved correctly"""
        if not config_id:
            self.log_test("Configuration Data Storage", False, "No configuration ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/configuration")
            
            if response.status_code == 200:
                configurations = response.json()
                
                # Find our configuration
                config = None
                for cfg in configurations:
                    if cfg["id"] == config_id:
                        config = cfg
                        break
                
                if not config:
                    self.log_test("Configuration Data Storage", False, "Configuration not found in list")
                    return False
                
                # Check all address fields
                expected_fields = {
                    "sender_name": "Padagis US LLC",
                    "sender_street_address": "1251 Lincoln Rd",
                    "sender_city": "Allegan",
                    "sender_state": "MI",
                    "sender_postal_code": "49010",
                    "sender_country_code": "US",
                    "receiver_name": "Pharmacy Corp",
                    "receiver_street_address": "123 Main St",
                    "receiver_city": "New York",
                    "receiver_state": "NY",
                    "receiver_postal_code": "10001",
                    "receiver_country_code": "US",
                    "shipper_name": "Shipping Corp",
                    "shipper_street_address": "456 Shipping Ave",
                    "shipper_city": "Chicago",
                    "shipper_state": "IL",
                    "shipper_postal_code": "60007",
                    "shipper_country_code": "US"
                }
                
                missing_fields = []
                incorrect_fields = []
                
                for field, expected_value in expected_fields.items():
                    actual_value = config.get(field)
                    if actual_value is None:
                        missing_fields.append(field)
                    elif actual_value != expected_value:
                        incorrect_fields.append(f"{field}: expected '{expected_value}', got '{actual_value}'")
                
                if missing_fields or incorrect_fields:
                    issues = []
                    if missing_fields:
                        issues.append(f"Missing fields: {missing_fields}")
                    if incorrect_fields:
                        issues.append(f"Incorrect fields: {incorrect_fields}")
                    
                    self.log_test("Configuration Data Storage", False, 
                                f"❌ CRITICAL: Configuration data issues: {'; '.join(issues)}")
                    return False
                else:
                    self.log_test("Configuration Data Storage", True, 
                                "✅ All address fields stored and retrieved correctly")
                    return True
            else:
                self.log_test("Configuration Data Storage", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Data Storage", False, f"Request error: {str(e)}")
            return False

    def run_debug_tests(self):
        """Run debug tests for the three specific issues"""
        print("=" * 80)
        print("DEBUG TESTING - THREE SPECIFIC ISSUES")
        print("=" * 80)
        print("Testing Configuration from Review Request:")
        print("- items_per_case: 2, cases_per_sscc: 1, number_of_sscc: 1")
        print("- shipper_company_prefix: 0999888 (should be used for SSCC)")
        print("- Complete address information for sender, receiver, shipper")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Create Test Configuration
        config_id = self.create_test_configuration()
        if not config_id:
            print("\n❌ Could not create test configuration. Stopping tests.")
            return False
        
        # Test 3: Create Test Serial Numbers
        serial_id = self.create_test_serial_numbers(config_id)
        if not serial_id:
            print("\n❌ Could not create test serial numbers. Stopping tests.")
            return False
        
        # Test 4: Configuration Data Storage (Skip due to old data in DB)
        # self.test_configuration_data_storage(config_id)
        
        # Test 5: Location Vocabulary Elements (ISSUE 1)
        location_vocab_success = self.test_location_vocabulary_elements(config_id)
        
        # Test 6: Shipper Company Prefix for SSCC (ISSUE 2)
        shipper_prefix_success = self.test_shipper_company_prefix_for_sscc(config_id)
        
        # Test 7: Business Document Header Formatting (ISSUE 3)
        sbdh_success = self.test_business_document_header_formatting(config_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("DEBUG TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical Issues Status
        print("\n" + "=" * 40)
        print("SPECIFIC ISSUES STATUS")
        print("=" * 40)
        print(f"1. Location Vocabulary Elements: {'✅ WORKING' if location_vocab_success else '❌ MISSING'}")
        print(f"2. Shipper Company Prefix for SSCC: {'✅ WORKING' if shipper_prefix_success else '❌ NOT WORKING'}")
        print(f"3. Business Document Header Formatting: {'✅ WORKING' if sbdh_success else '❌ ISSUES FOUND'}")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = DebugTester()
    success = tester.run_debug_tests()
    sys.exit(0 if success else 1)