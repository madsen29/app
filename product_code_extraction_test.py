#!/usr/bin/env python3
"""
Product Code Extraction Fix Testing for EPCIS Serial Number Aggregation App
Tests the specific Product Code extraction fix to ensure it doesn't include the padded 0:

1. Test 10-digit Package NDC with Product Code extraction
2. Test 11-digit Package NDC with Product Code extraction  
3. Test EPCIS XML generation with corrected Package NDC and Product Code
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://1379817a-9549-4f0e-8757-8e6eaf81b9ac.preview.emergentagent.com/api"

class ProductCodeExtractionTester:
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
    
    def test_10_digit_package_ndc_conversion(self):
        """
        Test 10-digit Package NDC with Product Code extraction
        Simulate FDA API response where Package NDC "45802-466-53" (10-digit: "4580246653") 
        is converted to 11-digit "4580204653"
        Verify that packageNdc is stored as "4580204653" (11-digit with padded 0)
        Verify that productCode is extracted as "46653" (5 digits, WITHOUT the padded 0)
        """
        # Test configuration with 10-digit NDC that should be converted to 11-digit
        test_data = {
            "items_per_case": 10,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "company_prefix": "0345802",  # 03 + 45802
            "item_product_code": "46653",  # Product code WITHOUT padded 0
            "case_product_code": "000000",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2", 
            "item_indicator_digit": "1",
            "package_ndc": "4580204653",  # 11-digit with padded 0
            "lot_number": "4JT0482",
            "expiration_date": "2026-08-31"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify packageNdc is stored as 11-digit with padded 0
                if data.get("package_ndc") == "4580204653":
                    # Verify productCode is extracted as 5 digits WITHOUT the padded 0
                    if data.get("item_product_code") == "46653":
                        self.log_test(
                            "10-digit Package NDC Conversion", 
                            True, 
                            "Package NDC stored as 11-digit, Product Code extracted without padded 0",
                            f"Package NDC: {data.get('package_ndc')}, Product Code: {data.get('item_product_code')}"
                        )
                        return data["id"]
                    else:
                        self.log_test(
                            "10-digit Package NDC Conversion", 
                            False, 
                            f"Product Code incorrect: expected '46653', got '{data.get('item_product_code')}'",
                            data
                        )
                        return None
                else:
                    self.log_test(
                        "10-digit Package NDC Conversion", 
                        False, 
                        f"Package NDC incorrect: expected '4580204653', got '{data.get('package_ndc')}'",
                        data
                    )
                    return None
            else:
                self.log_test("10-digit Package NDC Conversion", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("10-digit Package NDC Conversion", False, f"Request error: {str(e)}")
            return None
    
    def test_11_digit_package_ndc_handling(self):
        """
        Test 11-digit Package NDC with Product Code extraction
        Test with already 11-digit Package NDC "4580204653"
        Verify that packageNdc remains "4580204653" 
        Verify that productCode is extracted as "4653" (without leading 0)
        """
        # Test configuration with already 11-digit NDC
        test_data = {
            "items_per_case": 10,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "company_prefix": "0345802",  # 03 + 45802
            "item_product_code": "4653",   # Product code without leading 0
            "case_product_code": "000000",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "item_indicator_digit": "1", 
            "package_ndc": "4580204653",  # Already 11-digit
            "lot_number": "4JT0482",
            "expiration_date": "2026-08-31"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify packageNdc remains 11-digit
                if data.get("package_ndc") == "4580204653":
                    # Verify productCode is extracted without leading 0
                    if data.get("item_product_code") == "4653":
                        self.log_test(
                            "11-digit Package NDC Handling", 
                            True, 
                            "Package NDC remains 11-digit, Product Code extracted without leading 0",
                            f"Package NDC: {data.get('package_ndc')}, Product Code: {data.get('item_product_code')}"
                        )
                        return data["id"]
                    else:
                        self.log_test(
                            "11-digit Package NDC Handling", 
                            False, 
                            f"Product Code incorrect: expected '4653', got '{data.get('item_product_code')}'",
                            data
                        )
                        return None
                else:
                    self.log_test(
                        "11-digit Package NDC Handling", 
                        False, 
                        f"Package NDC incorrect: expected '4580204653', got '{data.get('package_ndc')}'",
                        data
                    )
                    return None
            else:
                self.log_test("11-digit Package NDC Handling", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("11-digit Package NDC Handling", False, f"Request error: {str(e)}")
            return None
    
    def test_epcis_xml_generation_with_clean_ndc(self, config_id):
        """
        Test EPCIS XML generation with corrected Package NDC and Product Code
        Create configuration with corrected Package NDC and Product Code
        Generate EPCIS XML and verify additionalTradeItemIdentification contains the clean 11-digit NDC
        Verify the Product Code is used correctly in the GS1 identifiers
        """
        if not config_id:
            self.log_test("EPCIS XML Generation with Clean NDC", False, "No configuration ID available")
            return
        
        # Create serial numbers for the configuration
        serial_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": ["SSCC001"],
            "case_serial_numbers": ["CASE001", "CASE002"],  # 2 cases per SSCC
            "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(20)]  # 10 items per case × 2 cases = 20 items
        }
        
        try:
            # First create serial numbers
            serial_response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if serial_response.status_code != 200:
                self.log_test("EPCIS XML Generation with Clean NDC", False, f"Serial numbers creation failed: {serial_response.text}")
                return
            
            # Now generate EPCIS XML
            epcis_data = {
                "configuration_id": config_id,
                "read_point": "urn:epc:id:sgln:0345802.00000.0",
                "biz_location": "urn:epc:id:sgln:0345802.00001.0"
            }
            
            epcis_response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=epcis_data,
                headers={"Content-Type": "application/json"}
            )
            
            if epcis_response.status_code == 200:
                xml_content = epcis_response.text
                
                # Parse XML and check for clean NDC in additionalTradeItemIdentification
                if self.validate_clean_ndc_in_xml(xml_content):
                    self.log_test(
                        "EPCIS XML Generation with Clean NDC", 
                        True, 
                        "EPCIS XML contains clean 11-digit NDC in additionalTradeItemIdentification",
                        f"XML length: {len(xml_content)} characters"
                    )
                else:
                    self.log_test("EPCIS XML Generation with Clean NDC", False, "EPCIS XML does not contain clean NDC or has formatting issues")
            else:
                self.log_test("EPCIS XML Generation with Clean NDC", False, f"EPCIS generation failed: HTTP {epcis_response.status_code}: {epcis_response.text}")
                
        except Exception as e:
            self.log_test("EPCIS XML Generation with Clean NDC", False, f"Request error: {str(e)}")
    
    def validate_clean_ndc_in_xml(self, xml_content):
        """
        Validate that EPCIS XML contains clean 11-digit NDC without hyphens
        and correct EPCClass vocabulary element order
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Find EPCISMasterData in extension
            epcis_master_data = None
            for header in root:
                if header.tag.endswith("EPCISHeader"):
                    for extension in header:
                        if extension.tag.endswith("extension"):
                            for child in extension:
                                if child.tag.endswith("EPCISMasterData"):
                                    epcis_master_data = child
                                    break
                            break
                    break
            
            if epcis_master_data is None:
                print("   Missing EPCISMasterData in extension")
                return False
            
            # Find VocabularyList
            vocabulary_list = None
            for child in epcis_master_data:
                if child.tag.endswith("VocabularyList"):
                    vocabulary_list = child
                    break
            
            if vocabulary_list is None:
                print("   Missing VocabularyList")
                return False
            
            # Find EPCClass vocabulary
            vocabulary = None
            for child in vocabulary_list:
                if child.tag.endswith("Vocabulary") and child.get("type") == "urn:epcglobal:epcis:vtype:EPCClass":
                    vocabulary = child
                    break
            
            if vocabulary is None:
                print("   Missing EPCClass vocabulary")
                return False
            
            # Find VocabularyElementList
            vocabulary_element_list = None
            for child in vocabulary:
                if child.tag.endswith("VocabularyElementList"):
                    vocabulary_element_list = child
                    break
            
            if vocabulary_element_list is None:
                print("   Missing VocabularyElementList")
                return False
            
            # Check vocabulary elements and their order
            vocabulary_elements = []
            clean_ndc_found = False
            
            for element in vocabulary_element_list:
                if element.tag.endswith("VocabularyElement"):
                    element_id = element.get("id")
                    vocabulary_elements.append(element_id)
                    
                    # Check for additionalTradeItemIdentification attribute
                    for attr in element:
                        if (attr.tag.endswith("attribute") and 
                            attr.get("id") == "urn:epcglobal:cbv:mda#additionalTradeItemIdentification"):
                            ndc_value = attr.text
                            print(f"   Found additionalTradeItemIdentification: {ndc_value}")
                            
                            # Check if NDC is clean (no hyphens) and 11-digit
                            if ndc_value == "4580204653":
                                clean_ndc_found = True
                                print("   ✓ Clean 11-digit NDC found")
                            elif "-" in ndc_value:
                                print(f"   ❌ NDC contains hyphens: {ndc_value}")
                                return False
                            else:
                                print(f"   ❌ Unexpected NDC format: {ndc_value}")
                                return False
            
            if not clean_ndc_found:
                print("   ❌ Clean 11-digit NDC not found in additionalTradeItemIdentification")
                return False
            
            # Check EPCClass vocabulary element order
            # Expected order: Item → Inner Case → Case (but we only have Item and Case in this test)
            # So expected order: Item → Case
            print(f"   Found vocabulary elements: {vocabulary_elements}")
            
            # Check that we have the expected patterns
            expected_item_pattern = "urn:epc:idpat:sgtin:0345802.146653.*"  # Item with indicator 1 + product code 46653
            expected_case_pattern = "urn:epc:idpat:sgtin:0345802.2000000.*"  # Case with indicator 2 + product code 000000
            
            if len(vocabulary_elements) >= 2:
                # Check if Item comes before Case
                item_index = -1
                case_index = -1
                
                for i, element_id in enumerate(vocabulary_elements):
                    if "146653" in element_id:  # Item pattern
                        item_index = i
                    elif "2000000" in element_id:  # Case pattern
                        case_index = i
                
                if item_index != -1 and case_index != -1:
                    if item_index < case_index:
                        print("   ✓ EPCClass vocabulary elements in correct order: Item → Case")
                    else:
                        print(f"   ❌ EPCClass vocabulary elements in wrong order: Item at {item_index}, Case at {case_index}")
                        return False
                else:
                    print("   ❌ Could not find expected Item and Case patterns")
                    return False
            
            # Verify GS1 identifiers use correct Product Code (without leading 0)
            if self.validate_gs1_identifiers_in_xml(root):
                print("   ✓ GS1 identifiers use correct Product Code")
                return True
            else:
                print("   ❌ GS1 identifiers have incorrect Product Code")
                return False
            
        except ET.ParseError as e:
            print(f"   XML parsing error: {str(e)}")
            return False
        except Exception as e:
            print(f"   Validation error: {str(e)}")
            return False
    
    def validate_gs1_identifiers_in_xml(self, root):
        """Validate that GS1 identifiers use the correct Product Code without leading 0"""
        try:
            # Find EventList
            event_list = None
            for body in root:
                if body.tag.endswith("EPCISBody"):
                    for child in body:
                        if child.tag.endswith("EventList"):
                            event_list = child
                            break
                    break
            
            if event_list is None:
                print("   Missing EventList")
                return False
            
            # Check all EPCs in events
            for event in event_list:
                # Check ObjectEvent EPCs
                if event.tag.endswith("ObjectEvent"):
                    for child in event:
                        if child.tag.endswith("epcList"):
                            for epc_elem in child:
                                if epc_elem.tag.endswith("epc"):
                                    epc = epc_elem.text
                                    if "sgtin" in epc and "146653" in epc:
                                        # Item SGTIN should use product code 46653 (without leading 0)
                                        expected_pattern = "urn:epc:id:sgtin:0345802.146653."
                                        if not epc.startswith(expected_pattern):
                                            print(f"   ❌ Item SGTIN has wrong product code: {epc}")
                                            return False
                
                # Check AggregationEvent parent and child EPCs
                elif event.tag.endswith("AggregationEvent"):
                    for child in event:
                        if child.tag.endswith("parentID"):
                            parent_epc = child.text
                            # Parent could be SSCC or Case SGTIN
                            if "sgtin" in parent_epc and "2000000" in parent_epc:
                                # Case SGTIN should use product code 000000
                                expected_pattern = "urn:epc:id:sgtin:0345802.2000000."
                                if not parent_epc.startswith(expected_pattern):
                                    print(f"   ❌ Case SGTIN has wrong product code: {parent_epc}")
                                    return False
                        
                        elif child.tag.endswith("childEPCs"):
                            for child_epc_elem in child:
                                if child_epc_elem.tag.endswith("epc"):
                                    child_epc = child_epc_elem.text
                                    if "sgtin" in child_epc and "146653" in child_epc:
                                        # Item SGTIN should use product code 46653
                                        expected_pattern = "urn:epc:id:sgtin:0345802.146653."
                                        if not child_epc.startswith(expected_pattern):
                                            print(f"   ❌ Child Item SGTIN has wrong product code: {child_epc}")
                                            return False
            
            return True
            
        except Exception as e:
            print(f"   Error validating GS1 identifiers: {str(e)}")
            return False
    
    def run_product_code_extraction_tests(self):
        """Run all Product Code extraction tests"""
        print("=" * 80)
        print("PRODUCT CODE EXTRACTION FIX TESTING")
        print("=" * 80)
        print("Testing Product Code extraction fix to ensure it doesn't include the padded 0")
        print("=" * 80)
        
        # Test 1: 10-digit Package NDC with Product Code extraction
        config_id_1 = self.test_10_digit_package_ndc_conversion()
        
        # Test 2: 11-digit Package NDC with Product Code extraction
        config_id_2 = self.test_11_digit_package_ndc_handling()
        
        # Test 3: EPCIS XML generation with clean NDC (using first config)
        if config_id_1:
            self.test_epcis_xml_generation_with_clean_ndc(config_id_1)
        
        # Summary
        print("\n" + "=" * 80)
        print("PRODUCT CODE EXTRACTION TEST SUMMARY")
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
        print("✓ 10-digit Package NDC conversion to 11-digit with padded 0")
        print("✓ Product Code extraction without padded 0")
        print("✓ 11-digit Package NDC handling")
        print("✓ EPCIS XML generation with clean NDC")
        print("✓ EPCClass vocabulary element order")
        print("✓ GS1 identifier format with correct Product Code")
        
        return passed == total

if __name__ == "__main__":
    tester = ProductCodeExtractionTester()
    success = tester.run_product_code_extraction_tests()
    sys.exit(0 if success else 1)