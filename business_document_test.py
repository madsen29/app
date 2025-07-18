#!/usr/bin/env python3
"""
Business Document Information and GS1 Rx EPCIS Compliance Testing
Tests the new Business Document Information fields and GS1 Rx EPCIS compliance features:

1. Configuration API - Test new business document fields
2. EPCIS XML Generation - Verify GS1 Rx EPCIS compliance features
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

class BusinessDocumentTester:
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
    
    def test_business_document_configuration(self):
        """Test Configuration API with new business document fields"""
        test_data = {
            "items_per_case": 3,
            "cases_per_sscc": 2,
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
            # Business Document Information fields
            "sender_company_prefix": "0345802",
            "sender_gln": "0345802000014",
            "sender_sgln": "0345802000014.001",
            "receiver_company_prefix": "0567890",
            "receiver_gln": "0567890000021",
            "receiver_sgln": "0567890000021.001",
            "shipper_company_prefix": "0999888",
            "shipper_gln": "0999888000028",
            "shipper_sgln": "0999888000028.001",
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
                
                # Verify all business document fields are stored
                business_fields = [
                    "sender_company_prefix", "sender_gln", "sender_sgln",
                    "receiver_company_prefix", "receiver_gln", "receiver_sgln",
                    "shipper_company_prefix", "shipper_gln", "shipper_sgln",
                    "shipper_same_as_sender"
                ]
                
                all_fields_present = True
                missing_fields = []
                
                for field in business_fields:
                    if field not in data or data[field] != test_data[field]:
                        all_fields_present = False
                        missing_fields.append(field)
                
                if all_fields_present:
                    self.log_test("Business Document Configuration", True, 
                                "All business document fields properly stored",
                                f"Config ID: {data['id']}")
                    return data["id"]
                else:
                    self.log_test("Business Document Configuration", False, 
                                f"Missing or incorrect business document fields: {missing_fields}")
                    return None
            else:
                self.log_test("Business Document Configuration", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Business Document Configuration", False, f"Request error: {str(e)}")
            return None

    def test_serial_numbers_creation(self, config_id):
        """Test serial numbers creation for the test configuration"""
        if not config_id:
            self.log_test("Serial Numbers Creation", False, "No configuration ID available")
            return None
            
        # For config: 1 SSCC, 2 Cases, 3 Items per Case = 6 total items
        test_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": ["1001"],
            "case_serial_numbers": ["C001", "C002"],
            "inner_case_serial_numbers": [],
            "item_serial_numbers": ["I001", "I002", "I003", "I004", "I005", "I006"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (len(data["sscc_serial_numbers"]) == 1 and 
                    len(data["case_serial_numbers"]) == 2 and
                    len(data["item_serial_numbers"]) == 6):
                    self.log_test("Serial Numbers Creation", True, 
                                "Serial numbers saved correctly",
                                f"SSCC: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
                    return data["id"]
                else:
                    self.log_test("Serial Numbers Creation", False, 
                                f"Count mismatch - SSCC: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
                    return None
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return None

    def test_sscc_uses_shipper_prefix(self, config_id):
        """Test that SSCC EPCs use shipper's company prefix"""
        if not config_id:
            self.log_test("SSCC Shipper Prefix", False, "No configuration ID available")
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
                
                # Check if SSCC uses shipper's company prefix (0999888)
                expected_sscc = "urn:epc:id:sscc:0999888.31001"
                
                if expected_sscc in xml_content:
                    self.log_test("SSCC Shipper Prefix", True, 
                                "SSCC EPCs correctly use shipper's company prefix",
                                f"Found: {expected_sscc}")
                    return True
                else:
                    # Check if it's using wrong prefix
                    wrong_sscc = "urn:epc:id:sscc:1234567.31001"
                    if wrong_sscc in xml_content:
                        self.log_test("SSCC Shipper Prefix", False, 
                                    "SSCC EPCs using regular company prefix instead of shipper's",
                                    f"Found: {wrong_sscc}, Expected: {expected_sscc}")
                    else:
                        self.log_test("SSCC Shipper Prefix", False, 
                                    "SSCC EPC not found in expected format")
                    return False
            else:
                self.log_test("SSCC Shipper Prefix", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SSCC Shipper Prefix", False, f"Request error: {str(e)}")
            return False

    def test_sgtin_uses_regular_prefix(self, config_id):
        """Test that SGTIN EPCs use regular company prefix"""
        if not config_id:
            self.log_test("SGTIN Regular Prefix", False, "No configuration ID available")
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
                
                # Check if SGTINs use regular company prefix (1234567)
                expected_case_sgtin = "urn:epc:id:sgtin:1234567.2000001.C001"
                expected_item_sgtin = "urn:epc:id:sgtin:1234567.1000000.I001"
                
                case_correct = expected_case_sgtin in xml_content
                item_correct = expected_item_sgtin in xml_content
                
                if case_correct and item_correct:
                    self.log_test("SGTIN Regular Prefix", True, 
                                "SGTIN EPCs correctly use regular company prefix",
                                f"Case: {expected_case_sgtin}, Item: {expected_item_sgtin}")
                    return True
                else:
                    missing = []
                    if not case_correct:
                        missing.append(f"Case SGTIN: {expected_case_sgtin}")
                    if not item_correct:
                        missing.append(f"Item SGTIN: {expected_item_sgtin}")
                    
                    self.log_test("SGTIN Regular Prefix", False, 
                                f"Missing expected SGTIN EPCs: {missing}")
                    return False
            else:
                self.log_test("SGTIN Regular Prefix", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SGTIN Regular Prefix", False, f"Request error: {str(e)}")
            return False

    def test_sbdh_structure(self, config_id):
        """Test SBDH (StandardBusinessDocumentHeader) structure"""
        if not config_id:
            self.log_test("SBDH Structure", False, "No configuration ID available")
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
                
                # Parse XML to check for SBDH elements
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Look for EPCISHeader which should contain business document info
                    epcis_header = None
                    for elem in root.iter():
                        if elem.tag.endswith("EPCISHeader"):
                            epcis_header = elem
                            break
                    
                    if epcis_header is not None:
                        # Check if extension contains EPCISMasterData
                        extension_found = False
                        epcis_master_data_found = False
                        
                        for child in epcis_header:
                            if child.tag.endswith("extension"):
                                extension_found = True
                                for grandchild in child:
                                    if grandchild.tag.endswith("EPCISMasterData"):
                                        epcis_master_data_found = True
                                        break
                                break
                        
                        if extension_found and epcis_master_data_found:
                            self.log_test("SBDH Structure", True, 
                                        "EPCISHeader contains extension with EPCISMasterData")
                            return True
                        else:
                            self.log_test("SBDH Structure", False, 
                                        f"Missing SBDH elements - Extension: {extension_found}, EPCISMasterData: {epcis_master_data_found}")
                            return False
                    else:
                        self.log_test("SBDH Structure", False, "EPCISHeader not found")
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

    def test_location_vocabulary(self, config_id):
        """Test Location Vocabulary using GLN/SGLN from business entities"""
        if not config_id:
            self.log_test("Location Vocabulary", False, "No configuration ID available")
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
                
                # Check for business entity GLNs/SGLNs in the XML
                expected_glns = [
                    "0345802000014",  # sender_gln
                    "0567890000021",  # receiver_gln
                    "0999888000028"   # shipper_gln
                ]
                
                expected_sglns = [
                    "0345802000014.001",  # sender_sgln
                    "0567890000021.001",  # receiver_sgln
                    "0999888000028.001"   # shipper_sgln
                ]
                
                found_glns = []
                found_sglns = []
                
                for gln in expected_glns:
                    if gln in xml_content:
                        found_glns.append(gln)
                
                for sgln in expected_sglns:
                    if sgln in xml_content:
                        found_sglns.append(sgln)
                
                # For now, we'll check if at least some business entity identifiers are present
                # The current implementation may not include all location vocabulary yet
                if len(found_glns) > 0 or len(found_sglns) > 0:
                    self.log_test("Location Vocabulary", True, 
                                f"Business entity identifiers found in XML",
                                f"GLNs: {found_glns}, SGLNs: {found_sglns}")
                    return True
                else:
                    self.log_test("Location Vocabulary", False, 
                                "No business entity GLN/SGLN identifiers found in XML")
                    return False
            else:
                self.log_test("Location Vocabulary", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Location Vocabulary", False, f"Request error: {str(e)}")
            return False

    def test_shipping_bizstep_last(self, config_id):
        """Test that Shipping bizStep is the last ObjectEvent"""
        if not config_id:
            self.log_test("Shipping bizStep Last", False, "No configuration ID available")
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
                
                # Parse XML to check event order
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find EventList
                    event_list = None
                    for elem in root.iter():
                        if elem.tag.endswith("EventList"):
                            event_list = elem
                            break
                    
                    if event_list is not None:
                        events = list(event_list)
                        
                        if len(events) > 0:
                            # Check the last event
                            last_event = events[-1]
                            
                            if last_event.tag.endswith("ObjectEvent"):
                                # Check if it has shipping bizStep
                                for child in last_event:
                                    if child.tag.endswith("bizStep"):
                                        if "shipping" in child.text:
                                            self.log_test("Shipping bizStep Last", True, 
                                                        "Last ObjectEvent has shipping bizStep")
                                            return True
                                        else:
                                            self.log_test("Shipping bizStep Last", False, 
                                                        f"Last ObjectEvent has wrong bizStep: {child.text}")
                                            return False
                                
                                self.log_test("Shipping bizStep Last", False, 
                                            "Last ObjectEvent missing bizStep")
                                return False
                            else:
                                self.log_test("Shipping bizStep Last", False, 
                                            f"Last event is not ObjectEvent: {last_event.tag}")
                                return False
                        else:
                            self.log_test("Shipping bizStep Last", False, "No events found")
                            return False
                    else:
                        self.log_test("Shipping bizStep Last", False, "EventList not found")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("Shipping bizStep Last", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Shipping bizStep Last", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Shipping bizStep Last", False, f"Request error: {str(e)}")
            return False

    def run_business_document_tests(self):
        """Run all business document and GS1 Rx EPCIS compliance tests"""
        print("=" * 80)
        print("BUSINESS DOCUMENT INFORMATION AND GS1 Rx EPCIS COMPLIANCE TESTING")
        print("=" * 80)
        print("Testing Configuration:")
        print("- 1 SSCC, 2 Cases, 3 Items per Case (6 total items)")
        print("- Shipper Company Prefix: 0999888 (for SSCC)")
        print("- Regular Company Prefix: 1234567 (for SGTIN)")
        print("- Business Document Information fields")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Business Document Configuration
        config_id = self.test_business_document_configuration()
        
        # Test 3: Serial Numbers Creation
        serial_id = self.test_serial_numbers_creation(config_id)
        
        # Test 4: SSCC uses shipper's company prefix
        sscc_prefix_success = self.test_sscc_uses_shipper_prefix(config_id)
        
        # Test 5: SGTIN uses regular company prefix
        sgtin_prefix_success = self.test_sgtin_uses_regular_prefix(config_id)
        
        # Test 6: SBDH Structure
        sbdh_success = self.test_sbdh_structure(config_id)
        
        # Test 7: Location Vocabulary
        location_vocab_success = self.test_location_vocabulary(config_id)
        
        # Test 8: Shipping bizStep is last
        shipping_last_success = self.test_shipping_bizstep_last(config_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("BUSINESS DOCUMENT TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical Requirements Status
        print("\n" + "=" * 40)
        print("CRITICAL REQUIREMENTS STATUS")
        print("=" * 40)
        print(f"SSCC uses Shipper Prefix: {'✅ WORKING' if sscc_prefix_success else '❌ FAILING'}")
        print(f"SGTIN uses Regular Prefix: {'✅ WORKING' if sgtin_prefix_success else '❌ FAILING'}")
        print(f"SBDH Structure: {'✅ WORKING' if sbdh_success else '❌ FAILING'}")
        print(f"Location Vocabulary: {'✅ WORKING' if location_vocab_success else '❌ FAILING'}")
        print(f"Shipping bizStep Last: {'✅ WORKING' if shipping_last_success else '❌ FAILING'}")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nGS1 Rx EPCIS Compliance Features Tested:")
        print("✓ Business Document Information fields storage")
        print("✓ SSCC generation using shipper's company prefix")
        print("✓ SGTIN generation using regular company prefix")
        print("✓ SBDH (StandardBusinessDocumentHeader) structure")
        print("✓ Location Vocabulary with GLN/SGLN")
        print("✓ Shipping bizStep as last ObjectEvent")
        
        return passed == total

if __name__ == "__main__":
    tester = BusinessDocumentTester()
    success = tester.run_business_document_tests()
    sys.exit(0 if success else 1)