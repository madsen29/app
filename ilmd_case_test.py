#!/usr/bin/env python3
"""
ILMD Extension Testing for Case Commissioning Events
Tests specifically for the Case commissioning event ILMD extension as requested in the review.

Test Configuration:
- Company Prefix: "1234567"
- Product Code: "000000"
- Lot Number: "4JT0482"
- Expiration Date: "2026-08-31"
- Hierarchy: 1 SSCC → 5 Cases → 10 Items per case (50 total items)
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class ILMDCaseTester:
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
    
    def create_test_configuration(self):
        """Create configuration with lot number and expiration date as specified in review request"""
        test_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5,
            "number_of_sscc": 1,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000000",
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
                self.log_test("Configuration Creation", True, 
                            f"Configuration created with lot_number='{data.get('lot_number')}' and expiration_date='{data.get('expiration_date')}'")
                return data["id"]
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration Creation", False, f"Request error: {str(e)}")
            return None
    
    def create_test_serial_numbers(self, config_id):
        """Create serial numbers for the test configuration"""
        if not config_id:
            return None
            
        # 1 SSCC, 5 cases, 50 items (10 per case)
        test_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": ["SSCC001"],
            "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],
            "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(50)]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Serial Numbers Creation", True, 
                            f"Serial numbers created: 1 SSCC, 5 cases, 50 items")
                return data["id"]
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return None
    
    def generate_and_test_epcis_xml(self, config_id):
        """Generate EPCIS XML and test for ILMD extensions in Case commissioning events"""
        if not config_id:
            return None
            
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
                self.log_test("EPCIS Generation", True, f"EPCIS XML generated successfully")
                return xml_content
            else:
                self.log_test("EPCIS Generation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("EPCIS Generation", False, f"Request error: {str(e)}")
            return None
    
    def test_case_commissioning_ilmd_extension(self, xml_content):
        """Test that Case commissioning event contains ILMD extension"""
        if not xml_content:
            self.log_test("Case ILMD Extension Test", False, "No XML content to test")
            return False
            
        try:
            root = ET.fromstring(xml_content)
            
            # Find all ObjectEvents (commissioning events)
            object_events = []
            for event in root.iter():
                if event.tag.endswith("ObjectEvent"):
                    object_events.append(event)
            
            if len(object_events) < 3:
                self.log_test("Case ILMD Extension Test", False, 
                            f"Expected at least 3 ObjectEvents (Items, Cases, SSCCs), found {len(object_events)}")
                return False
            
            # Find the Case commissioning event
            case_commissioning_event = None
            for event in object_events:
                # Check if this event contains case EPCs
                epc_list = None
                for child in event:
                    if child.tag.endswith("epcList"):
                        epc_list = child
                        break
                
                if epc_list is not None:
                    for epc_elem in epc_list:
                        if epc_elem.tag.endswith("epc"):
                            epc = epc_elem.text
                            # Case EPCs have format: urn:epc:id:sgtin:1234567.2000000.CASExxx
                            if epc and "urn:epc:id:sgtin:1234567.2000000." in epc and "CASE" in epc:
                                case_commissioning_event = event
                                break
                    if case_commissioning_event:
                        break
            
            if case_commissioning_event is None:
                self.log_test("Case ILMD Extension Test", False, "Could not find Case commissioning event")
                return False
            
            # Check for ILMD extension in the Case commissioning event
            extension_elem = None
            for child in case_commissioning_event:
                if child.tag.endswith("extension"):
                    extension_elem = child
                    break
            
            if extension_elem is None:
                self.log_test("Case ILMD Extension Test", False, "Case commissioning event missing extension element")
                return False
            
            # Check for ilmd element within extension
            ilmd_elem = None
            for child in extension_elem:
                if child.tag.endswith("ilmd"):
                    ilmd_elem = child
                    break
            
            if ilmd_elem is None:
                self.log_test("Case ILMD Extension Test", False, "Case commissioning event missing ilmd element in extension")
                return False
            
            # Check for lot number and expiration date
            lot_number_elem = None
            expiration_date_elem = None
            
            for child in ilmd_elem:
                if child.tag.endswith("lotNumber"):
                    lot_number_elem = child
                elif child.tag.endswith("itemExpirationDate"):
                    expiration_date_elem = child
            
            if lot_number_elem is None:
                self.log_test("Case ILMD Extension Test", False, "Case commissioning event missing lotNumber in ILMD")
                return False
            
            if expiration_date_elem is None:
                self.log_test("Case ILMD Extension Test", False, "Case commissioning event missing itemExpirationDate in ILMD")
                return False
            
            # Verify the values
            if lot_number_elem.text != "4JT0482":
                self.log_test("Case ILMD Extension Test", False, 
                            f"Expected lot number '4JT0482', got '{lot_number_elem.text}'")
                return False
            
            if expiration_date_elem.text != "2026-08-31":
                self.log_test("Case ILMD Extension Test", False, 
                            f"Expected expiration date '2026-08-31', got '{expiration_date_elem.text}'")
                return False
            
            self.log_test("Case ILMD Extension Test", True, 
                        f"Case commissioning event contains correct ILMD extension with lot_number='{lot_number_elem.text}' and expiration_date='{expiration_date_elem.text}'")
            return True
            
        except ET.ParseError as e:
            self.log_test("Case ILMD Extension Test", False, f"XML parsing error: {str(e)}")
            return False
        except Exception as e:
            self.log_test("Case ILMD Extension Test", False, f"Test error: {str(e)}")
            return False
    
    def test_complete_ilmd_coverage(self, xml_content):
        """Test that ALL commissioning events include ILMD extensions (Items, Inner Cases, Cases) but NOT SSCCs"""
        if not xml_content:
            self.log_test("Complete ILMD Coverage Test", False, "No XML content to test")
            return False
            
        try:
            root = ET.fromstring(xml_content)
            
            # Find all ObjectEvents (commissioning events)
            object_events = []
            for event in root.iter():
                if event.tag.endswith("ObjectEvent"):
                    object_events.append(event)
            
            item_event_has_ilmd = False
            case_event_has_ilmd = False
            sscc_event_has_ilmd = False
            
            for event in object_events:
                # Determine event type by examining EPCs
                epc_list = None
                for child in event:
                    if child.tag.endswith("epcList"):
                        epc_list = child
                        break
                
                if epc_list is not None:
                    first_epc = None
                    for epc_elem in epc_list:
                        if epc_elem.tag.endswith("epc"):
                            first_epc = epc_elem.text
                            break
                    
                    if first_epc:
                        # Check for ILMD extension
                        has_ilmd = False
                        for child in event:
                            if child.tag.endswith("extension"):
                                for ext_child in child:
                                    if ext_child.tag.endswith("ilmd"):
                                        has_ilmd = True
                                        break
                                break
                        
                        # Categorize event type and record ILMD presence
                        if "urn:epc:id:sgtin:" in first_epc and "ITEM" in first_epc:
                            item_event_has_ilmd = has_ilmd
                        elif "urn:epc:id:sgtin:" in first_epc and "CASE" in first_epc:
                            case_event_has_ilmd = has_ilmd
                        elif "urn:epc:id:sscc:" in first_epc:
                            sscc_event_has_ilmd = has_ilmd
            
            # Verify ILMD coverage
            success = True
            details = []
            
            if not item_event_has_ilmd:
                success = False
                details.append("Item commissioning event missing ILMD extension")
            else:
                details.append("✓ Item commissioning event has ILMD extension")
            
            if not case_event_has_ilmd:
                success = False
                details.append("Case commissioning event missing ILMD extension")
            else:
                details.append("✓ Case commissioning event has ILMD extension")
            
            if sscc_event_has_ilmd:
                success = False
                details.append("SSCC commissioning event incorrectly has ILMD extension (should not have)")
            else:
                details.append("✓ SSCC commissioning event correctly does NOT have ILMD extension")
            
            self.log_test("Complete ILMD Coverage Test", success, 
                        "ILMD extension coverage verified" if success else "ILMD extension coverage issues found",
                        "; ".join(details))
            return success
            
        except Exception as e:
            self.log_test("Complete ILMD Coverage Test", False, f"Test error: {str(e)}")
            return False
    
    def test_xml_structure_validation(self, xml_content):
        """Validate the XML structure of Case commissioning event with ILMD"""
        if not xml_content:
            self.log_test("XML Structure Validation", False, "No XML content to test")
            return False
            
        try:
            root = ET.fromstring(xml_content)
            
            # Find Case commissioning event
            case_event = None
            for event in root.iter():
                if event.tag.endswith("ObjectEvent"):
                    epc_list = None
                    for child in event:
                        if child.tag.endswith("epcList"):
                            epc_list = child
                            break
                    
                    if epc_list is not None:
                        for epc_elem in epc_list:
                            if epc_elem.tag.endswith("epc"):
                                epc = epc_elem.text
                                if epc and "urn:epc:id:sgtin:1234567.2000000." in epc and "CASE" in epc:
                                    case_event = event
                                    break
                        if case_event:
                            break
            
            if case_event is None:
                self.log_test("XML Structure Validation", False, "Could not find Case commissioning event")
                return False
            
            # Validate required elements exist
            required_elements = ["eventTime", "epcList", "action", "bizStep", "disposition", "readPoint", "bizLocation", "extension"]
            missing_elements = []
            
            for req_elem in required_elements:
                found = False
                for child in case_event:
                    if child.tag.endswith(req_elem):
                        found = True
                        break
                if not found:
                    missing_elements.append(req_elem)
            
            if missing_elements:
                self.log_test("XML Structure Validation", False, 
                            f"Case commissioning event missing required elements: {', '.join(missing_elements)}")
                return False
            
            # Validate bizLocation structure
            biz_location = None
            for child in case_event:
                if child.tag.endswith("bizLocation"):
                    biz_location = child
                    break
            
            if biz_location is not None:
                id_elem = None
                for child in biz_location:
                    if child.tag.endswith("id"):
                        id_elem = child
                        break
                
                if id_elem is None or id_elem.text != "urn:epc:id:sgln:1234567.00001.0":
                    self.log_test("XML Structure Validation", False, 
                                f"Invalid bizLocation/id: expected 'urn:epc:id:sgln:1234567.00001.0', got '{id_elem.text if id_elem else 'None'}'")
                    return False
            
            # Validate ILMD extension structure
            extension = None
            for child in case_event:
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
                    lot_found = False
                    exp_found = False
                    
                    for child in ilmd:
                        if child.tag.endswith("lotNumber") and child.text == "4JT0482":
                            lot_found = True
                        elif child.tag.endswith("itemExpirationDate") and child.text == "2026-08-31":
                            exp_found = True
                    
                    if not lot_found or not exp_found:
                        self.log_test("XML Structure Validation", False, 
                                    f"ILMD extension incomplete: lot_found={lot_found}, exp_found={exp_found}")
                        return False
                else:
                    self.log_test("XML Structure Validation", False, "Extension element missing ilmd child")
                    return False
            
            self.log_test("XML Structure Validation", True, 
                        "Case commissioning event XML structure is valid with proper ILMD extension")
            return True
            
        except Exception as e:
            self.log_test("XML Structure Validation", False, f"Validation error: {str(e)}")
            return False
    
    def run_ilmd_case_tests(self):
        """Run all ILMD Case commissioning event tests"""
        print("=" * 80)
        print("ILMD CASE COMMISSIONING EVENT TESTING")
        print("=" * 80)
        print("Testing Case commissioning event ILMD extension as requested in review")
        print("Configuration: 1234567 | 000000 | 4JT0482 | 2026-08-31 | 1 SSCC → 5 Cases → 10 Items/case")
        print("=" * 80)
        
        # Step 1: Create configuration with lot number and expiration date
        config_id = self.create_test_configuration()
        if not config_id:
            print("\n❌ Configuration creation failed. Stopping tests.")
            return False
        
        # Step 2: Create serial numbers
        serial_id = self.create_test_serial_numbers(config_id)
        if not serial_id:
            print("\n❌ Serial numbers creation failed. Stopping tests.")
            return False
        
        # Step 3: Generate EPCIS XML
        xml_content = self.generate_and_test_epcis_xml(config_id)
        if not xml_content:
            print("\n❌ EPCIS XML generation failed. Stopping tests.")
            return False
        
        # Step 4: Test Case commissioning event ILMD extension
        case_ilmd_success = self.test_case_commissioning_ilmd_extension(xml_content)
        
        # Step 5: Test complete ILMD coverage
        complete_coverage_success = self.test_complete_ilmd_coverage(xml_content)
        
        # Step 6: Test XML structure validation
        xml_structure_success = self.test_xml_structure_validation(xml_content)
        
        # Summary
        print("\n" + "=" * 80)
        print("ILMD CASE COMMISSIONING EVENT TEST SUMMARY")
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
        
        print("\nKey ILMD Features Tested:")
        print("✓ Case commissioning event ILMD extension presence")
        print("✓ Complete ILMD coverage (Items ✓, Cases ✓, SSCCs ✗)")
        print("✓ XML structure validation with proper ILMD format")
        print("✓ Lot number and expiration date values")
        
        # Overall success
        critical_tests_passed = case_ilmd_success and complete_coverage_success and xml_structure_success
        
        if critical_tests_passed:
            print("\n🎉 CASE COMMISSIONING EVENT ILMD EXTENSION IS WORKING CORRECTLY!")
        else:
            print("\n❌ CASE COMMISSIONING EVENT ILMD EXTENSION HAS ISSUES!")
        
        return critical_tests_passed

if __name__ == "__main__":
    tester = ILMDCaseTester()
    success = tester.run_ilmd_case_tests()
    sys.exit(0 if success else 1)