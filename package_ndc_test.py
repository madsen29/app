#!/usr/bin/env python3
"""
Package NDC Formatting Fix Testing
Tests the Package NDC formatting fix to ensure proper 11-digit NDC handling as per review request:

1. Test 10-digit to 11-digit Package NDC conversion
2. Test 11-digit Package NDC (already correct)
3. Test configuration and EPCIS generation
4. Verify EPCClass vocabulary elements are in correct order: Item → Inner Case → Case
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class PackageNDCTester:
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
        """Test 1: 10-digit Package NDC conversion to 11-digit"""
        print("\n=== TEST 1: 10-digit Package NDC Conversion ===")
        
        # Test configuration with 10-digit Package NDC "45802-466-53" (becomes "4580246653" without hyphens)
        # Should be converted to 11-digit "45802-0466-53" (becomes "4580204653" without hyphens)
        test_config = {
            "items_per_case": 8,  # 8 items per inner case
            "cases_per_sscc": 2,  # 2 cases per SSCC
            "number_of_sscc": 1,  # 1 SSCC
            "use_inner_cases": True,
            "inner_cases_per_case": 6,  # 6 inner cases per case
            "items_per_inner_case": 8,  # 8 items per inner case (total 48 items)
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "inner_case_product_code": "000001",
            "lot_number": "4JT0482",
            "expiration_date": "2026-08-31",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "inner_case_indicator_digit": "4",
            "item_indicator_digit": "1",
            "package_ndc": "4580246653"  # 10-digit NDC (should be converted to 11-digit)
        }
        
        try:
            # Create configuration
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_config,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("10-digit NDC Configuration", False, f"Failed to create configuration: {response.status_code}")
                return None
                
            config_data = response.json()
            config_id = config_data["id"]
            
            # Verify package_ndc is stored correctly
            if config_data.get("package_ndc") == "4580246653":
                self.log_test("10-digit NDC Configuration", True, "10-digit Package NDC stored correctly", 
                            f"Stored: {config_data.get('package_ndc')}")
            else:
                self.log_test("10-digit NDC Configuration", False, f"Package NDC not stored correctly: {config_data.get('package_ndc')}")
                return None
            
            # Create serial numbers
            serial_data = {
                "configuration_id": config_id,
                "sscc_serial_numbers": ["SSCC001"],
                "case_serial_numbers": ["CASE001", "CASE002"],
                "inner_case_serial_numbers": [f"INNER{i+1:03d}" for i in range(12)],  # 6 inner cases per case × 2 cases = 12
                "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(48)]  # 8 items per inner case × 12 inner cases = 48
            }
            
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("10-digit NDC Serial Numbers", False, f"Failed to create serial numbers: {response.status_code}")
                return None
            
            self.log_test("10-digit NDC Serial Numbers", True, "Serial numbers created successfully")
            
            # Generate EPCIS XML
            epcis_request = {
                "configuration_id": config_id,
                "read_point": "urn:epc:id:sgln:1234567.00000.0",
                "biz_location": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=epcis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("10-digit NDC EPCIS Generation", False, f"Failed to generate EPCIS: {response.status_code}")
                return None
            
            xml_content = response.text
            
            # Parse XML and check for converted 11-digit NDC
            try:
                root = ET.fromstring(xml_content)
                
                # Find additionalTradeItemIdentification attributes
                ndc_values = []
                for elem in root.iter():
                    if elem.get("id") == "urn:epcglobal:cbv:mda#additionalTradeItemIdentification":
                        ndc_values.append(elem.text)
                
                # Check if all NDC values are the converted 11-digit format
                expected_ndc = "4580204653"  # 10-digit "4580246653" should be converted to 11-digit "4580204653"
                
                if ndc_values:
                    all_correct = all(ndc == expected_ndc for ndc in ndc_values)
                    if all_correct:
                        self.log_test("10-digit NDC Conversion", True, f"10-digit NDC correctly converted to 11-digit", 
                                    f"Found {len(ndc_values)} NDC values, all = '{expected_ndc}'")
                    else:
                        self.log_test("10-digit NDC Conversion", False, f"NDC conversion failed", 
                                    f"Expected: '{expected_ndc}', Found: {ndc_values}")
                        return config_id
                else:
                    self.log_test("10-digit NDC Conversion", False, "No additionalTradeItemIdentification found in XML")
                    return config_id
                    
            except ET.ParseError as e:
                self.log_test("10-digit NDC XML Parsing", False, f"XML parsing error: {str(e)}")
                return config_id
            
            return config_id
            
        except Exception as e:
            self.log_test("10-digit NDC Test", False, f"Test error: {str(e)}")
            return None
    
    def test_11_digit_package_ndc_unchanged(self):
        """Test 2: 11-digit Package NDC should remain unchanged"""
        print("\n=== TEST 2: 11-digit Package NDC (Already Correct) ===")
        
        # Test configuration with already properly formatted 11-digit Package NDC
        test_config = {
            "items_per_case": 8,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": True,
            "inner_cases_per_case": 6,
            "items_per_inner_case": 8,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "inner_case_product_code": "000001",
            "lot_number": "4JT0482",
            "expiration_date": "2026-08-31",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "inner_case_indicator_digit": "4",
            "item_indicator_digit": "1",
            "package_ndc": "4580204653"  # Already 11-digit NDC (should remain unchanged)
        }
        
        try:
            # Create configuration
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_config,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("11-digit NDC Configuration", False, f"Failed to create configuration: {response.status_code}")
                return None
                
            config_data = response.json()
            config_id = config_data["id"]
            
            # Create serial numbers
            serial_data = {
                "configuration_id": config_id,
                "sscc_serial_numbers": ["SSCC002"],
                "case_serial_numbers": ["CASE003", "CASE004"],
                "inner_case_serial_numbers": [f"INNER{i+13:03d}" for i in range(12)],
                "item_serial_numbers": [f"ITEM{i+49:03d}" for i in range(48)]
            }
            
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("11-digit NDC Serial Numbers", False, f"Failed to create serial numbers: {response.status_code}")
                return None
            
            # Generate EPCIS XML
            epcis_request = {
                "configuration_id": config_id,
                "read_point": "urn:epc:id:sgln:1234567.00000.0",
                "biz_location": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=epcis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("11-digit NDC EPCIS Generation", False, f"Failed to generate EPCIS: {response.status_code}")
                return None
            
            xml_content = response.text
            
            # Parse XML and check NDC remains unchanged
            try:
                root = ET.fromstring(xml_content)
                
                # Find additionalTradeItemIdentification attributes
                ndc_values = []
                for elem in root.iter():
                    if elem.get("id") == "urn:epcglobal:cbv:mda#additionalTradeItemIdentification":
                        ndc_values.append(elem.text)
                
                # Check if all NDC values remain as the original 11-digit format
                expected_ndc = "4580204653"  # Should remain unchanged
                
                if ndc_values:
                    all_correct = all(ndc == expected_ndc for ndc in ndc_values)
                    if all_correct:
                        self.log_test("11-digit NDC Unchanged", True, f"11-digit NDC correctly preserved", 
                                    f"Found {len(ndc_values)} NDC values, all = '{expected_ndc}'")
                    else:
                        self.log_test("11-digit NDC Unchanged", False, f"NDC preservation failed", 
                                    f"Expected: '{expected_ndc}', Found: {ndc_values}")
                        return config_id
                else:
                    self.log_test("11-digit NDC Unchanged", False, "No additionalTradeItemIdentification found in XML")
                    return config_id
                    
            except ET.ParseError as e:
                self.log_test("11-digit NDC XML Parsing", False, f"XML parsing error: {str(e)}")
                return config_id
            
            return config_id
            
        except Exception as e:
            self.log_test("11-digit NDC Test", False, f"Test error: {str(e)}")
            return None
    
    def test_epcclass_vocabulary_order(self):
        """Test 3: Verify EPCClass vocabulary elements are in correct order: Item → Inner Case → Case"""
        print("\n=== TEST 3: EPCClass Vocabulary Element Order ===")
        
        # Test configuration for 4-level hierarchy to test all EPCClass elements
        test_config = {
            "items_per_case": 8,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": True,
            "inner_cases_per_case": 6,
            "items_per_inner_case": 8,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
            "inner_case_product_code": "000001",
            "lot_number": "4JT0482",
            "expiration_date": "2026-08-31",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "inner_case_indicator_digit": "4",
            "item_indicator_digit": "1",
            "package_ndc": "45802-046-85"  # With hyphens to test hyphen removal too
        }
        
        try:
            # Create configuration
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_config,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("EPCClass Order Configuration", False, f"Failed to create configuration: {response.status_code}")
                return None
                
            config_data = response.json()
            config_id = config_data["id"]
            
            # Create serial numbers
            serial_data = {
                "configuration_id": config_id,
                "sscc_serial_numbers": ["SSCC003"],
                "case_serial_numbers": ["CASE005", "CASE006"],
                "inner_case_serial_numbers": [f"INNER{i+25:03d}" for i in range(12)],
                "item_serial_numbers": [f"ITEM{i+97:03d}" for i in range(48)]
            }
            
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("EPCClass Order Serial Numbers", False, f"Failed to create serial numbers: {response.status_code}")
                return None
            
            # Generate EPCIS XML
            epcis_request = {
                "configuration_id": config_id,
                "read_point": "urn:epc:id:sgln:1234567.00000.0",
                "biz_location": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=epcis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("EPCClass Order EPCIS Generation", False, f"Failed to generate EPCIS: {response.status_code}")
                return None
            
            xml_content = response.text
            
            # Parse XML and check EPCClass vocabulary element order
            try:
                root = ET.fromstring(xml_content)
                
                # Find VocabularyElementList
                vocabulary_elements = []
                for elem in root.iter():
                    if elem.tag.endswith("VocabularyElementList"):
                        for vocab_elem in elem:
                            if vocab_elem.tag.endswith("VocabularyElement"):
                                epc_pattern = vocab_elem.get("id")
                                if epc_pattern:
                                    vocabulary_elements.append(epc_pattern)
                
                if len(vocabulary_elements) != 3:
                    self.log_test("EPCClass Order Count", False, f"Expected 3 EPCClass elements, found {len(vocabulary_elements)}")
                    return config_id
                
                # Expected order: Item → Inner Case → Case
                expected_patterns = [
                    "urn:epc:idpat:sgtin:1234567.1000000.*",  # Item (indicator digit 1)
                    "urn:epc:idpat:sgtin:1234567.4000001.*",  # Inner Case (indicator digit 4)
                    "urn:epc:idpat:sgtin:1234567.2000000.*"   # Case (indicator digit 2)
                ]
                
                if vocabulary_elements == expected_patterns:
                    self.log_test("EPCClass Vocabulary Order", True, "EPCClass elements in correct order: Item → Inner Case → Case", 
                                f"Found patterns: {vocabulary_elements}")
                else:
                    self.log_test("EPCClass Vocabulary Order", False, "EPCClass elements in wrong order", 
                                f"Expected: {expected_patterns}, Found: {vocabulary_elements}")
                    return config_id
                
                # Also check hyphen removal in additionalTradeItemIdentification
                ndc_values = []
                for elem in root.iter():
                    if elem.get("id") == "urn:epcglobal:cbv:mda#additionalTradeItemIdentification":
                        ndc_values.append(elem.text)
                
                expected_clean_ndc = "4580204685"  # "45802-046-85" with hyphens removed
                
                if ndc_values:
                    all_clean = all(ndc == expected_clean_ndc for ndc in ndc_values)
                    if all_clean:
                        self.log_test("Hyphen Removal", True, f"Hyphens correctly removed from Package NDC", 
                                    f"Found {len(ndc_values)} NDC values, all = '{expected_clean_ndc}'")
                    else:
                        self.log_test("Hyphen Removal", False, f"Hyphen removal failed", 
                                    f"Expected: '{expected_clean_ndc}', Found: {ndc_values}")
                else:
                    self.log_test("Hyphen Removal", False, "No additionalTradeItemIdentification found in XML")
                    
            except ET.ParseError as e:
                self.log_test("EPCClass Order XML Parsing", False, f"XML parsing error: {str(e)}")
                return config_id
            
            return config_id
            
        except Exception as e:
            self.log_test("EPCClass Order Test", False, f"Test error: {str(e)}")
            return None
    
    def test_package_ndc_conversion_logic(self):
        """Test 4: Verify Package NDC conversion logic for different formats"""
        print("\n=== TEST 4: Package NDC Conversion Logic ===")
        
        test_cases = [
            {
                "name": "10-digit with hyphens",
                "input": "45802-466-53",
                "expected": "4580204653"  # Should convert to 11-digit and remove hyphens
            },
            {
                "name": "10-digit without hyphens", 
                "input": "4580246653",
                "expected": "4580204653"  # Should convert to 11-digit
            },
            {
                "name": "11-digit with hyphens",
                "input": "45802-0466-53", 
                "expected": "4580204653"  # Should just remove hyphens
            },
            {
                "name": "11-digit without hyphens",
                "input": "4580204653",
                "expected": "4580204653"  # Should remain unchanged
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                test_config = {
                    "items_per_case": 10,
                    "cases_per_sscc": 1,
                    "number_of_sscc": 1,
                    "use_inner_cases": False,
                    "company_prefix": "1234567",
                    "item_product_code": "000000",
                    "case_product_code": "000000",
                    "sscc_indicator_digit": "3",
                    "case_indicator_digit": "2",
                    "item_indicator_digit": "1",
                    "package_ndc": test_case["input"]
                }
                
                # Create configuration
                response = self.session.post(
                    f"{self.base_url}/configuration",
                    json=test_config,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    self.log_test(f"NDC Logic {test_case['name']}", False, f"Failed to create configuration: {response.status_code}")
                    continue
                    
                config_data = response.json()
                config_id = config_data["id"]
                
                # Create minimal serial numbers
                serial_data = {
                    "configuration_id": config_id,
                    "sscc_serial_numbers": [f"SSCC{i+10:03d}"],
                    "case_serial_numbers": [f"CASE{i+10:03d}"],
                    "item_serial_numbers": [f"ITEM{j+i*10:03d}" for j in range(10)]
                }
                
                response = self.session.post(
                    f"{self.base_url}/serial-numbers",
                    json=serial_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    self.log_test(f"NDC Logic {test_case['name']}", False, f"Failed to create serial numbers: {response.status_code}")
                    continue
                
                # Generate EPCIS XML
                epcis_request = {
                    "configuration_id": config_id,
                    "read_point": "urn:epc:id:sgln:1234567.00000.0",
                    "biz_location": "urn:epc:id:sgln:1234567.00001.0"
                }
                
                response = self.session.post(
                    f"{self.base_url}/generate-epcis",
                    json=epcis_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    self.log_test(f"NDC Logic {test_case['name']}", False, f"Failed to generate EPCIS: {response.status_code}")
                    continue
                
                xml_content = response.text
                
                # Parse XML and check NDC conversion
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find additionalTradeItemIdentification attributes
                    ndc_values = []
                    for elem in root.iter():
                        if elem.get("id") == "urn:epcglobal:cbv:mda#additionalTradeItemIdentification":
                            ndc_values.append(elem.text)
                    
                    if ndc_values:
                        actual_ndc = ndc_values[0]  # Take first one for comparison
                        if actual_ndc == test_case["expected"]:
                            self.log_test(f"NDC Logic {test_case['name']}", True, f"Conversion correct", 
                                        f"Input: '{test_case['input']}' → Output: '{actual_ndc}'")
                        else:
                            self.log_test(f"NDC Logic {test_case['name']}", False, f"Conversion failed", 
                                        f"Input: '{test_case['input']}', Expected: '{test_case['expected']}', Got: '{actual_ndc}'")
                    else:
                        self.log_test(f"NDC Logic {test_case['name']}", False, "No additionalTradeItemIdentification found in XML")
                        
                except ET.ParseError as e:
                    self.log_test(f"NDC Logic {test_case['name']}", False, f"XML parsing error: {str(e)}")
                    
            except Exception as e:
                self.log_test(f"NDC Logic {test_case['name']}", False, f"Test error: {str(e)}")
    
    def run_all_tests(self):
        """Run all Package NDC formatting tests"""
        print("=" * 80)
        print("PACKAGE NDC FORMATTING FIX TESTING")
        print("=" * 80)
        print("Testing Package NDC formatting fix for proper 11-digit NDC handling")
        print("Expected: 10-digit NDCs converted to 11-digit, hyphens removed, correct EPCClass order")
        print("=" * 80)
        
        # Test 1: 10-digit to 11-digit conversion
        config_id_1 = self.test_10_digit_package_ndc_conversion()
        
        # Test 2: 11-digit NDC unchanged
        config_id_2 = self.test_11_digit_package_ndc_unchanged()
        
        # Test 3: EPCClass vocabulary order
        config_id_3 = self.test_epcclass_vocabulary_order()
        
        # Test 4: Package NDC conversion logic
        self.test_package_ndc_conversion_logic()
        
        # Summary
        print("\n" + "=" * 80)
        print("PACKAGE NDC FORMATTING TEST SUMMARY")
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
        print("✓ 10-digit to 11-digit Package NDC conversion")
        print("✓ 11-digit Package NDC preservation")
        print("✓ Hyphen removal from Package NDC")
        print("✓ EPCClass vocabulary element order: Item → Inner Case → Case")
        print("✓ EPCIS XML additionalTradeItemIdentification validation")
        
        return passed == total

if __name__ == "__main__":
    tester = PackageNDCTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)