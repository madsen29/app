#!/usr/bin/env python3
"""
GS1 Rx EPCIS Compliance Testing - Location Vocabulary and Shipping ObjectEvent
Tests the specific fixes for:
1. Location Vocabulary - Verify that Location vocabulary is now present in EPCISMasterData
2. Shipping ObjectEvent - Verify that shipping bizStep ObjectEvent appears as the last event

Test Configuration (from review request):
{
  "items_per_case": 3,
  "cases_per_sscc": 2,
  "number_of_sscc": 1,
  "use_inner_cases": false,
  "company_prefix": "1234567",
  "item_product_code": "000000",
  "case_product_code": "000001",
  "lot_number": "LOT123",
  "expiration_date": "2025-12-31",
  "sscc_indicator_digit": "3",
  "case_indicator_digit": "2",
  "item_indicator_digit": "1",
  "sender_company_prefix": "0345802",
  "sender_gln": "0345802000014",
  "sender_sgln": "0345802000014.001",
  "receiver_company_prefix": "0567890",
  "receiver_gln": "0567890000021",
  "receiver_sgln": "0567890000021.001",
  "shipper_company_prefix": "0999888",
  "shipper_gln": "0999888000028",
  "shipper_sgln": "0999888000028.001",
  "shipper_same_as_sender": false,
  "package_ndc": "45802-046-85",
  "regulated_product_name": "Test Product",
  "manufacturer_name": "Test Manufacturer"
}
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://c8e3fe45-251a-4359-a250-c028fb05fe98.preview.emergentagent.com/api"

class GS1RxEPCISTester:
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
        """Create configuration with exact review request parameters"""
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
        """Create serial numbers for test configuration"""
        if not config_id:
            self.log_test("Test Serial Numbers Creation", False, "No configuration ID available")
            return None
            
        # For config: 1 SSCC, 2 Cases, 3 Items per Case = 6 total items
        sscc_serials = ["SSCC001"]
        case_serials = ["CASE001", "CASE002"]
        item_serials = ["ITEM001", "ITEM002", "ITEM003", "ITEM004", "ITEM005", "ITEM006"]
        
        test_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": sscc_serials,
            "case_serial_numbers": case_serials,
            "inner_case_serial_numbers": [],
            "item_serial_numbers": item_serials
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

    def test_location_vocabulary_presence(self, config_id):
        """Test that Location vocabulary is present in EPCISMasterData"""
        if not config_id:
            self.log_test("Location Vocabulary Presence", False, "No configuration ID available")
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
                
                # Parse XML to check for Location vocabulary
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
                    
                    if location_vocabulary_found:
                        # Check for expected location elements
                        expected_locations = [
                            "urn:epc:id:sgln:0345802000014",      # sender_gln
                            "urn:epc:id:sgln:0345802000014.001",  # sender_sgln
                            "urn:epc:id:sgln:0567890000021",      # receiver_gln
                            "urn:epc:id:sgln:0567890000021.001",  # receiver_sgln
                            "urn:epc:id:sgln:0999888000028",      # shipper_gln
                            "urn:epc:id:sgln:0999888000028.001"   # shipper_sgln
                        ]
                        
                        found_locations = [loc for loc in expected_locations if loc in location_elements]
                        
                        if len(found_locations) >= 6:  # All expected locations found
                            self.log_test("Location Vocabulary Presence", True, 
                                        f"Location vocabulary found with {len(found_locations)} location elements",
                                        f"Found locations: {found_locations}")
                            return True
                        else:
                            self.log_test("Location Vocabulary Presence", False, 
                                        f"Location vocabulary found but missing expected elements",
                                        f"Expected: {expected_locations}, Found: {found_locations}")
                            return False
                    else:
                        self.log_test("Location Vocabulary Presence", False, 
                                    "Location vocabulary not found in EPCISMasterData")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("Location Vocabulary Presence", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Location Vocabulary Presence", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Location Vocabulary Presence", False, f"Request error: {str(e)}")
            return False

    def test_shipping_object_event_last(self, config_id):
        """Test that shipping ObjectEvent appears as the last event"""
        if not config_id:
            self.log_test("Shipping ObjectEvent Last", False, "No configuration ID available")
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
                            last_event = events[-1]
                            
                            # Check if last event is ObjectEvent with shipping bizStep
                            if last_event.tag.endswith("ObjectEvent"):
                                # Find bizStep in the last event
                                biz_step_elem = None
                                action_elem = None
                                disposition_elem = None
                                epc_list_elem = None
                                
                                for child in last_event:
                                    if child.tag.endswith("bizStep"):
                                        biz_step_elem = child
                                    elif child.tag.endswith("action"):
                                        action_elem = child
                                    elif child.tag.endswith("disposition"):
                                        disposition_elem = child
                                    elif child.tag.endswith("epcList"):
                                        epc_list_elem = child
                                
                                # Verify shipping event properties
                                is_shipping = (biz_step_elem is not None and 
                                             "shipping" in biz_step_elem.text)
                                is_observe = (action_elem is not None and 
                                            action_elem.text == "OBSERVE")
                                is_in_transit = (disposition_elem is not None and 
                                               "in_transit" in disposition_elem.text)
                                
                                # Check if it contains SSCC EPCs
                                has_sscc_epcs = False
                                sscc_count = 0
                                if epc_list_elem is not None:
                                    for epc_elem in epc_list_elem:
                                        if epc_elem.tag.endswith("epc"):
                                            epc_text = epc_elem.text
                                            if epc_text and "sscc:" in epc_text:
                                                has_sscc_epcs = True
                                                sscc_count += 1
                                
                                if is_shipping and is_observe and is_in_transit and has_sscc_epcs:
                                    self.log_test("Shipping ObjectEvent Last", True, 
                                                f"Shipping ObjectEvent found as last event with correct properties",
                                                f"bizStep: shipping, action: OBSERVE, disposition: in_transit, SSCC EPCs: {sscc_count}")
                                    return True
                                else:
                                    self.log_test("Shipping ObjectEvent Last", False, 
                                                f"Last ObjectEvent missing shipping properties",
                                                f"shipping: {is_shipping}, observe: {is_observe}, in_transit: {is_in_transit}, has_sscc: {has_sscc_epcs}")
                                    return False
                            else:
                                self.log_test("Shipping ObjectEvent Last", False, 
                                            f"Last event is not ObjectEvent, found: {last_event.tag}")
                                return False
                        else:
                            self.log_test("Shipping ObjectEvent Last", False, "No events found in EventList")
                            return False
                    else:
                        self.log_test("Shipping ObjectEvent Last", False, "EventList not found in XML")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("Shipping ObjectEvent Last", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Shipping ObjectEvent Last", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Shipping ObjectEvent Last", False, f"Request error: {str(e)}")
            return False

    def test_sscc_uses_shipper_prefix(self, config_id):
        """Test that SSCC EPCs use shipper's company prefix (0999888)"""
        if not config_id:
            self.log_test("SSCC Uses Shipper Prefix", False, "No configuration ID available")
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
                
                # Check for SSCC EPCs with shipper prefix
                expected_sscc_prefix = "urn:epc:id:sscc:0999888.3"  # shipper_company_prefix + sscc_indicator_digit
                
                if expected_sscc_prefix in xml_content:
                    # Also check that regular company prefix is NOT used for SSCC
                    wrong_sscc_prefix = "urn:epc:id:sscc:1234567.3"  # regular company_prefix
                    
                    if wrong_sscc_prefix not in xml_content:
                        self.log_test("SSCC Uses Shipper Prefix", True, 
                                    "SSCC EPCs correctly use shipper's company prefix (0999888)")
                        return True
                    else:
                        self.log_test("SSCC Uses Shipper Prefix", False, 
                                    "SSCC EPCs incorrectly use regular company prefix instead of shipper's")
                        return False
                else:
                    self.log_test("SSCC Uses Shipper Prefix", False, 
                                f"Expected SSCC prefix '{expected_sscc_prefix}' not found in XML")
                    return False
            else:
                self.log_test("SSCC Uses Shipper Prefix", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SSCC Uses Shipper Prefix", False, f"Request error: {str(e)}")
            return False

    def test_sgtin_uses_regular_prefix(self, config_id):
        """Test that SGTIN EPCs use regular company prefix (1234567)"""
        if not config_id:
            self.log_test("SGTIN Uses Regular Prefix", False, "No configuration ID available")
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
                
                # Check for SGTIN EPCs with regular prefix
                expected_case_sgtin = "urn:epc:id:sgtin:1234567.2000001."  # case with indicator 2
                expected_item_sgtin = "urn:epc:id:sgtin:1234567.1000000."  # item with indicator 1
                
                case_found = expected_case_sgtin in xml_content
                item_found = expected_item_sgtin in xml_content
                
                if case_found and item_found:
                    self.log_test("SGTIN Uses Regular Prefix", True, 
                                "SGTIN EPCs correctly use regular company prefix (1234567)")
                    return True
                else:
                    self.log_test("SGTIN Uses Regular Prefix", False, 
                                f"Expected SGTIN prefixes not found - Case: {case_found}, Item: {item_found}")
                    return False
            else:
                self.log_test("SGTIN Uses Regular Prefix", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SGTIN Uses Regular Prefix", False, f"Request error: {str(e)}")
            return False

    def test_epcclass_vocabulary_present(self, config_id):
        """Test that EPCClass vocabulary is present"""
        if not config_id:
            self.log_test("EPCClass Vocabulary Present", False, "No configuration ID available")
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
                
                # Parse XML to check for EPCClass vocabulary
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find EPCClass vocabulary
                    epcclass_vocabulary_found = False
                    epcclass_elements = []
                    
                    for elem in root.iter():
                        if elem.tag.endswith("Vocabulary") and elem.get("type") == "urn:epcglobal:epcis:vtype:EPCClass":
                            epcclass_vocabulary_found = True
                            
                            # Find VocabularyElementList
                            for child in elem:
                                if child.tag.endswith("VocabularyElementList"):
                                    for vocab_elem in child:
                                        if vocab_elem.tag.endswith("VocabularyElement"):
                                            epcclass_elements.append(vocab_elem.get("id"))
                    
                    if epcclass_vocabulary_found:
                        # Check for expected EPCClass elements (Item and Case for 3-level hierarchy)
                        expected_patterns = [
                            "urn:epc:idpat:sgtin:1234567.1000000.*",  # Item
                            "urn:epc:idpat:sgtin:1234567.2000001.*"   # Case
                        ]
                        
                        found_patterns = [pattern for pattern in expected_patterns if pattern in epcclass_elements]
                        
                        if len(found_patterns) >= 2:  # Both Item and Case patterns found
                            self.log_test("EPCClass Vocabulary Present", True, 
                                        f"EPCClass vocabulary found with {len(found_patterns)} elements",
                                        f"Found patterns: {found_patterns}")
                            return True
                        else:
                            self.log_test("EPCClass Vocabulary Present", False, 
                                        f"EPCClass vocabulary found but missing expected patterns",
                                        f"Expected: {expected_patterns}, Found: {found_patterns}")
                            return False
                    else:
                        self.log_test("EPCClass Vocabulary Present", False, 
                                    "EPCClass vocabulary not found in EPCISMasterData")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("EPCClass Vocabulary Present", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("EPCClass Vocabulary Present", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("EPCClass Vocabulary Present", False, f"Request error: {str(e)}")
            return False

    def run_gs1_rx_epcis_tests(self):
        """Run GS1 Rx EPCIS compliance tests"""
        print("=" * 80)
        print("GS1 Rx EPCIS COMPLIANCE TESTING - LOCATION VOCABULARY & SHIPPING EVENT")
        print("=" * 80)
        print("Testing specific fixes for:")
        print("1. Location Vocabulary - Verify presence in EPCISMasterData")
        print("2. Shipping ObjectEvent - Verify appears as last event")
        print("3. SSCC EPCs use shipper's company prefix (0999888)")
        print("4. SGTIN EPCs use regular company prefix (1234567)")
        print("5. EPCClass vocabulary is present")
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
        
        # Test 4: Location Vocabulary Presence (CRITICAL)
        location_vocab_success = self.test_location_vocabulary_presence(config_id)
        
        # Test 5: Shipping ObjectEvent Last (CRITICAL)
        shipping_event_success = self.test_shipping_object_event_last(config_id)
        
        # Test 6: SSCC Uses Shipper Prefix
        sscc_prefix_success = self.test_sscc_uses_shipper_prefix(config_id)
        
        # Test 7: SGTIN Uses Regular Prefix
        sgtin_prefix_success = self.test_sgtin_uses_regular_prefix(config_id)
        
        # Test 8: EPCClass Vocabulary Present
        epcclass_vocab_success = self.test_epcclass_vocabulary_present(config_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("GS1 Rx EPCIS COMPLIANCE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical Issues Status
        print("\n" + "=" * 40)
        print("CRITICAL ISSUES STATUS")
        print("=" * 40)
        print(f"Location Vocabulary Present: {'✅ WORKING' if location_vocab_success else '❌ MISSING'}")
        print(f"Shipping ObjectEvent Last: {'✅ WORKING' if shipping_event_success else '❌ MISSING'}")
        print(f"SSCC Uses Shipper Prefix: {'✅ WORKING' if sscc_prefix_success else '❌ FAILING'}")
        print(f"SGTIN Uses Regular Prefix: {'✅ WORKING' if sgtin_prefix_success else '❌ FAILING'}")
        print(f"EPCClass Vocabulary Present: {'✅ WORKING' if epcclass_vocab_success else '❌ MISSING'}")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nTest Configuration Used:")
        print("✓ 1 SSCC, 2 Cases, 3 Items per Case (6 total items)")
        print("✓ Company Prefix: 1234567")
        print("✓ Shipper Company Prefix: 0999888")
        print("✓ Business Document Information: sender, receiver, shipper GLN/SGLN")
        print("✓ Package NDC: 45802-046-85")
        
        return passed == total

if __name__ == "__main__":
    tester = GS1RxEPCISTester()
    success = tester.run_gs1_rx_epcis_tests()
    sys.exit(0 if success else 1)