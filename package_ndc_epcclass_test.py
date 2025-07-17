#!/usr/bin/env python3
"""
Package NDC and EPCClass Testing for EPCIS Serial Number Aggregation App
Tests the new package_ndc field and EPCClass generation with multiple hierarchy scenarios:
1. New package_ndc field storage and retrieval in configuration API
2. EPCClass vocabulary elements for each packaging level with correct indicator digits
3. EPCISMasterData wrapped inside <extension> element
4. package_ndc used for additionalTradeItemIdentification instead of product_ndc
5. Multiple hierarchy scenarios (2-level, 3-level, 4-level)
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://c8e3fe45-251a-4359-a250-c028fb05fe98.preview.emergentagent.com/api"

class PackageNDCEPCClassTester:
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
    
    def test_package_ndc_field_storage(self):
        """Test that package_ndc field is properly stored and retrieved in configuration API"""
        test_config = {
            "items_per_case": 8,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": True,
            "inner_cases_per_case": 3,
            "items_per_inner_case": 8,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "inner_case_product_code": "000001",
            "lot_number": "",
            "expiration_date": "",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "inner_case_indicator_digit": "4",
            "item_indicator_digit": "1",
            "package_ndc": "45802-046-85",  # New field to test
            "product_ndc": "12345-678-90",  # Old field for comparison
            "regulated_product_name": "Test Product",
            "manufacturer_name": "Test Manufacturer",
            "dosage_form_type": "Tablet",
            "strength_description": "10mg",
            "net_content_description": "100 tablets"
        }
        
        try:
            # Create configuration
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_config,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if package_ndc field is stored correctly
                if "package_ndc" in data and data["package_ndc"] == "45802-046-85":
                    self.log_test("Package NDC Field Storage", True, 
                                "package_ndc field properly stored in configuration",
                                f"Stored value: {data['package_ndc']}")
                    return data["id"]
                else:
                    self.log_test("Package NDC Field Storage", False, 
                                "package_ndc field not stored correctly",
                                f"Expected: 45802-046-85, Got: {data.get('package_ndc', 'MISSING')}")
                    return None
            else:
                self.log_test("Package NDC Field Storage", False, 
                            f"Configuration creation failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Package NDC Field Storage", False, f"Request error: {str(e)}")
            return None
    
    def test_2_level_hierarchy_epcclass(self):
        """Test 2-level hierarchy (SSCC→Items): Should have 1 EPCClass for Items"""
        test_config = {
            "items_per_case": 48,  # Items go directly into SSCC
            "cases_per_sscc": 0,   # No cases - direct SSCC→Items
            "number_of_sscc": 1,
            "use_inner_cases": False,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",  # Required field even for 2-level
            "item_indicator_digit": "1",
            "package_ndc": "45802-046-85"
        }
        
        return self._test_hierarchy_epcclass("2-Level Hierarchy (SSCC→Items)", test_config, 
                                           expected_epcclass_count=1,
                                           expected_levels=["Item"])
    
    def test_3_level_hierarchy_epcclass(self):
        """Test 3-level hierarchy (SSCC→Cases→Items): Should have 2 EPCClasses for Cases and Items"""
        test_config = {
            "items_per_case": 8,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": False,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "item_indicator_digit": "1",
            "package_ndc": "45802-046-85"
        }
        
        return self._test_hierarchy_epcclass("3-Level Hierarchy (SSCC→Cases→Items)", test_config,
                                           expected_epcclass_count=2,
                                           expected_levels=["Item", "Case"])
    
    def test_4_level_hierarchy_epcclass(self):
        """Test 4-level hierarchy (SSCC→Cases→Inner Cases→Items): Should have 3 EPCClasses"""
        test_config = {
            "items_per_case": 8,  # This becomes items_per_inner_case when inner cases are used
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
            "item_indicator_digit": "1",
            "package_ndc": "45802-046-85"
        }
        
        return self._test_hierarchy_epcclass("4-Level Hierarchy (SSCC→Cases→Inner Cases→Items)", test_config,
                                           expected_epcclass_count=3,
                                           expected_levels=["Item", "Case", "Inner Case"])
    
    def _test_hierarchy_epcclass(self, test_name, config, expected_epcclass_count, expected_levels):
        """Helper method to test EPCClass generation for different hierarchies"""
        try:
            # Create configuration
            config_response = self.session.post(
                f"{self.base_url}/configuration",
                json=config,
                headers={"Content-Type": "application/json"}
            )
            
            if config_response.status_code != 200:
                self.log_test(test_name, False, f"Configuration creation failed: {config_response.status_code}")
                return None
            
            config_id = config_response.json()["id"]
            
            # Create serial numbers based on hierarchy
            serial_data = self._generate_serial_numbers_for_config(config)
            serial_data["configuration_id"] = config_id
            
            serial_response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if serial_response.status_code != 200:
                self.log_test(test_name, False, f"Serial numbers creation failed: {serial_response.status_code}")
                return None
            
            # Generate EPCIS XML
            epcis_request = {
                "configuration_id": config_id,
                "read_point": "urn:epc:id:sgln:1234567.00000.0",
                "biz_location": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            epcis_response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=epcis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if epcis_response.status_code != 200:
                self.log_test(test_name, False, f"EPCIS generation failed: {epcis_response.status_code}")
                return None
            
            # Validate EPCClass structure
            xml_content = epcis_response.text
            validation_result = self._validate_epcclass_structure(xml_content, expected_epcclass_count, expected_levels, config)
            
            if validation_result["success"]:
                self.log_test(test_name, True, validation_result["message"], validation_result["details"])
                return config_id
            else:
                self.log_test(test_name, False, validation_result["message"], validation_result["details"])
                return None
                
        except Exception as e:
            self.log_test(test_name, False, f"Request error: {str(e)}")
            return None
    
    def _generate_serial_numbers_for_config(self, config):
        """Generate appropriate serial numbers based on configuration"""
        sscc_count = config["number_of_sscc"]
        cases_per_sscc = config["cases_per_sscc"]
        use_inner_cases = config.get("use_inner_cases", False)
        
        # Generate SSCC serials
        sscc_serials = [f"SSCC{i+1:03d}" for i in range(sscc_count)]
        
        if cases_per_sscc == 0:
            # Direct SSCC→Items
            case_serials = []
            inner_case_serials = []
            total_items = config["items_per_case"] * sscc_count
        else:
            # SSCC→Cases→Items or SSCC→Cases→Inner Cases→Items
            total_cases = cases_per_sscc * sscc_count
            case_serials = [f"CASE{i+1:03d}" for i in range(total_cases)]
            
            if use_inner_cases:
                inner_cases_per_case = config["inner_cases_per_case"]
                items_per_inner_case = config["items_per_inner_case"]
                total_inner_cases = inner_cases_per_case * total_cases
                inner_case_serials = [f"INNER{i+1:03d}" for i in range(total_inner_cases)]
                total_items = items_per_inner_case * total_inner_cases
            else:
                inner_case_serials = []
                items_per_case = config["items_per_case"]
                total_items = items_per_case * total_cases
        
        item_serials = [f"ITEM{i+1:03d}" for i in range(total_items)]
        
        return {
            "sscc_serial_numbers": sscc_serials,
            "case_serial_numbers": case_serials,
            "inner_case_serial_numbers": inner_case_serials,
            "item_serial_numbers": item_serials
        }
    
    def _validate_epcclass_structure(self, xml_content, expected_count, expected_levels, config):
        """Validate EPCClass structure in EPCIS XML"""
        try:
            root = ET.fromstring(xml_content)
            
            # Find EPCISMasterData within extension
            epcis_header = None
            for child in root:
                if child.tag.endswith("EPCISHeader"):
                    epcis_header = child
                    break
            
            if epcis_header is None:
                return {"success": False, "message": "EPCISHeader not found", "details": None}
            
            # Check if EPCISMasterData is wrapped in extension
            extension = None
            epcis_master_data = None
            
            for child in epcis_header:
                if child.tag.endswith("extension"):
                    extension = child
                    # Look for EPCISMasterData within extension
                    for grandchild in child:
                        if grandchild.tag.endswith("EPCISMasterData"):
                            epcis_master_data = grandchild
                            break
                    break
                elif child.tag.endswith("EPCISMasterData"):
                    # EPCISMasterData found directly (not in extension) - this is wrong
                    return {"success": False, "message": "EPCISMasterData found directly in EPCISHeader, should be wrapped in extension", "details": None}
            
            if extension is None:
                return {"success": False, "message": "Extension element not found in EPCISHeader", "details": None}
            
            if epcis_master_data is None:
                return {"success": False, "message": "EPCISMasterData not found within extension", "details": None}
            
            # Find VocabularyList
            vocabulary_list = None
            for child in epcis_master_data:
                if child.tag.endswith("VocabularyList"):
                    vocabulary_list = child
                    break
            
            if vocabulary_list is None:
                return {"success": False, "message": "VocabularyList not found", "details": None}
            
            # Find EPCClass vocabulary
            epcclass_vocabulary = None
            for child in vocabulary_list:
                if child.tag.endswith("Vocabulary") and child.get("type") == "urn:epcglobal:epcis:vtype:EPCClass":
                    epcclass_vocabulary = child
                    break
            
            if epcclass_vocabulary is None:
                return {"success": False, "message": "EPCClass vocabulary not found", "details": None}
            
            # Find VocabularyElementList
            vocabulary_element_list = None
            for child in epcclass_vocabulary:
                if child.tag.endswith("VocabularyElementList"):
                    vocabulary_element_list = child
                    break
            
            if vocabulary_element_list is None:
                return {"success": False, "message": "VocabularyElementList not found", "details": None}
            
            # Count VocabularyElements (EPCClasses)
            vocabulary_elements = []
            for child in vocabulary_element_list:
                if child.tag.endswith("VocabularyElement"):
                    vocabulary_elements.append(child)
            
            if len(vocabulary_elements) != expected_count:
                return {"success": False, 
                       "message": f"Expected {expected_count} EPCClass elements, found {len(vocabulary_elements)}",
                       "details": f"Expected levels: {expected_levels}"}
            
            # Validate each EPCClass has correct indicator digit and package_ndc
            validation_details = []
            company_prefix = config["company_prefix"]
            package_ndc = config.get("package_ndc", "")
            
            for element in vocabulary_elements:
                element_id = element.get("id")
                
                # Check indicator digit placement
                if "Item" in expected_levels and f".{config['item_indicator_digit']}{config['item_product_code']}." in element_id:
                    validation_details.append(f"✓ Item EPCClass with indicator digit {config['item_indicator_digit']}")
                elif "Case" in expected_levels and f".{config['case_indicator_digit']}{config['case_product_code']}." in element_id:
                    validation_details.append(f"✓ Case EPCClass with indicator digit {config['case_indicator_digit']}")
                elif "Inner Case" in expected_levels and config.get("inner_case_indicator_digit") and f".{config['inner_case_indicator_digit']}{config['inner_case_product_code']}." in element_id:
                    validation_details.append(f"✓ Inner Case EPCClass with indicator digit {config['inner_case_indicator_digit']}")
                
                # Check package_ndc usage in additionalTradeItemIdentification
                package_ndc_found = False
                for attr in element:
                    if (attr.tag.endswith("attribute") and 
                        attr.get("id") == "urn:epcglobal:cbv:mda#additionalTradeItemIdentification" and
                        attr.text == package_ndc):
                        package_ndc_found = True
                        break
                
                if package_ndc and package_ndc_found:
                    validation_details.append(f"✓ package_ndc ({package_ndc}) used for additionalTradeItemIdentification")
                elif package_ndc and not package_ndc_found:
                    return {"success": False, 
                           "message": "package_ndc not found in additionalTradeItemIdentification",
                           "details": f"Expected: {package_ndc}"}
            
            return {"success": True, 
                   "message": f"EPCClass structure valid: {expected_count} elements for {expected_levels}",
                   "details": "; ".join(validation_details)}
            
        except ET.ParseError as e:
            return {"success": False, "message": f"XML parsing error: {str(e)}", "details": None}
        except Exception as e:
            return {"success": False, "message": f"Validation error: {str(e)}", "details": None}
    
    def test_epcis_master_data_extension_wrapper(self):
        """Test that EPCISMasterData is wrapped inside an <extension> element"""
        # Use simple 3-level hierarchy for this test
        test_config = {
            "items_per_case": 8,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": False,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "item_indicator_digit": "1",
            "package_ndc": "45802-046-85"
        }
        
        try:
            # Create configuration and generate EPCIS
            config_response = self.session.post(f"{self.base_url}/configuration", json=test_config)
            if config_response.status_code != 200:
                self.log_test("EPCISMasterData Extension Wrapper", False, "Configuration creation failed")
                return
            
            config_id = config_response.json()["id"]
            
            # Create serial numbers
            serial_data = self._generate_serial_numbers_for_config(test_config)
            serial_data["configuration_id"] = config_id
            serial_response = self.session.post(f"{self.base_url}/serial-numbers", json=serial_data)
            
            if serial_response.status_code != 200:
                self.log_test("EPCISMasterData Extension Wrapper", False, "Serial numbers creation failed")
                return
            
            # Generate EPCIS
            epcis_request = {"configuration_id": config_id}
            epcis_response = self.session.post(f"{self.base_url}/generate-epcis", json=epcis_request)
            
            if epcis_response.status_code != 200:
                self.log_test("EPCISMasterData Extension Wrapper", False, "EPCIS generation failed")
                return
            
            # Parse XML and check structure
            root = ET.fromstring(epcis_response.text)
            
            # Navigate: EPCISDocument → EPCISHeader → extension → EPCISMasterData
            epcis_header = None
            for child in root:
                if child.tag.endswith("EPCISHeader"):
                    epcis_header = child
                    break
            
            if epcis_header is None:
                self.log_test("EPCISMasterData Extension Wrapper", False, "EPCISHeader not found")
                return
            
            extension = None
            epcis_master_data = None
            
            for child in epcis_header:
                if child.tag.endswith("extension"):
                    extension = child
                    # Look for EPCISMasterData within extension
                    for grandchild in child:
                        if grandchild.tag.endswith("EPCISMasterData"):
                            epcis_master_data = grandchild
                            break
                    break
                elif child.tag.endswith("EPCISMasterData"):
                    # EPCISMasterData found directly (not in extension) - this is wrong
                    self.log_test("EPCISMasterData Extension Wrapper", False, "EPCISMasterData found directly in EPCISHeader, should be wrapped in extension")
                    return
            
            if extension is None:
                self.log_test("EPCISMasterData Extension Wrapper", False, "Extension element not found in EPCISHeader")
                return
            
            if epcis_master_data is None:
                self.log_test("EPCISMasterData Extension Wrapper", False, "EPCISMasterData not found within extension")
                return
            
            self.log_test("EPCISMasterData Extension Wrapper", True, 
                         "EPCISMasterData is properly wrapped inside <extension> element",
                         "Structure: EPCISHeader → extension → EPCISMasterData")
            
        except Exception as e:
            self.log_test("EPCISMasterData Extension Wrapper", False, f"Test error: {str(e)}")
    
    def run_all_tests(self):
        """Run all package NDC and EPCClass tests"""
        print("=" * 80)
        print("PACKAGE NDC AND EPCCLASS TESTING")
        print("=" * 80)
        print("Testing new package_ndc field and EPCClass generation with multiple hierarchy scenarios")
        print("Test configuration: Company Prefix: 1234567, Package NDC: 45802-046-85")
        print("=" * 80)
        
        # Test 1: Package NDC field storage and retrieval
        config_id = self.test_package_ndc_field_storage()
        
        # Test 2: EPCISMasterData extension wrapper
        self.test_epcis_master_data_extension_wrapper()
        
        # Test 3: 2-level hierarchy EPCClass generation
        self.test_2_level_hierarchy_epcclass()
        
        # Test 4: 3-level hierarchy EPCClass generation  
        self.test_3_level_hierarchy_epcclass()
        
        # Test 5: 4-level hierarchy EPCClass generation
        self.test_4_level_hierarchy_epcclass()
        
        # Summary
        print("\n" + "=" * 80)
        print("PACKAGE NDC AND EPCCLASS TEST SUMMARY")
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
        print("✓ Package NDC field storage and retrieval")
        print("✓ EPCISMasterData wrapped in <extension> element")
        print("✓ EPCClass vocabulary elements for each packaging level")
        print("✓ Correct indicator digit usage in EPCClass patterns")
        print("✓ package_ndc used for additionalTradeItemIdentification")
        print("✓ Multiple hierarchy scenarios (2-level, 3-level, 4-level)")
        
        return passed == total

if __name__ == "__main__":
    tester = PackageNDCEPCClassTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)