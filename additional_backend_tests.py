#!/usr/bin/env python3
"""
Additional Backend Tests for EPCIS Configuration API
Tests specific scenarios requested in the review:
1. Default configuration (numberOfSscc: 1, casesPerSscc: 5, itemsPerCase: 10)
2. Edge cases (casesPerSscc: 0 for direct SSCC→Items aggregation)
3. Inner Cases enabled (useInnerCases: true)
4. Specific test data from review request
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class AdditionalBackendTester:
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
    
    def test_default_configuration(self):
        """Test with default configuration as specified in review"""
        test_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 1,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "111111",
            "sscc_indicator_digit": "0",
            "case_indicator_digit": "0",
            "item_indicator_digit": "0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (data["items_per_case"] == 10 and data["cases_per_sscc"] == 5 and 
                    data["number_of_sscc"] == 1 and "id" in data):
                    self.log_test("Default Configuration", True, 
                                "Default configuration (1 SSCC, 5 cases, 10 items/case) created successfully",
                                f"Config ID: {data['id']}")
                    return data["id"]
                else:
                    self.log_test("Default Configuration", False, "Configuration data mismatch", data)
                    return None
            else:
                self.log_test("Default Configuration", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Default Configuration", False, f"Request error: {str(e)}")
            return None
    
    def test_edge_case_direct_sscc_items(self):
        """Test edge case: casesPerSscc: 0 for direct SSCC→Items aggregation"""
        test_data = {
            "items_per_case": 10,  # In this case, this means items_per_sscc
            "cases_per_sscc": 0,   # Edge case: no cases, direct SSCC→Items
            "number_of_sscc": 1,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "111111",  # Won't be used
            "sscc_indicator_digit": "0",
            "case_indicator_digit": "0",
            "item_indicator_digit": "0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                config_id = data["id"]
                
                # Test serial numbers for this edge case
                serial_data = {
                    "configuration_id": config_id,
                    "sscc_serial_numbers": ["SSCC001"],
                    "case_serial_numbers": [],  # No cases expected
                    "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(10)]  # 10 items directly in SSCC
                }
                
                serial_response = self.session.post(
                    f"{self.base_url}/serial-numbers",
                    json=serial_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if serial_response.status_code == 200:
                    # Test EPCIS generation for direct SSCC→Items
                    epcis_data = {
                        "configuration_id": config_id,
                        "read_point": "urn:epc:id:sgln:1234567.00000.0",
                        "biz_location": "urn:epc:id:sgln:1234567.00001.0"
                    }
                    
                    epcis_response = self.session.post(
                        f"{self.base_url}/generate-epcis",
                        json=epcis_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if epcis_response.status_code == 200:
                        # Validate the XML has direct SSCC→Items aggregation
                        xml_content = epcis_response.text
                        if self.validate_direct_sscc_items_xml(xml_content):
                            self.log_test("Edge Case Direct SSCC→Items", True, 
                                        "Direct SSCC→Items aggregation (casesPerSscc: 0) works correctly",
                                        "XML contains direct aggregation without cases")
                        else:
                            self.log_test("Edge Case Direct SSCC→Items", False, 
                                        "EPCIS XML validation failed for direct aggregation")
                    else:
                        self.log_test("Edge Case Direct SSCC→Items", False, 
                                    f"EPCIS generation failed: {epcis_response.status_code}")
                else:
                    self.log_test("Edge Case Direct SSCC→Items", False, 
                                f"Serial numbers creation failed: {serial_response.status_code}")
            else:
                self.log_test("Edge Case Direct SSCC→Items", False, 
                            f"Configuration creation failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Edge Case Direct SSCC→Items", False, f"Request error: {str(e)}")
    
    def test_inner_cases_enabled(self):
        """Test with Inner Cases enabled (useInnerCases: true)"""
        test_data = {
            "items_per_case": 0,  # Not used when inner cases enabled
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": True,
            "inner_cases_per_case": 3,
            "items_per_inner_case": 5,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "111111",
            "inner_case_product_code": "222222",
            "sscc_indicator_digit": "0",
            "case_indicator_digit": "0",
            "inner_case_indicator_digit": "0",
            "item_indicator_digit": "0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                config_id = data["id"]
                
                # Calculate expected quantities: 1 SSCC, 2 cases, 6 inner cases (3×2), 30 items (5×6)
                serial_data = {
                    "configuration_id": config_id,
                    "sscc_serial_numbers": ["SSCC001"],
                    "case_serial_numbers": ["CASE001", "CASE002"],
                    "inner_case_serial_numbers": [f"INNER{i+1:03d}" for i in range(6)],
                    "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(30)]
                }
                
                serial_response = self.session.post(
                    f"{self.base_url}/serial-numbers",
                    json=serial_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if serial_response.status_code == 200:
                    self.log_test("Inner Cases Configuration", True, 
                                "Inner cases configuration and serial numbers created successfully",
                                "1 SSCC → 2 Cases → 6 Inner Cases → 30 Items")
                else:
                    self.log_test("Inner Cases Configuration", False, 
                                f"Serial numbers creation failed: {serial_response.status_code} - {serial_response.text}")
            else:
                self.log_test("Inner Cases Configuration", False, 
                            f"Configuration creation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Inner Cases Configuration", False, f"Request error: {str(e)}")
    
    def test_specific_review_data(self):
        """Test with specific data from review request"""
        test_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 1,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "111111",
            "sscc_indicator_digit": "0",
            "case_indicator_digit": "0",
            "item_indicator_digit": "0"
        }
        
        try:
            # Step 1: Save configuration
            config_response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if config_response.status_code != 200:
                self.log_test("Complete Workflow Test", False, 
                            f"Configuration creation failed: {config_response.status_code}")
                return
            
            config_data = config_response.json()
            config_id = config_data["id"]
            
            # Verify configuration_id is returned
            if not config_id:
                self.log_test("Complete Workflow Test", False, "Configuration ID not returned")
                return
            
            # Step 2: Save serial numbers
            serial_data = {
                "configuration_id": config_id,
                "sscc_serial_numbers": ["SSCC001"],
                "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],
                "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(50)]
            }
            
            serial_response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if serial_response.status_code != 200:
                self.log_test("Complete Workflow Test", False, 
                            f"Serial numbers creation failed: {serial_response.status_code}")
                return
            
            # Step 3: Generate EPCIS XML
            epcis_data = {
                "configuration_id": config_id,
                "read_point": "urn:epc:id:sgln:1234567.00000.0",
                "biz_location": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            epcis_response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=epcis_data,
                headers={"Content-Type": "application/json"}
            )
            
            if epcis_response.status_code == 200:
                # Verify all fields are properly saved
                if (config_data["company_prefix"] == "1234567" and 
                    config_data["item_product_code"] == "000000" and
                    config_data["sscc_indicator_digit"] == "0"):
                    self.log_test("Complete Workflow Test", True, 
                                "Complete workflow (save config → save serials → generate EPCIS) successful",
                                f"Config ID: {config_id}, XML generated successfully")
                else:
                    self.log_test("Complete Workflow Test", False, 
                                "GS1 parameters not properly saved")
            else:
                self.log_test("Complete Workflow Test", False, 
                            f"EPCIS generation failed: {epcis_response.status_code}")
                
        except Exception as e:
            self.log_test("Complete Workflow Test", False, f"Request error: {str(e)}")
    
    def test_required_field_validation(self):
        """Test validation for required fields"""
        # Test missing company_prefix
        invalid_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 1,
            # Missing company_prefix and other required GS1 fields
            "item_product_code": "000000"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [400, 422]:
                self.log_test("Required Field Validation", True, 
                            "Missing required fields properly rejected")
            else:
                self.log_test("Required Field Validation", False, 
                            f"Expected validation error, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Required Field Validation", False, f"Request error: {str(e)}")
    
    def validate_direct_sscc_items_xml(self, xml_content):
        """Validate XML for direct SSCC→Items aggregation"""
        try:
            root = ET.fromstring(xml_content)
            
            # Find EventList
            event_list = None
            for elem in root.iter():
                if elem.tag.endswith("EventList"):
                    event_list = elem
                    break
            
            if event_list is None:
                return False
            
            # Count events - should have fewer events for direct aggregation
            aggregation_events = []
            for child in event_list:
                if child.tag.endswith("AggregationEvent"):
                    aggregation_events.append(child)
            
            # For direct SSCC→Items, should have only 1 aggregation event
            if len(aggregation_events) != 1:
                print(f"   Expected 1 aggregation event for direct SSCC→Items, found {len(aggregation_events)}")
                return False
            
            # Check that the aggregation event has SSCC as parent and items as children
            agg_event = aggregation_events[0]
            parent_id = None
            child_epcs = None
            
            for child in agg_event:
                if child.tag.endswith("parentID"):
                    parent_id = child
                elif child.tag.endswith("childEPCs"):
                    child_epcs = child
            
            if parent_id is None or child_epcs is None:
                return False
            
            # Parent should be SSCC
            if not parent_id.text.startswith("urn:epc:id:sscc:"):
                print(f"   Expected SSCC parent, got: {parent_id.text}")
                return False
            
            # Should have 10 child items
            child_count = len(list(child_epcs))
            if child_count != 10:
                print(f"   Expected 10 child items, found {child_count}")
                return False
            
            return True
            
        except Exception as e:
            print(f"   Error validating direct SSCC→Items XML: {str(e)}")
            return False
    
    def run_additional_tests(self):
        """Run all additional tests requested in the review"""
        print("=" * 80)
        print("ADDITIONAL BACKEND TESTS - CONFIGURATION API FOCUS")
        print("=" * 80)
        print("Testing specific scenarios from review request:")
        print("1. Default configuration (1 SSCC, 5 cases, 10 items/case)")
        print("2. Edge case: Direct SSCC→Items (casesPerSscc: 0)")
        print("3. Inner Cases enabled")
        print("4. Complete workflow validation")
        print("5. Required field validation")
        print("=" * 80)
        
        # Run all additional tests
        self.test_default_configuration()
        self.test_edge_case_direct_sscc_items()
        self.test_inner_cases_enabled()
        self.test_specific_review_data()
        self.test_required_field_validation()
        
        # Summary
        print("\n" + "=" * 80)
        print("ADDITIONAL TESTS SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Additional Tests: {total}")
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
    tester = AdditionalBackendTester()
    success = tester.run_additional_tests()
    print(f"\nAdditional tests {'PASSED' if success else 'FAILED'}")