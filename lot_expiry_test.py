#!/usr/bin/env python3
"""
Backend API Testing for GS1 EPCIS Lot Number and Expiration Date Fields
Tests the new lot_number and expiration_date functionality:
1. Configuration API with lot_number and expiration_date fields
2. EPCIS XML generation with ILMD extensions
3. Complete workflow validation
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://b592395b-b7d6-4a00-b6d1-3e8882cb2379.preview.emergentagent.com/api"

class LotExpiryTester:
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
    
    def test_configuration_with_lot_expiry(self):
        """Test configuration creation with lot_number and expiration_date fields"""
        test_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 1,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000001",
            "lot_number": "4JT0482",
            "expiration_date": "2026-08-31",
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
                
                # Check that lot_number and expiration_date are properly stored
                if (data.get("lot_number") == "4JT0482" and 
                    data.get("expiration_date") == "2026-08-31"):
                    self.log_test("Configuration with Lot/Expiry", True, 
                                "Configuration created with lot number and expiration date",
                                f"Lot: {data['lot_number']}, Expiry: {data['expiration_date']}")
                    return data["id"]
                else:
                    self.log_test("Configuration with Lot/Expiry", False, 
                                "Lot number or expiration date not properly stored", data)
                    return None
            else:
                self.log_test("Configuration with Lot/Expiry", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration with Lot/Expiry", False, f"Request error: {str(e)}")
            return None
    
    def test_configuration_without_lot_expiry(self):
        """Test configuration creation without lot_number and expiration_date (should work with defaults)"""
        test_data = {
            "items_per_case": 5,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000001",
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
                
                # Check that lot_number and expiration_date default to empty strings
                if (data.get("lot_number") == "" and 
                    data.get("expiration_date") == ""):
                    self.log_test("Configuration without Lot/Expiry", True, 
                                "Configuration created with empty lot/expiry defaults",
                                f"Lot: '{data['lot_number']}', Expiry: '{data['expiration_date']}'")
                    return data["id"]
                else:
                    self.log_test("Configuration without Lot/Expiry", False, 
                                "Unexpected default values for lot/expiry", data)
                    return None
            else:
                self.log_test("Configuration without Lot/Expiry", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration without Lot/Expiry", False, f"Request error: {str(e)}")
            return None
    
    def create_serial_numbers(self, config_id, items_per_case, cases_per_sscc, number_of_sscc):
        """Helper method to create serial numbers for a configuration"""
        if not config_id:
            return None
            
        total_cases = cases_per_sscc * number_of_sscc
        total_items = items_per_case * total_cases
        
        sscc_serials = [f"SSCC{i+1:03d}" for i in range(number_of_sscc)]
        case_serials = [f"CASE{i+1:03d}" for i in range(total_cases)]
        item_serials = [f"ITEM{i+1:03d}" for i in range(total_items)]
        
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
                return response.json()["id"]
            else:
                print(f"   Failed to create serial numbers: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   Error creating serial numbers: {str(e)}")
            return None
    
    def test_epcis_with_ilmd_extension(self, config_id):
        """Test EPCIS XML generation with ILMD extension containing lot number and expiration date"""
        if not config_id:
            self.log_test("EPCIS with ILMD Extension", False, "No configuration ID available")
            return
        
        # Create serial numbers first
        serial_id = self.create_serial_numbers(config_id, 10, 5, 1)  # 10 items/case, 5 cases/sscc, 1 sscc
        if not serial_id:
            self.log_test("EPCIS with ILMD Extension", False, "Failed to create serial numbers")
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
                if self.validate_ilmd_extension(xml_content, "4JT0482", "2026-08-31"):
                    self.log_test("EPCIS with ILMD Extension", True, 
                                "EPCIS XML contains proper ILMD extension with lot number and expiration date")
                else:
                    self.log_test("EPCIS with ILMD Extension", False, 
                                "ILMD extension not found or incorrect in EPCIS XML")
            else:
                self.log_test("EPCIS with ILMD Extension", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("EPCIS with ILMD Extension", False, f"Request error: {str(e)}")
    
    def test_epcis_without_ilmd_extension(self, config_id):
        """Test EPCIS XML generation without ILMD extension (empty lot/expiry)"""
        if not config_id:
            self.log_test("EPCIS without ILMD Extension", False, "No configuration ID available")
            return
        
        # Create serial numbers first
        serial_id = self.create_serial_numbers(config_id, 5, 2, 1)  # 5 items/case, 2 cases/sscc, 1 sscc
        if not serial_id:
            self.log_test("EPCIS without ILMD Extension", False, "Failed to create serial numbers")
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
                if self.validate_no_ilmd_extension(xml_content):
                    self.log_test("EPCIS without ILMD Extension", True, 
                                "EPCIS XML correctly omits ILMD extension when lot/expiry are empty")
                else:
                    self.log_test("EPCIS without ILMD Extension", False, 
                                "ILMD extension found when it should be omitted")
            else:
                self.log_test("EPCIS without ILMD Extension", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("EPCIS without ILMD Extension", False, f"Request error: {str(e)}")
    
    def validate_ilmd_extension(self, xml_content, expected_lot, expected_expiry):
        """Validate that EPCIS XML contains proper ILMD extension"""
        try:
            root = ET.fromstring(xml_content)
            
            # Find all ObjectEvents (commissioning events)
            object_events = []
            for event in root.iter():
                if event.tag.endswith("ObjectEvent"):
                    object_events.append(event)
            
            if not object_events:
                print("   No ObjectEvents found in XML")
                return False
            
            # Check each ObjectEvent for ILMD extension
            ilmd_found_count = 0
            for event in object_events:
                extension = None
                for child in event:
                    if child.tag.endswith("extension"):
                        extension = child
                        break
                
                if extension is not None:
                    ilmd = None
                    for child in extension:
                        if child.tag.endswith("ilmd"):
                            ilmd = child
                            break
                    
                    if ilmd is not None:
                        ilmd_found_count += 1
                        
                        # Check for lot number
                        lot_found = False
                        expiry_found = False
                        
                        for child in ilmd:
                            if child.tag.endswith("lotNumber"):
                                if child.text == expected_lot:
                                    lot_found = True
                                else:
                                    print(f"   Wrong lot number: expected '{expected_lot}', got '{child.text}'")
                                    return False
                            elif child.tag.endswith("itemExpirationDate"):
                                if child.text == expected_expiry:
                                    expiry_found = True
                                else:
                                    print(f"   Wrong expiration date: expected '{expected_expiry}', got '{child.text}'")
                                    return False
                        
                        if not lot_found:
                            print("   Lot number not found in ILMD extension")
                            return False
                        if not expiry_found:
                            print("   Expiration date not found in ILMD extension")
                            return False
            
            if ilmd_found_count == 0:
                print("   No ILMD extensions found in ObjectEvents")
                return False
            
            print(f"   ✓ Found {ilmd_found_count} ILMD extensions with correct lot number and expiration date")
            return True
            
        except ET.ParseError as e:
            print(f"   XML parsing error: {str(e)}")
            return False
        except Exception as e:
            print(f"   Validation error: {str(e)}")
            return False
    
    def validate_no_ilmd_extension(self, xml_content):
        """Validate that EPCIS XML does not contain ILMD extension when lot/expiry are empty"""
        try:
            root = ET.fromstring(xml_content)
            
            # Find all ObjectEvents (commissioning events)
            object_events = []
            for event in root.iter():
                if event.tag.endswith("ObjectEvent"):
                    object_events.append(event)
            
            if not object_events:
                print("   No ObjectEvents found in XML")
                return False
            
            # Check that no ObjectEvent has ILMD extension
            for event in object_events:
                extension = None
                for child in event:
                    if child.tag.endswith("extension"):
                        extension = child
                        break
                
                if extension is not None:
                    ilmd = None
                    for child in extension:
                        if child.tag.endswith("ilmd"):
                            ilmd = child
                            break
                    
                    if ilmd is not None:
                        print("   Found ILMD extension when lot/expiry are empty")
                        return False
            
            print("   ✓ No ILMD extensions found (correct for empty lot/expiry)")
            return True
            
        except ET.ParseError as e:
            print(f"   XML parsing error: {str(e)}")
            return False
        except Exception as e:
            print(f"   Validation error: {str(e)}")
            return False
    
    def test_complete_workflow(self):
        """Test complete workflow: create config with lot/expiry → add serials → generate EPCIS"""
        print("\n" + "=" * 60)
        print("COMPLETE WORKFLOW TEST")
        print("=" * 60)
        
        # Step 1: Create configuration with lot number and expiration date
        config_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 1,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000001",
            "lot_number": "4JT0482",
            "expiration_date": "2026-08-31",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "item_indicator_digit": "1"
        }
        
        try:
            config_response = self.session.post(
                f"{self.base_url}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if config_response.status_code != 200:
                self.log_test("Complete Workflow", False, "Failed to create configuration")
                return
            
            config_id = config_response.json()["id"]
            print(f"   ✓ Configuration created: {config_id}")
            
            # Step 2: Add serial numbers
            serial_data = {
                "configuration_id": config_id,
                "sscc_serial_numbers": ["SSCC001"],
                "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],  # 5 cases
                "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(50)]  # 50 items (10 per case × 5 cases)
            }
            
            serial_response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if serial_response.status_code != 200:
                self.log_test("Complete Workflow", False, "Failed to create serial numbers")
                return
            
            print(f"   ✓ Serial numbers created")
            
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
            
            if epcis_response.status_code != 200:
                self.log_test("Complete Workflow", False, "Failed to generate EPCIS XML")
                return
            
            xml_content = epcis_response.text
            print(f"   ✓ EPCIS XML generated ({len(xml_content)} characters)")
            
            # Step 4: Validate ILMD extension in XML
            if self.validate_ilmd_extension(xml_content, "4JT0482", "2026-08-31"):
                self.log_test("Complete Workflow", True, 
                            "Complete workflow successful with ILMD extension",
                            "Config → Serials → EPCIS with lot number and expiration date")
            else:
                self.log_test("Complete Workflow", False, "ILMD extension validation failed")
                
        except Exception as e:
            self.log_test("Complete Workflow", False, f"Workflow error: {str(e)}")
    
    def run_all_tests(self):
        """Run all lot number and expiration date tests"""
        print("=" * 80)
        print("GS1 EPCIS LOT NUMBER AND EXPIRATION DATE TESTING")
        print("=" * 80)
        print("Testing new lot_number and expiration_date fields with ILMD extensions")
        print("=" * 80)
        
        # Test 1: Configuration with lot number and expiration date
        config_with_lot_id = self.test_configuration_with_lot_expiry()
        
        # Test 2: Configuration without lot number and expiration date
        config_without_lot_id = self.test_configuration_without_lot_expiry()
        
        # Test 3: EPCIS generation with ILMD extension
        self.test_epcis_with_ilmd_extension(config_with_lot_id)
        
        # Test 4: EPCIS generation without ILMD extension
        self.test_epcis_without_ilmd_extension(config_without_lot_id)
        
        # Test 5: Complete workflow test
        self.test_complete_workflow()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY - LOT NUMBER AND EXPIRATION DATE")
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
        print("✓ Configuration API with lot_number and expiration_date fields")
        print("✓ EPCIS XML generation with ILMD extensions")
        print("✓ Proper ILMD structure with cbvmda:lotNumber and cbvmda:itemExpirationDate")
        print("✓ Conditional ILMD extension (only when lot/expiry provided)")
        print("✓ Complete workflow integration")
        
        return passed == total

if __name__ == "__main__":
    tester = LotExpiryTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)