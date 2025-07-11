#!/usr/bin/env python3
"""
Backend API Testing for EPCIS Serial Number Aggregation App
Tests the three main backend endpoints:
1. POST /api/configuration
2. POST /api/serial-numbers  
3. POST /api/generate-epcis
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
        """Test POST /api/configuration with valid data including GS1 parameters"""
        test_data = {
            "items_per_case": 10,
            "number_of_cases": 5,
            "company_prefix": "9876543",
            "product_code": "123456",
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
                required_fields = ["id", "items_per_case", "number_of_cases", "timestamp"]
                
                if all(field in data for field in required_fields):
                    if data["items_per_case"] == 10 and data["number_of_cases"] == 5:
                        self.log_test("Configuration Creation", True, "Configuration created successfully", 
                                    f"ID: {data['id']}")
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
        """Test configuration creation with invalid data"""
        invalid_data = {
            "items_per_case": -1,  # Invalid negative value
            "number_of_cases": 0   # Invalid zero value
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Should either reject with 400 or accept (depending on validation implementation)
            if response.status_code in [400, 422]:
                self.log_test("Configuration Validation", True, "Invalid data properly rejected")
            elif response.status_code == 200:
                self.log_test("Configuration Validation", False, "Invalid data was accepted (no validation)")
            else:
                self.log_test("Configuration Validation", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Configuration Validation", False, f"Request error: {str(e)}")
    
    def test_serial_numbers_creation(self, config_id):
        """Test POST /api/serial-numbers with valid data"""
        if not config_id:
            self.log_test("Serial Numbers Creation", False, "No configuration ID available")
            return None
            
        # Generate test serial numbers for 10 items per case, 5 cases = 50 total items
        case_serials = [f"CASE{i+1:03d}" for i in range(5)]
        item_serials = [f"ITEM{i+1:03d}" for i in range(50)]
        
        test_data = {
            "configuration_id": config_id,
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
                required_fields = ["id", "configuration_id", "case_serial_numbers", "item_serial_numbers", "timestamp"]
                
                if all(field in data for field in required_fields):
                    if (len(data["case_serial_numbers"]) == 5 and 
                        len(data["item_serial_numbers"]) == 50 and
                        data["configuration_id"] == config_id):
                        self.log_test("Serial Numbers Creation", True, "Serial numbers saved successfully",
                                    f"Cases: {len(data['case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
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
        """Test serial numbers validation with incorrect counts"""
        if not config_id:
            self.log_test("Serial Numbers Validation", False, "No configuration ID available")
            return
            
        # Test with wrong number of items (should be 50, providing 30)
        invalid_data = {
            "configuration_id": config_id,
            "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],  # Correct: 5 cases
            "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(30)]  # Wrong: 30 items instead of 50
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                error_msg = response.json().get("detail", "")
                if "Expected 50 item serial numbers" in error_msg:
                    self.log_test("Serial Numbers Validation", True, "Validation correctly rejected wrong item count")
                else:
                    self.log_test("Serial Numbers Validation", False, f"Wrong error message: {error_msg}")
            else:
                self.log_test("Serial Numbers Validation", False, f"Expected 400 error, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Serial Numbers Validation", False, f"Request error: {str(e)}")
    
    def test_epcis_generation(self, config_id):
        """Test POST /api/generate-epcis and validate XML output"""
        if not config_id:
            self.log_test("EPCIS Generation", False, "No configuration ID available")
            return
            
        test_data = {
            "configuration_id": config_id,
            "company_prefix": "1234567",
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
                # Check if response is XML
                content_type = response.headers.get('content-type', '')
                if 'xml' in content_type:
                    xml_content = response.text
                    if self.validate_epcis_xml(xml_content):
                        self.log_test("EPCIS Generation", True, "Valid EPCIS XML generated successfully",
                                    f"XML length: {len(xml_content)} characters")
                    else:
                        self.log_test("EPCIS Generation", False, "Generated XML is not valid EPCIS format")
                else:
                    self.log_test("EPCIS Generation", False, f"Expected XML, got content-type: {content_type}")
            else:
                self.log_test("EPCIS Generation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("EPCIS Generation", False, f"Request error: {str(e)}")
    
    def validate_epcis_xml(self, xml_content):
        """Validate that the generated XML is proper EPCIS format"""
        try:
            root = ET.fromstring(xml_content)
            
            # Check root element (handle namespace)
            if not root.tag.endswith("EPCISDocument"):
                print(f"   Invalid root element: {root.tag}")
                return False
            
            # Check namespace (it's embedded in the tag name when parsed)
            if not root.tag.startswith("{urn:epcglobal:epcis:xsd:2}"):
                print(f"   Invalid or missing EPCIS namespace in tag: {root.tag}")
                return False
            
            # Define namespace for finding elements
            ns = {"epcis": "urn:epcglobal:epcis:xsd:2"}
            
            # Check for EPCISBody (with namespace in tag)
            epcis_body = None
            for child in root:
                if child.tag.endswith("EPCISBody"):
                    epcis_body = child
                    break
            
            if epcis_body is None:
                print(f"   Missing EPCISBody element")
                return False
            
            # Check for EventList
            event_list = None
            for child in epcis_body:
                if child.tag.endswith("EventList"):
                    event_list = child
                    break
                    
            if event_list is None:
                print(f"   Missing EventList element")
                return False
            
            # Check for AggregationEvents
            aggregation_events = []
            for child in event_list:
                if child.tag.endswith("AggregationEvent"):
                    aggregation_events.append(child)
            
            if len(aggregation_events) != 5:  # Should have 5 events for 5 cases
                print(f"   Expected 5 AggregationEvents, found {len(aggregation_events)}")
                return False
            
            # Validate first aggregation event structure
            first_event = aggregation_events[0]
            required_elements = ["eventTime", "parentID", "childEPCs", "action", "bizStep"]
            
            # Helper function to find element by tag ending
            def find_element_by_ending(parent, tag_ending):
                for child in parent:
                    if child.tag.endswith(tag_ending):
                        return child
                return None
            
            for element in required_elements:
                elem = find_element_by_ending(first_event, element)
                if elem is None:
                    print(f"   Missing required element in AggregationEvent: {element}")
                    return False
            
            # Check parent ID format (should be SSCC)
            parent_id_elem = find_element_by_ending(first_event, "parentID")
            parent_id = parent_id_elem.text
            if not parent_id.startswith("urn:epc:id:sscc:"):
                print(f"   Invalid parent ID format: {parent_id}")
                return False
            
            # Check child EPCs format (should be SGTIN)
            child_epcs_elem = find_element_by_ending(first_event, "childEPCs")
            epcs = []
            for child in child_epcs_elem:
                if child.tag.endswith("epc"):
                    epcs.append(child)
            
            if len(epcs) != 10:  # Should have 10 items per case
                print(f"   Expected 10 child EPCs per case, found {len(epcs)}")
                return False
            
            for epc in epcs:
                if not epc.text.startswith("urn:epc:id:sgtin:"):
                    print(f"   Invalid child EPC format: {epc.text}")
                    return False
            
            # Check action
            action_elem = find_element_by_ending(first_event, "action")
            action = action_elem.text
            if action != "ADD":
                print(f"   Expected action 'ADD', found '{action}'")
                return False
            
            print(f"   ✓ Valid EPCIS XML with {len(aggregation_events)} aggregation events")
            print(f"   ✓ Parent ID format: {parent_id}")
            print(f"   ✓ Child EPCs per case: {len(epcs)}")
            return True
            
        except ET.ParseError as e:
            print(f"   XML parsing error: {str(e)}")
            return False
        except Exception as e:
            print(f"   Validation error: {str(e)}")
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
        """Run all backend tests in sequence"""
        print("=" * 60)
        print("EPCIS BACKEND API TESTING")
        print("=" * 60)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Configuration Creation
        config_id = self.test_configuration_creation()
        
        # Test 3: Configuration Validation
        self.test_configuration_validation()
        
        # Test 4: Serial Numbers Creation (requires config_id)
        serial_id = self.test_serial_numbers_creation(config_id)
        
        # Test 5: Serial Numbers Validation
        self.test_serial_numbers_validation(config_id)
        
        # Test 6: EPCIS Generation
        self.test_epcis_generation(config_id)
        
        # Test 7: Error Handling
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
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
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)