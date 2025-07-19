#!/usr/bin/env python3
"""
EPCClass Data Integration Testing for EPCIS Serial Number Aggregation App
Tests the EPCClass functionality as requested in the review:
1. Configuration API with EPCClass fields
2. EPCIS XML Generation with EPCISMasterData section
3. Complete workflow test with EPCClass data
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class EPCClassTester:
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
    
    def test_configuration_with_epcclass_data(self):
        """Test Configuration API with EPCClass fields using review request data"""
        test_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 1,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000001",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "item_indicator_digit": "1",
            # EPCClass data from review request
            "product_ndc": "45802-046-85",
            "regulated_product_name": "RX ECONAZOLE NITRATE 1% CRM 85G",
            "manufacturer_name": "Padagis LLC",
            "dosage_form_type": "CREAM",
            "strength_description": "10 mg/g",
            "net_content_description": "85GM     Wgt"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all EPCClass fields are properly stored
                epcclass_fields = [
                    "product_ndc", "regulated_product_name", "manufacturer_name",
                    "dosage_form_type", "strength_description", "net_content_description"
                ]
                
                missing_fields = []
                incorrect_values = []
                
                for field in epcclass_fields:
                    if field not in data:
                        missing_fields.append(field)
                    elif data[field] != test_data[field]:
                        incorrect_values.append(f"{field}: expected '{test_data[field]}', got '{data[field]}'")
                
                if missing_fields:
                    self.log_test("Configuration with EPCClass Data", False, 
                                f"Missing EPCClass fields: {missing_fields}")
                    print(f"   Actual response data: {json.dumps(data, indent=2)}")
                    return None
                elif incorrect_values:
                    self.log_test("Configuration with EPCClass Data", False, 
                                f"Incorrect EPCClass values: {incorrect_values}")
                    return None
                else:
                    self.log_test("Configuration with EPCClass Data", True, 
                                "All EPCClass fields properly stored",
                                f"NDC: {data['product_ndc']}, Product: {data['regulated_product_name']}")
                    return data["id"]
            else:
                self.log_test("Configuration with EPCClass Data", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration with EPCClass Data", False, f"Request error: {str(e)}")
            return None
    
    def test_epcis_xml_with_epcismasterdata(self, config_id):
        """Test EPCIS XML Generation includes EPCISMasterData with EPCClass vocabulary"""
        if not config_id:
            self.log_test("EPCIS XML with EPCISMasterData", False, "No configuration ID available")
            return None
            
        # First, create serial numbers for the configuration
        serial_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": ["SSCC001"],
            "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],  # 5 cases
            "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(50)]  # 50 items (10 per case × 5 cases)
        }
        
        try:
            # Create serial numbers first
            serial_response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if serial_response.status_code != 200:
                self.log_test("EPCIS XML with EPCISMasterData", False, 
                            f"Failed to create serial numbers: {serial_response.status_code}")
                return None
            
            # Generate EPCIS XML
            epcis_data = {
                "configuration_id": config_id,
                "read_point": "urn:epc:id:sgln:1234567.00000.0",
                "biz_location": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=epcis_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Validate EPCISMasterData structure
                if self.validate_epcismasterdata_structure(xml_content):
                    self.log_test("EPCIS XML with EPCISMasterData", True, 
                                "EPCIS XML includes proper EPCISMasterData with EPCClass vocabulary",
                                f"XML length: {len(xml_content)} characters")
                    return xml_content
                else:
                    self.log_test("EPCIS XML with EPCISMasterData", False, 
                                "EPCISMasterData structure validation failed")
                    return None
            else:
                self.log_test("EPCIS XML with EPCISMasterData", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("EPCIS XML with EPCISMasterData", False, f"Request error: {str(e)}")
            return None
    
    def validate_epcismasterdata_structure(self, xml_content):
        """Validate EPCISMasterData structure with EPCClass vocabulary"""
        try:
            root = ET.fromstring(xml_content)
            
            # Find EPCISHeader
            epcis_header = None
            for child in root:
                if child.tag.endswith("EPCISHeader"):
                    epcis_header = child
                    break
            
            if epcis_header is None:
                print("   Missing EPCISHeader element")
                return False
            
            # Find EPCISMasterData
            epcis_master_data = None
            for child in epcis_header:
                if child.tag.endswith("EPCISMasterData"):
                    epcis_master_data = child
                    break
            
            if epcis_master_data is None:
                print("   Missing EPCISMasterData element")
                return False
            
            # Find VocabularyList
            vocabulary_list = None
            for child in epcis_master_data:
                if child.tag.endswith("VocabularyList"):
                    vocabulary_list = child
                    break
            
            if vocabulary_list is None:
                print("   Missing VocabularyList element")
                return False
            
            # Find EPCClass Vocabulary
            epcclass_vocabulary = None
            for child in vocabulary_list:
                if child.tag.endswith("Vocabulary"):
                    vocab_type = child.get("type")
                    if vocab_type == "urn:epcglobal:epcis:vtype:EPCClass":
                        epcclass_vocabulary = child
                        break
            
            if epcclass_vocabulary is None:
                print("   Missing EPCClass Vocabulary element")
                return False
            
            # Find VocabularyElementList
            vocabulary_element_list = None
            for child in epcclass_vocabulary:
                if child.tag.endswith("VocabularyElementList"):
                    vocabulary_element_list = child
                    break
            
            if vocabulary_element_list is None:
                print("   Missing VocabularyElementList element")
                return False
            
            # Find VocabularyElement
            vocabulary_element = None
            for child in vocabulary_element_list:
                if child.tag.endswith("VocabularyElement"):
                    vocabulary_element = child
                    break
            
            if vocabulary_element is None:
                print("   Missing VocabularyElement element")
                return False
            
            # Check VocabularyElement ID format
            element_id = vocabulary_element.get("id")
            expected_pattern = "urn:epc:idpat:sgtin:1234567.1000000.*"
            if element_id != expected_pattern:
                print(f"   Incorrect VocabularyElement ID: expected '{expected_pattern}', got '{element_id}'")
                return False
            
            # Validate EPCClass attributes
            expected_attributes = {
                "urn:epcglobal:cbv:mda#additionalTradeItemIdentification": "45802-046-85",
                "urn:epcglobal:cbv:mda#additionalTradeItemIdentificationTypeCode": "FDA_NDC_11",
                "urn:epcglobal:cbv:mda#regulatedProductName": "RX ECONAZOLE NITRATE 1% CRM 85G",
                "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName": "Padagis LLC",
                "urn:epcglobal:cbv:mda#dosageFormType": "CREAM",
                "urn:epcglobal:cbv:mda#strengthDescription": "10 mg/g",
                "urn:epcglobal:cbv:mda#netContentDescription": "85GM     Wgt"
            }
            
            found_attributes = {}
            for child in vocabulary_element:
                if child.tag.endswith("attribute"):
                    attr_id = child.get("id")
                    attr_value = child.text
                    found_attributes[attr_id] = attr_value
            
            missing_attributes = []
            incorrect_values = []
            
            for expected_id, expected_value in expected_attributes.items():
                if expected_id not in found_attributes:
                    missing_attributes.append(expected_id)
                elif found_attributes[expected_id] != expected_value:
                    incorrect_values.append(f"{expected_id}: expected '{expected_value}', got '{found_attributes[expected_id]}'")
            
            if missing_attributes:
                print(f"   Missing EPCClass attributes: {missing_attributes}")
                return False
            
            if incorrect_values:
                print(f"   Incorrect EPCClass attribute values: {incorrect_values}")
                return False
            
            print("   ✓ EPCISMasterData structure is valid")
            print("   ✓ EPCClass vocabulary element found with correct ID pattern")
            print(f"   ✓ All {len(expected_attributes)} EPCClass attributes present with correct values")
            return True
            
        except ET.ParseError as e:
            print(f"   XML parsing error: {str(e)}")
            return False
        except Exception as e:
            print(f"   Validation error: {str(e)}")
            return False
    
    def test_complete_workflow_with_epcclass(self):
        """Test complete workflow: Configuration → Serial Numbers → EPCIS XML with EPCClass data"""
        print("\n" + "=" * 60)
        print("COMPLETE WORKFLOW TEST WITH EPCCLASS DATA")
        print("=" * 60)
        
        # Step 1: Create configuration with EPCClass data
        config_id = self.test_configuration_with_epcclass_data()
        if not config_id:
            self.log_test("Complete Workflow", False, "Failed at configuration creation step")
            return False
        
        # Step 2: Generate EPCIS XML with EPCISMasterData
        xml_content = self.test_epcis_xml_with_epcismasterdata(config_id)
        if not xml_content:
            self.log_test("Complete Workflow", False, "Failed at EPCIS XML generation step")
            return False
        
        # Step 3: Validate complete XML structure
        if self.validate_complete_xml_structure(xml_content):
            self.log_test("Complete Workflow", True, 
                        "Complete workflow successful: Configuration → Serial Numbers → EPCIS XML with EPCClass data")
            return True
        else:
            self.log_test("Complete Workflow", False, "Complete XML structure validation failed")
            return False
    
    def validate_complete_xml_structure(self, xml_content):
        """Validate that XML contains both EPCISMasterData and event data"""
        try:
            root = ET.fromstring(xml_content)
            
            # Check for EPCISMasterData
            has_master_data = False
            has_event_data = False
            
            for child in root:
                if child.tag.endswith("EPCISHeader"):
                    for header_child in child:
                        if header_child.tag.endswith("EPCISMasterData"):
                            has_master_data = True
                            break
                elif child.tag.endswith("EPCISBody"):
                    for body_child in child:
                        if body_child.tag.endswith("EventList"):
                            # Check if EventList has events
                            event_count = len(list(body_child))
                            if event_count > 0:
                                has_event_data = True
                            break
            
            if not has_master_data:
                print("   Missing EPCISMasterData in complete XML")
                return False
            
            if not has_event_data:
                print("   Missing event data in EPCISBody")
                return False
            
            print("   ✓ Complete XML contains both EPCISMasterData and event data")
            return True
            
        except Exception as e:
            print(f"   Error validating complete XML structure: {str(e)}")
            return False
    
    def run_epcclass_tests(self):
        """Run all EPCClass-specific tests"""
        print("=" * 80)
        print("EPCCLASS DATA INTEGRATION TESTING")
        print("=" * 80)
        print("Testing EPCClass functionality as requested in review:")
        print("1. Configuration API with EPCClass fields")
        print("2. EPCIS XML Generation with EPCISMasterData")
        print("3. Complete workflow test")
        print("=" * 80)
        
        # Test complete workflow
        workflow_success = self.test_complete_workflow_with_epcclass()
        
        # Summary
        print("\n" + "=" * 80)
        print("EPCCLASS TEST SUMMARY")
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
        
        print("\nEPCClass Features Tested:")
        print("✓ Configuration API stores EPCClass fields:")
        print("  - product_ndc")
        print("  - regulated_product_name") 
        print("  - manufacturer_name")
        print("  - dosage_form_type")
        print("  - strength_description")
        print("  - net_content_description")
        print("✓ EPCIS XML includes EPCISMasterData section")
        print("✓ VocabularyList contains EPCClass vocabulary")
        print("✓ EPCClass attributes properly formatted")
        print("✓ Complete workflow integration")
        
        return passed == total

if __name__ == "__main__":
    tester = EPCClassTester()
    success = tester.run_epcclass_tests()
    sys.exit(0 if success else 1)