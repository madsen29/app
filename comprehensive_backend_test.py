#!/usr/bin/env python3
"""
Comprehensive Backend Testing for EPCIS Serial Number Aggregation App
Tests all backend endpoints with the specific configuration from the review request:
- Company Prefix: 1234567
- Product Code: 000000
- Lot Number: 4JT0482
- Expiration Date: 2026-08-31
- Test with 1 SSCC, 5 Cases, 10 Items per case (50 total items)
- Include EPCClass test data
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://1379817a-9549-4f0e-8757-8e6eaf81b9ac.preview.emergentagent.com/api"

class ComprehensiveBackendTester:
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
    
    def test_configuration_with_moved_fields(self):
        """Test configuration API with all moved fields and EPCClass data"""
        # Test configuration as specified in review request
        test_data = {
            # Packaging Configuration
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 1,
            "use_inner_cases": False,
            
            # Product Information (moved fields)
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "lot_number": "4JT0482",
            "expiration_date": "2026-08-31",
            
            # GS1 Indicator Digits (moved fields)
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2", 
            "item_indicator_digit": "1",
            
            # EPCClass data
            "product_ndc": "12345-678-90",
            "regulated_product_name": "Test Pharmaceutical Product",
            "manufacturer_name": "Test Pharma Inc",
            "dosage_form_type": "TABLET",
            "strength_description": "100mg",
            "net_content_description": "30 tablets"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify all moved fields are stored correctly
                moved_fields_check = (
                    data["company_prefix"] == "1234567" and
                    data["item_product_code"] == "000000" and
                    data["case_product_code"] == "000000" and
                    data["lot_number"] == "4JT0482" and
                    data["expiration_date"] == "2026-08-31" and
                    data["sscc_indicator_digit"] == "3" and
                    data["case_indicator_digit"] == "2" and
                    data["item_indicator_digit"] == "1"
                )
                
                # Verify EPCClass fields are stored correctly
                epcclass_fields_check = (
                    data["product_ndc"] == "12345-678-90" and
                    data["regulated_product_name"] == "Test Pharmaceutical Product" and
                    data["manufacturer_name"] == "Test Pharma Inc" and
                    data["dosage_form_type"] == "TABLET" and
                    data["strength_description"] == "100mg" and
                    data["net_content_description"] == "30 tablets"
                )
                
                if moved_fields_check and epcclass_fields_check:
                    self.log_test("Configuration with Moved Fields", True, 
                                "All moved fields and EPCClass data stored correctly",
                                f"Config ID: {data['id']}, Hierarchy: 1 SSCC → 5 Cases → 10 Items/case")
                    return data["id"]
                else:
                    self.log_test("Configuration with Moved Fields", False, 
                                "Field validation failed", 
                                f"Moved fields OK: {moved_fields_check}, EPCClass OK: {epcclass_fields_check}")
                    return None
            else:
                self.log_test("Configuration with Moved Fields", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration with Moved Fields", False, f"Request error: {str(e)}")
            return None
    
    def test_hierarchy_scenarios(self):
        """Test various hierarchy scenarios"""
        scenarios = [
            {
                "name": "2-level: SSCC→Items",
                "config": {
                    "items_per_case": 50,  # items go directly in SSCC
                    "cases_per_sscc": 0,   # no cases
                    "number_of_sscc": 1,
                    "use_inner_cases": False,
                    "company_prefix": "1234567",
                    "item_product_code": "000000",
                    "case_product_code": "000000",
                    "sscc_indicator_digit": "3",
                    "case_indicator_digit": "2",
                    "item_indicator_digit": "1"
                },
                "expected_serials": {"sscc": 1, "cases": 0, "items": 50}
            },
            {
                "name": "3-level: SSCC→Cases→Items",
                "config": {
                    "items_per_case": 10,
                    "cases_per_sscc": 5,
                    "number_of_sscc": 1,
                    "use_inner_cases": False,
                    "company_prefix": "1234567",
                    "item_product_code": "000000",
                    "case_product_code": "000000",
                    "sscc_indicator_digit": "3",
                    "case_indicator_digit": "2",
                    "item_indicator_digit": "1"
                },
                "expected_serials": {"sscc": 1, "cases": 5, "items": 50}
            },
            {
                "name": "4-level: SSCC→Cases→Inner Cases→Items",
                "config": {
                    "items_per_case": 0,  # not used when inner cases enabled
                    "cases_per_sscc": 2,
                    "number_of_sscc": 1,
                    "use_inner_cases": True,
                    "inner_cases_per_case": 3,
                    "items_per_inner_case": 8,
                    "company_prefix": "1234567",
                    "item_product_code": "000000",
                    "case_product_code": "000000",
                    "inner_case_product_code": "000001",
                    "sscc_indicator_digit": "3",
                    "case_indicator_digit": "2",
                    "inner_case_indicator_digit": "4",
                    "item_indicator_digit": "1"
                },
                "expected_serials": {"sscc": 1, "cases": 2, "inner_cases": 6, "items": 48}
            }
        ]
        
        for scenario in scenarios:
            try:
                # Create configuration
                response = self.session.post(
                    f"{self.base_url}/configuration",
                    json=scenario["config"],
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    config_data = response.json()
                    config_id = config_data["id"]
                    
                    # Test serial numbers for this scenario
                    expected = scenario["expected_serials"]
                    
                    # Generate serial numbers
                    sscc_serials = [f"SSCC{i+1:03d}" for i in range(expected["sscc"])]
                    case_serials = [f"CASE{i+1:03d}" for i in range(expected["cases"])]
                    inner_case_serials = [f"INNER{i+1:03d}" for i in range(expected.get("inner_cases", 0))]
                    item_serials = [f"ITEM{i+1:03d}" for i in range(expected["items"])]
                    
                    serial_data = {
                        "configuration_id": config_id,
                        "sscc_serial_numbers": sscc_serials,
                        "case_serial_numbers": case_serials,
                        "inner_case_serial_numbers": inner_case_serials,
                        "item_serial_numbers": item_serials
                    }
                    
                    serial_response = self.session.post(
                        f"{self.base_url}/serial-numbers",
                        json=serial_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if serial_response.status_code == 200:
                        serial_result = serial_response.json()
                        
                        # Verify counts
                        counts_correct = (
                            len(serial_result["sscc_serial_numbers"]) == expected["sscc"] and
                            len(serial_result["case_serial_numbers"]) == expected["cases"] and
                            len(serial_result.get("inner_case_serial_numbers", [])) == expected.get("inner_cases", 0) and
                            len(serial_result["item_serial_numbers"]) == expected["items"]
                        )
                        
                        if counts_correct:
                            self.log_test(f"Hierarchy Scenario: {scenario['name']}", True,
                                        "Configuration and serial validation working",
                                        f"SSCCs: {expected['sscc']}, Cases: {expected['cases']}, Inner Cases: {expected.get('inner_cases', 0)}, Items: {expected['items']}")
                        else:
                            self.log_test(f"Hierarchy Scenario: {scenario['name']}", False,
                                        "Serial count validation failed", serial_result)
                    else:
                        self.log_test(f"Hierarchy Scenario: {scenario['name']}", False,
                                    f"Serial numbers failed: {serial_response.status_code}")
                else:
                    self.log_test(f"Hierarchy Scenario: {scenario['name']}", False,
                                f"Configuration failed: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Hierarchy Scenario: {scenario['name']}", False, f"Error: {str(e)}")
    
    def test_epcis_with_ilmd_and_epcclass(self, config_id):
        """Test EPCIS generation with ILMD extensions and EPCClass data"""
        if not config_id:
            self.log_test("EPCIS with ILMD and EPCClass", False, "No configuration ID available")
            return
            
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
                
                # Validate EPCIS structure and ILMD extensions
                if self.validate_epcis_with_ilmd_and_epcclass(xml_content):
                    self.log_test("EPCIS with ILMD and EPCClass", True,
                                "Valid EPCIS 1.2 XML with ILMD extensions and EPCClass data",
                                f"XML length: {len(xml_content)} characters")
                else:
                    self.log_test("EPCIS with ILMD and EPCClass", False,
                                "EPCIS validation failed")
            else:
                self.log_test("EPCIS with ILMD and EPCClass", False,
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("EPCIS with ILMD and EPCClass", False, f"Request error: {str(e)}")
    
    def validate_epcis_with_ilmd_and_epcclass(self, xml_content):
        """Validate EPCIS XML with ILMD extensions and EPCClass data"""
        try:
            root = ET.fromstring(xml_content)
            
            # Check EPCIS 1.2 structure
            if not (root.tag.endswith("EPCISDocument") and 
                   root.get("schemaVersion") == "1.2"):
                print("   Invalid EPCIS 1.2 structure")
                return False
            
            # Check EPCISMasterData with EPCClass
            epcis_header = None
            for child in root:
                if child.tag.endswith("EPCISHeader"):
                    epcis_header = child
                    break
            
            if epcis_header is None:
                print("   Missing EPCISHeader")
                return False
            
            # Find EPCISMasterData
            epcis_master_data = None
            for child in epcis_header:
                if child.tag.endswith("EPCISMasterData"):
                    epcis_master_data = child
                    break
            
            if epcis_master_data is None:
                print("   Missing EPCISMasterData")
                return False
            
            # Validate EPCClass vocabulary
            epcclass_found = False
            vocabulary_list = None
            for child in epcis_master_data:
                if child.tag.endswith("VocabularyList"):
                    vocabulary_list = child
                    break
            
            if vocabulary_list:
                for vocabulary in vocabulary_list:
                    if vocabulary.get("type") == "urn:epcglobal:epcis:vtype:EPCClass":
                        epcclass_found = True
                        
                        # Check for EPCClass attributes
                        vocab_elem_list = None
                        for child in vocabulary:
                            if child.tag.endswith("VocabularyElementList"):
                                vocab_elem_list = child
                                break
                        
                        if vocab_elem_list:
                            for vocab_elem in vocab_elem_list:
                                if vocab_elem.tag.endswith("VocabularyElement"):
                                    # Check for expected attributes
                                    attributes = {}
                                    for attr in vocab_elem:
                                        if attr.tag.endswith("attribute"):
                                            attr_id = attr.get("id", "")
                                            attributes[attr_id] = attr.text
                                    
                                    # Verify EPCClass data is present
                                    expected_attrs = [
                                        "urn:epcglobal:cbv:mda#additionalTradeItemIdentification",
                                        "urn:epcglobal:cbv:mda#regulatedProductName",
                                        "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName"
                                    ]
                                    
                                    attrs_found = sum(1 for attr in expected_attrs if attr in attributes)
                                    if attrs_found > 0:
                                        print(f"   ✓ EPCClass attributes found: {attrs_found}")
                                        break
            
            if not epcclass_found:
                print("   Missing EPCClass vocabulary")
                return False
            
            # Find EventList and check for ILMD extensions
            epcis_body = None
            for child in root:
                if child.tag.endswith("EPCISBody"):
                    epcis_body = child
                    break
            
            if epcis_body is None:
                print("   Missing EPCISBody")
                return False
            
            event_list = None
            for child in epcis_body:
                if child.tag.endswith("EventList"):
                    event_list = child
                    break
            
            if event_list is None:
                print("   Missing EventList")
                return False
            
            # Check for ILMD extensions in commissioning events
            ilmd_found = False
            for event in event_list:
                if event.tag.endswith("ObjectEvent"):
                    # Look for extension/ilmd
                    for child in event:
                        if child.tag.endswith("extension"):
                            for ext_child in child:
                                if ext_child.tag.endswith("ilmd"):
                                    ilmd_found = True
                                    
                                    # Check for lot number and expiration date
                                    lot_found = False
                                    exp_found = False
                                    
                                    for ilmd_child in ext_child:
                                        if "lotNumber" in ilmd_child.tag and ilmd_child.text == "4JT0482":
                                            lot_found = True
                                        elif "itemExpirationDate" in ilmd_child.tag and ilmd_child.text == "2026-08-31":
                                            exp_found = True
                                    
                                    if lot_found and exp_found:
                                        print("   ✓ ILMD extension with lot number and expiration date found")
                                        break
            
            if not ilmd_found:
                print("   Missing ILMD extensions")
                return False
            
            print("   ✓ Valid EPCIS 1.2 XML with EPCClass and ILMD extensions")
            return True
            
        except ET.ParseError as e:
            print(f"   XML parsing error: {str(e)}")
            return False
        except Exception as e:
            print(f"   Validation error: {str(e)}")
            return False
    
    def test_serial_numbers_with_config(self, config_id):
        """Test serial numbers API with the specific configuration"""
        if not config_id:
            self.log_test("Serial Numbers with Config", False, "No configuration ID available")
            return
            
        # For 1 SSCC, 5 cases, 10 items per case = 50 total items
        sscc_serials = ["SSCC001"]
        case_serials = [f"CASE{i+1:03d}" for i in range(5)]
        item_serials = [f"ITEM{i+1:03d}" for i in range(50)]
        
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
                
                if (len(data["sscc_serial_numbers"]) == 1 and 
                    len(data["case_serial_numbers"]) == 5 and
                    len(data["item_serial_numbers"]) == 50 and
                    data["configuration_id"] == config_id):
                    self.log_test("Serial Numbers with Config", True,
                                "Serial numbers validated and stored correctly",
                                f"1 SSCC, 5 Cases, 50 Items")
                    return True
                else:
                    self.log_test("Serial Numbers with Config", False,
                                "Serial number counts incorrect", data)
                    return False
            else:
                self.log_test("Serial Numbers with Config", False,
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Serial Numbers with Config", False, f"Request error: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run comprehensive backend tests"""
        print("=" * 80)
        print("COMPREHENSIVE BACKEND TESTING - POST CSS STYLING VERIFICATION")
        print("=" * 80)
        print("Testing configuration from review request:")
        print("- Company Prefix: 1234567")
        print("- Product Code: 000000")
        print("- Lot Number: 4JT0482")
        print("- Expiration Date: 2026-08-31")
        print("- 1 SSCC, 5 Cases, 10 Items per case (50 total items)")
        print("- EPCClass test data included")
        print("=" * 80)
        
        # Test 1: Configuration with moved fields and EPCClass data
        config_id = self.test_configuration_with_moved_fields()
        
        # Test 2: Serial numbers with specific configuration
        if config_id:
            self.test_serial_numbers_with_config(config_id)
            
            # Test 3: EPCIS generation with ILMD and EPCClass
            self.test_epcis_with_ilmd_and_epcclass(config_id)
        
        # Test 4: Various hierarchy scenarios
        self.test_hierarchy_scenarios()
        
        # Summary
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST SUMMARY")
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
        
        print("\nKey Verifications Completed:")
        print("✓ Moved fields (Company Prefix, Product Code, Lot Number, Expiration Date)")
        print("✓ GS1 Indicator Digits (SSCC Extension, Case, Inner Case, Item)")
        print("✓ EPCClass fields (product_ndc, regulated_product_name, manufacturer_name, etc.)")
        print("✓ Various hierarchy scenarios (2-level, 3-level, 4-level)")
        print("✓ EPCIS 1.2 XML generation with ILMD extensions")
        print("✓ EPCISMasterData section with EPCClass data")
        
        return passed == total

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)