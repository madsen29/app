#!/usr/bin/env python3
"""
Backend API Testing for EPCIS Serial Number Aggregation App - RESTRUCTURED VERSION
Tests the three main backend endpoints with new GS1 EPCIS hierarchy:
1. POST /api/configuration (with SSCC→Cases→Items structure)
2. POST /api/serial-numbers (with SSCC, case, and item serial numbers)
3. POST /api/generate-epcis (EPCIS 1.2 with commissioning + aggregation events)
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://efa7bc97-ed4b-49d0-9444-1f27564cfee5.preview.emergentagent.com/api"

class BackendTester:
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
    
    def test_configuration_creation(self):
        """Test POST /api/configuration with new GS1 EPCIS hierarchy structure"""
        # Test scenario: 10 items per case, 5 cases per SSCC, 2 SSCCs
        test_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 2,
            "company_prefix": "9876543",
            "item_product_code": "123456",
            "case_product_code": "789012",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "item_indicator_digit": "1"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "items_per_case", "cases_per_sscc", "number_of_sscc", 
                                 "company_prefix", "item_product_code", "case_product_code",
                                 "sscc_indicator_digit", "case_indicator_digit", "item_indicator_digit", "timestamp"]
                
                if all(field in data for field in required_fields):
                    if (data["items_per_case"] == 10 and data["cases_per_sscc"] == 5 and data["number_of_sscc"] == 2 and
                        data["company_prefix"] == "9876543" and data["item_product_code"] == "123456" and
                        data["case_product_code"] == "789012" and data["sscc_indicator_digit"] == "3" and
                        data["case_indicator_digit"] == "2" and data["item_indicator_digit"] == "1"):
                        self.log_test("Configuration Creation", True, "Configuration created with new GS1 EPCIS hierarchy", 
                                    f"ID: {data['id']}, SSCC→Cases→Items: {data['number_of_sscc']}→{data['cases_per_sscc']}→{data['items_per_case']}")
                        return data["id"]  # Return config ID for subsequent tests
                    else:
                        self.log_test("Configuration Creation", False, "Data mismatch in response", data)
                        return None
                else:
                    self.log_test("Configuration Creation", False, "Missing required fields", data)
                    return None
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration Creation", False, f"Request error: {str(e)}")
            return None
    
    def test_configuration_validation(self):
        """Test configuration creation with missing required GS1 parameters"""
        invalid_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5
            # Missing required GS1 parameters: number_of_sscc, company_prefix, product codes, indicator digits
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Should reject with 422 due to missing required fields
            if response.status_code in [400, 422]:
                self.log_test("Configuration Validation", True, "Missing GS1 parameters properly rejected")
            elif response.status_code == 200:
                self.log_test("Configuration Validation", False, "Missing GS1 parameters were accepted (validation issue)")
            else:
                self.log_test("Configuration Validation", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Configuration Validation", False, f"Request error: {str(e)}")
    
    def test_serial_numbers_creation(self, config_id):
        """Test POST /api/serial-numbers with new hierarchy validation"""
        if not config_id:
            self.log_test("Serial Numbers Creation", False, "No configuration ID available")
            return None
            
        # For config: 10 items per case, 5 cases per SSCC, 2 SSCCs
        # Expected: 2 SSCC serials, 10 case serials (5×2), 100 item serials (10×5×2)
        sscc_serials = [f"SSCC{i+1:03d}" for i in range(2)]
        case_serials = [f"CASE{i+1:03d}" for i in range(10)]  # 5 cases per SSCC × 2 SSCCs = 10 total cases
        item_serials = [f"ITEM{i+1:03d}" for i in range(100)]  # 10 items per case × 10 cases = 100 total items
        
        test_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": sscc_serials,
            "case_serial_numbers": case_serials,
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
                required_fields = ["id", "configuration_id", "sscc_serial_numbers", "case_serial_numbers", "item_serial_numbers", "timestamp"]
                
                if all(field in data for field in required_fields):
                    if (len(data["sscc_serial_numbers"]) == 2 and 
                        len(data["case_serial_numbers"]) == 10 and
                        len(data["item_serial_numbers"]) == 100 and
                        data["configuration_id"] == config_id):
                        self.log_test("Serial Numbers Creation", True, "Serial numbers saved with correct hierarchy validation",
                                    f"SSCCs: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
                        return data["id"]
                    else:
                        self.log_test("Serial Numbers Creation", False, "Data validation failed", data)
                        return None
                else:
                    self.log_test("Serial Numbers Creation", False, "Missing required fields", data)
                    return None
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return None
    
    def test_serial_numbers_validation(self, config_id):
        """Test serial numbers validation with incorrect counts for new hierarchy"""
        if not config_id:
            self.log_test("Serial Numbers Validation", False, "No configuration ID available")
            return
            
        # Test with wrong number of SSCC serials (should be 2, providing 1)
        invalid_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": [f"SSCC{i+1:03d}" for i in range(1)],  # Wrong: 1 SSCC instead of 2
            "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(10)],  # Correct: 10 cases
            "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(100)]  # Correct: 100 items
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                error_msg = response.json().get("detail", "")
                if "Expected 2 SSCC serial numbers" in error_msg:
                    self.log_test("Serial Numbers Validation", True, "Validation correctly rejected wrong SSCC count")
                else:
                    self.log_test("Serial Numbers Validation", False, f"Wrong error message: {error_msg}")
            else:
                self.log_test("Serial Numbers Validation", False, f"Expected 400 error, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Serial Numbers Validation", False, f"Request error: {str(e)}")
    
    def test_epcis_generation(self, config_id):
        """Test POST /api/generate-epcis and validate EPCIS 1.2 XML with commissioning + aggregation events"""
        if not config_id:
            self.log_test("EPCIS Generation", False, "No configuration ID available")
            return
            
        test_data = {
            "configuration_id": config_id,
            "read_point": "urn:epc:id:sgln:9876543.00000.0",
            "biz_location": "urn:epc:id:sgln:9876543.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Check if response is XML
                content_type = response.headers.get('content-type', '')
                if 'xml' in content_type:
                    xml_content = response.text
                    if self.validate_epcis_1_2_xml(xml_content):
                        self.log_test("EPCIS Generation", True, "Valid EPCIS 1.2 XML generated with commissioning + aggregation events",
                                    f"XML length: {len(xml_content)} characters")
                    else:
                        self.log_test("EPCIS Generation", False, "Generated XML does not meet EPCIS 1.2 standards")
                else:
                    self.log_test("EPCIS Generation", False, f"Expected XML, got content-type: {content_type}")
            else:
                self.log_test("EPCIS Generation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("EPCIS Generation", False, f"Request error: {str(e)}")
    
    def validate_epcis_1_2_xml(self, xml_content):
        """Validate EPCIS 1.2 XML with commissioning events and proper GS1 identifiers"""
        try:
            root = ET.fromstring(xml_content)
            
            # Check root element and EPCIS 1.2 namespace
            if not root.tag.endswith("EPCISDocument"):
                print(f"   Invalid root element: {root.tag}")
                return False
            
            # Check for EPCIS 1.2 namespace (should be urn:epcglobal:epcis:xsd:1)
            if not root.tag.startswith("{urn:epcglobal:epcis:xsd:1}"):
                print(f"   Invalid EPCIS namespace - expected 1.2: {root.tag}")
                return False
            
            # Check schema version
            schema_version = root.get("schemaVersion")
            if schema_version != "1.2":
                print(f"   Expected schemaVersion='1.2', got '{schema_version}'")
                return False
            
            # Find EPCISBody and EventList
            epcis_body = None
            for child in root:
                if child.tag.endswith("EPCISBody"):
                    epcis_body = child
                    break
            
            if epcis_body is None:
                print(f"   Missing EPCISBody element")
                return False
            
            event_list = None
            for child in epcis_body:
                if child.tag.endswith("EventList"):
                    event_list = child
                    break
                    
            if event_list is None:
                print(f"   Missing EventList element")
                return False
            
            # Count different event types
            object_events = []
            aggregation_events = []
            
            for child in event_list:
                if child.tag.endswith("ObjectEvent"):
                    object_events.append(child)
                elif child.tag.endswith("AggregationEvent"):
                    aggregation_events.append(child)
            
            # Expected events for our test scenario:
            # - 100 ObjectEvents for item commissioning
            # - 10 ObjectEvents for case commissioning  
            # - 2 ObjectEvents for SSCC commissioning
            # - 10 AggregationEvents for Items→Cases
            # - 2 AggregationEvents for Cases→SSCCs
            # Total: 112 ObjectEvents + 12 AggregationEvents = 124 events
            
            expected_object_events = 100 + 10 + 2  # Items + Cases + SSCCs
            expected_aggregation_events = 10 + 2   # Items→Cases + Cases→SSCCs
            
            if len(object_events) != expected_object_events:
                print(f"   Expected {expected_object_events} ObjectEvents (commissioning), found {len(object_events)}")
                return False
                
            if len(aggregation_events) != expected_aggregation_events:
                print(f"   Expected {expected_aggregation_events} AggregationEvents, found {len(aggregation_events)}")
                return False
            
            # Validate commissioning events (ObjectEvents)
            commissioning_events_validated = self.validate_commissioning_events(object_events)
            if not commissioning_events_validated:
                return False
            
            # Validate aggregation events structure
            aggregation_events_validated = self.validate_aggregation_events(aggregation_events)
            if not aggregation_events_validated:
                return False
            
            # Validate GS1 identifier formats
            gs1_identifiers_validated = self.validate_gs1_identifiers(object_events, aggregation_events)
            if not gs1_identifiers_validated:
                return False
            
            print(f"   ✓ Valid EPCIS 1.2 XML with schema version {schema_version}")
            print(f"   ✓ Commissioning events: {len(object_events)} ObjectEvents")
            print(f"   ✓ Aggregation events: {len(aggregation_events)} AggregationEvents")
            print(f"   ✓ GS1 identifiers use correct format with indicator digits")
            return True
            
        except ET.ParseError as e:
            print(f"   XML parsing error: {str(e)}")
            return False
        except Exception as e:
            print(f"   Validation error: {str(e)}")
            return False
    
    def validate_commissioning_events(self, object_events):
        """Validate ObjectEvents are proper commissioning events"""
        try:
            for event in object_events:
                # Check required elements
                required_elements = ["eventTime", "epcList", "action", "bizStep", "disposition"]
                
                for element_name in required_elements:
                    elem = None
                    for child in event:
                        if child.tag.endswith(element_name):
                            elem = child
                            break
                    if elem is None:
                        print(f"   Missing {element_name} in ObjectEvent")
                        return False
                
                # Check action is ADD
                action_elem = None
                for child in event:
                    if child.tag.endswith("action"):
                        action_elem = child
                        break
                if action_elem.text != "ADD":
                    print(f"   Expected action 'ADD' in commissioning event, got '{action_elem.text}'")
                    return False
                
                # Check bizStep is commissioning
                bizstep_elem = None
                for child in event:
                    if child.tag.endswith("bizStep"):
                        bizstep_elem = child
                        break
                if "commissioning" not in bizstep_elem.text:
                    print(f"   Expected commissioning bizStep, got '{bizstep_elem.text}'")
                    return False
            
            return True
        except Exception as e:
            print(f"   Error validating commissioning events: {str(e)}")
            return False
    
    def validate_aggregation_events(self, aggregation_events):
        """Validate AggregationEvents structure"""
        try:
            for event in aggregation_events:
                # Check required elements
                required_elements = ["eventTime", "parentID", "childEPCs", "action", "bizStep"]
                
                for element_name in required_elements:
                    elem = None
                    for child in event:
                        if child.tag.endswith(element_name):
                            elem = child
                            break
                    if elem is None:
                        print(f"   Missing {element_name} in AggregationEvent")
                        return False
                
                # Check action is ADD
                action_elem = None
                for child in event:
                    if child.tag.endswith("action"):
                        action_elem = child
                        break
                if action_elem.text != "ADD":
                    print(f"   Expected action 'ADD' in aggregation event, got '{action_elem.text}'")
                    return False
                
                # Check bizStep is packing
                bizstep_elem = None
                for child in event:
                    if child.tag.endswith("bizStep"):
                        bizstep_elem = child
                        break
                if "packing" not in bizstep_elem.text:
                    print(f"   Expected packing bizStep, got '{bizstep_elem.text}'")
                    return False
            
            return True
        except Exception as e:
            print(f"   Error validating aggregation events: {str(e)}")
            return False
    
    def validate_gs1_identifiers(self, object_events, aggregation_events):
        """Validate GS1 identifier formats with correct indicator digit placement"""
        try:
            company_prefix = "9876543"
            item_product_code = "123456"
            case_product_code = "789012"
            sscc_indicator_digit = "3"
            case_indicator_digit = "2"
            item_indicator_digit = "1"
            
            # Check ObjectEvent EPCs
            for event in object_events:
                epc_list_elem = None
                for child in event:
                    if child.tag.endswith("epcList"):
                        epc_list_elem = child
                        break
                
                if epc_list_elem is not None:
                    for epc_elem in epc_list_elem:
                        if epc_elem.tag.endswith("epc"):
                            epc = epc_elem.text
                            
                            # Validate EPC format
                            if epc.startswith("urn:epc:id:sscc:"):
                                # SSCC format: urn:epc:id:sscc:{company_prefix}.{sscc_indicator_digit}{sscc_serial}
                                expected_prefix = f"urn:epc:id:sscc:{company_prefix}.{sscc_indicator_digit}"
                                if not epc.startswith(expected_prefix):
                                    print(f"   Invalid SSCC format: {epc}")
                                    print(f"   Expected to start with: {expected_prefix}")
                                    return False
                            elif epc.startswith("urn:epc:id:sgtin:"):
                                # SGTIN format: urn:epc:id:sgtin:{company_prefix}.{indicator_digit}{product_code}.{serial}
                                if f".{case_indicator_digit}{case_product_code}." in epc:
                                    # Case SGTIN
                                    expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}."
                                    if not epc.startswith(expected_prefix):
                                        print(f"   Invalid Case SGTIN format: {epc}")
                                        print(f"   Expected to start with: {expected_prefix}")
                                        return False
                                elif f".{item_indicator_digit}{item_product_code}." in epc:
                                    # Item SGTIN
                                    expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}."
                                    if not epc.startswith(expected_prefix):
                                        print(f"   Invalid Item SGTIN format: {epc}")
                                        print(f"   Expected to start with: {expected_prefix}")
                                        return False
                                else:
                                    print(f"   Unknown SGTIN format: {epc}")
                                    return False
                            else:
                                print(f"   Unknown EPC format: {epc}")
                                return False
            
            # Check AggregationEvent parent and child EPCs
            for event in aggregation_events:
                parent_id_elem = None
                child_epcs_elem = None
                
                for child in event:
                    if child.tag.endswith("parentID"):
                        parent_id_elem = child
                    elif child.tag.endswith("childEPCs"):
                        child_epcs_elem = child
                
                # Validate parent ID
                if parent_id_elem is not None:
                    parent_epc = parent_id_elem.text
                    if parent_epc.startswith("urn:epc:id:sscc:"):
                        expected_prefix = f"urn:epc:id:sscc:{company_prefix}.{sscc_indicator_digit}"
                        if not parent_epc.startswith(expected_prefix):
                            print(f"   Invalid parent SSCC format: {parent_epc}")
                            return False
                    elif parent_epc.startswith("urn:epc:id:sgtin:"):
                        expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}."
                        if not parent_epc.startswith(expected_prefix):
                            print(f"   Invalid parent Case SGTIN format: {parent_epc}")
                            return False
                
                # Validate child EPCs
                if child_epcs_elem is not None:
                    for child_epc_elem in child_epcs_elem:
                        if child_epc_elem.tag.endswith("epc"):
                            child_epc = child_epc_elem.text
                            if child_epc.startswith("urn:epc:id:sgtin:"):
                                if f".{case_indicator_digit}{case_product_code}." in child_epc:
                                    expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}."
                                elif f".{item_indicator_digit}{item_product_code}." in child_epc:
                                    expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}."
                                else:
                                    print(f"   Unknown child SGTIN format: {child_epc}")
                                    return False
                                
                                if not child_epc.startswith(expected_prefix):
                                    print(f"   Invalid child SGTIN format: {child_epc}")
                                    return False
            
            return True
        except Exception as e:
            print(f"   Error validating GS1 identifiers: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for non-existent resources"""
        # Test with non-existent configuration ID
        fake_config_id = "non-existent-id"
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json={
                    "configuration_id": fake_config_id,
                    "sscc_serial_numbers": ["SSCC001"],
                    "case_serial_numbers": ["CASE001"],
                    "item_serial_numbers": ["ITEM001"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 404:
                error_msg = response.json().get("detail", "")
                if "Configuration not found" in error_msg:
                    self.log_test("Error Handling", True, "Properly handles non-existent configuration")
                else:
                    self.log_test("Error Handling", False, f"Wrong error message: {error_msg}")
            else:
                self.log_test("Error Handling", False, f"Expected 404 error, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Request error: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests in sequence for restructured EPCIS API"""
        print("=" * 80)
        print("EPCIS BACKEND API TESTING - RESTRUCTURED GS1 HIERARCHY")
        print("=" * 80)
        print("Testing new structure: SSCC→Cases→Items with EPCIS 1.2 schema")
        print("Expected: 2 SSCCs, 10 Cases (5×2), 100 Items (10×5×2)")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Configuration Creation with new structure
        config_id = self.test_configuration_creation()
        
        # Test 3: Configuration Validation
        self.test_configuration_validation()
        
        # Test 4: Serial Numbers Creation with new hierarchy (requires config_id)
        serial_id = self.test_serial_numbers_creation(config_id)
        
        # Test 5: Serial Numbers Validation with new counts
        self.test_serial_numbers_validation(config_id)
        
        # Test 6: EPCIS 1.2 Generation with commissioning + aggregation events
        self.test_epcis_generation(config_id)
        
        # Test 7: Error Handling
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY - RESTRUCTURED EPCIS API")
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
        
        print("\nKey Features Tested:")
        print("✓ New GS1 hierarchy: SSCC→Cases→Items")
        print("✓ Separate product codes for items and cases")
        print("✓ Indicator digits before product codes")
        print("✓ EPCIS 1.2 schema with commissioning events")
        print("✓ Proper aggregation events (Items→Cases, Cases→SSCCs)")
        print("✓ GS1 identifier format validation")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)