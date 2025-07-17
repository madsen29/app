#!/usr/bin/env python3
"""
EPCIS Filename Structure Testing - Review Request Specific
Tests the updated EPCIS filename structure functionality with focus on:
1. EPCIS filename generation using new naming convention: "epcis"-{senderGLN}-{receiverGLN}-{YYMMDD}
2. Configuration with specific sender_gln and receiver_gln values
3. Serial numbers creation for configurations
4. Filename verification in response headers
5. Date format validation (YYMMDD)
6. Existing XML generation functionality verification

Expected filename pattern: "epcis-1234567890123-9876543210987-250122.xml" (if today is January 22, 2025)
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import sys
import os
import re

# Get backend URL from environment
BACKEND_URL = "https://c8e3fe45-251a-4359-a250-c028fb05fe98.preview.emergentagent.com/api"

class FilenameStructureTester:
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
    
    def create_test_configuration(self, sender_gln, receiver_gln):
        """Create a test configuration with specific sender and receiver GLNs"""
        test_data = {
            "itemsPerCase": 10,
            "casesPerSscc": 5,
            "numberOfSscc": 1,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000000",
            "lotNumber": "TEST123",
            "expirationDate": "2026-12-31",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            "senderGln": sender_gln,
            "receiverGln": receiver_gln,
            "senderCompanyPrefix": "0345802",
            "senderSgln": f"{sender_gln}.001",
            "senderName": "Test Sender Company",
            "senderStreetAddress": "123 Sender St",
            "senderCity": "Sender City",
            "senderState": "SC",
            "senderPostalCode": "12345",
            "senderCountryCode": "US",
            "receiverCompanyPrefix": "0567890",
            "receiverSgln": f"{receiver_gln}.001",
            "receiverName": "Test Receiver Company",
            "receiverStreetAddress": "456 Receiver Ave",
            "receiverCity": "Receiver City",
            "receiverState": "RC",
            "receiverPostalCode": "67890",
            "receiverCountryCode": "US",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Test Shipper Company",
            "shipperStreetAddress": "789 Shipper Blvd",
            "shipperCity": "Shipper City",
            "shipperState": "SH",
            "shipperPostalCode": "99999",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("senderGln") == sender_gln and data.get("receiverGln") == receiver_gln:
                    self.log_test("Configuration Creation", True, f"Configuration created with GLNs: sender={sender_gln}, receiver={receiver_gln}", 
                                f"ID: {data['id']}")
                    return data["id"]
                else:
                    self.log_test("Configuration Creation", False, f"GLN mismatch: expected sender={sender_gln}, receiver={receiver_gln}, got sender={data.get('senderGln')}, receiver={data.get('receiverGln')}")
                    return None
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration Creation", False, f"Request error: {str(e)}")
            return None

    def create_test_serial_numbers(self, config_id):
        """Create serial numbers for the test configuration"""
        if not config_id:
            self.log_test("Serial Numbers Creation", False, "No configuration ID available")
            return None
            
        # For config: 10 items per case, 5 cases per SSCC, 1 SSCC
        # Expected: 1 SSCC, 5 cases, 50 items
        test_data = {
            "configurationId": config_id,
            "ssccSerialNumbers": ["SSCC001"],
            "caseSerialNumbers": [f"CASE{i+1:03d}" for i in range(5)],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(50)]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (len(data["ssccSerialNumbers"]) == 1 and 
                    len(data["caseSerialNumbers"]) == 5 and
                    len(data["itemSerialNumbers"]) == 50):
                    self.log_test("Serial Numbers Creation", True, "Serial numbers created successfully",
                                f"SSCC: {len(data['ssccSerialNumbers'])}, Cases: {len(data['caseSerialNumbers'])}, Items: {len(data['itemSerialNumbers'])}")
                    return data["id"]
                else:
                    self.log_test("Serial Numbers Creation", False, f"Count mismatch - SSCC: {len(data['ssccSerialNumbers'])}, Cases: {len(data['caseSerialNumbers'])}, Items: {len(data['itemSerialNumbers'])}")
                    return None
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return None

    def test_filename_structure(self, config_id, expected_sender_gln, expected_receiver_gln):
        """Test EPCIS filename structure in response headers"""
        if not config_id:
            self.log_test("Filename Structure Test", False, "No configuration ID available")
            return False
            
        test_data = {
            "configurationId": config_id,
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-epcis",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Check Content-Disposition header for filename
                content_disposition = response.headers.get('Content-Disposition', '')
                
                if 'attachment; filename=' in content_disposition:
                    # Extract filename from header
                    filename_match = re.search(r'filename=([^;]+)', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1).strip()
                        
                        # Get today's date in YYMMDD format
                        today_yymmdd = datetime.now(timezone.utc).strftime("%y%m%d")
                        
                        # Expected filename pattern: "epcis-{senderGLN}-{receiverGLN}-{YYMMDD}.xml"
                        expected_filename = f"epcis-{expected_sender_gln}-{expected_receiver_gln}-{today_yymmdd}.xml"
                        
                        if filename == expected_filename:
                            self.log_test("Filename Structure Test", True, f"Filename follows correct pattern: {filename}")
                            
                            # Additional validation: check filename components
                            filename_parts = filename.replace('.xml', '').split('-')
                            if (len(filename_parts) == 4 and 
                                filename_parts[0] == 'epcis' and
                                filename_parts[1] == expected_sender_gln and
                                filename_parts[2] == expected_receiver_gln and
                                filename_parts[3] == today_yymmdd):
                                self.log_test("Filename Components Validation", True, 
                                            f"All components correct: prefix=epcis, sender={filename_parts[1]}, receiver={filename_parts[2]}, date={filename_parts[3]}")
                                return True
                            else:
                                self.log_test("Filename Components Validation", False, 
                                            f"Component mismatch: {filename_parts}")
                                return False
                        else:
                            self.log_test("Filename Structure Test", False, 
                                        f"Filename mismatch. Expected: {expected_filename}, Got: {filename}")
                            return False
                    else:
                        self.log_test("Filename Structure Test", False, "Could not extract filename from Content-Disposition header")
                        return False
                else:
                    self.log_test("Filename Structure Test", False, f"Content-Disposition header missing or invalid: {content_disposition}")
                    return False
            else:
                self.log_test("Filename Structure Test", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Filename Structure Test", False, f"Request error: {str(e)}")
            return False

    def test_xml_generation_functionality(self, config_id):
        """Test that existing XML generation functionality still works correctly"""
        if not config_id:
            self.log_test("XML Generation Functionality", False, "No configuration ID available")
            return False
            
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
                
                # Basic XML validation
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Check root element
                    if not root.tag.endswith("EPCISDocument"):
                        self.log_test("XML Generation Functionality", False, f"Invalid root element: {root.tag}")
                        return False
                    
                    # Check schema version
                    schema_version = root.get("schemaVersion")
                    if schema_version != "1.2":
                        self.log_test("XML Generation Functionality", False, f"Expected schemaVersion='1.2', got '{schema_version}'")
                        return False
                    
                    # Check for EPCISBody and EventList
                    epcis_body = None
                    for child in root:
                        if child.tag.endswith("EPCISBody"):
                            epcis_body = child
                            break
                    
                    if epcis_body is None:
                        self.log_test("XML Generation Functionality", False, "Missing EPCISBody element")
                        return False
                    
                    event_list = None
                    for child in epcis_body:
                        if child.tag.endswith("EventList"):
                            event_list = child
                            break
                            
                    if event_list is None:
                        self.log_test("XML Generation Functionality", False, "Missing EventList element")
                        return False
                    
                    # Count events
                    object_events = 0
                    aggregation_events = 0
                    
                    for child in event_list:
                        if child.tag.endswith("ObjectEvent"):
                            object_events += 1
                        elif child.tag.endswith("AggregationEvent"):
                            aggregation_events += 1
                    
                    # For our test config (1 SSCC, 5 cases, 50 items):
                    # Expected: 3 ObjectEvents (Items, Cases, SSCCs) + 6 AggregationEvents (5 Items→Cases + 1 Cases→SSCC)
                    expected_object_events = 3
                    expected_aggregation_events = 6
                    
                    if object_events == expected_object_events and aggregation_events == expected_aggregation_events:
                        self.log_test("XML Generation Functionality", True, 
                                    f"Valid EPCIS 1.2 XML generated with correct event structure",
                                    f"ObjectEvents: {object_events}, AggregationEvents: {aggregation_events}")
                        return True
                    else:
                        self.log_test("XML Generation Functionality", False, 
                                    f"Event count mismatch - ObjectEvents: {object_events} (expected {expected_object_events}), AggregationEvents: {aggregation_events} (expected {expected_aggregation_events})")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("XML Generation Functionality", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("XML Generation Functionality", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("XML Generation Functionality", False, f"Request error: {str(e)}")
            return False

    def test_multiple_gln_scenarios(self):
        """Test filename generation with different GLN combinations"""
        test_scenarios = [
            ("1234567890123", "9876543210987"),  # Review request example
            ("0345802000014", "0567890000021"),  # Different GLNs
            ("1111111111111", "2222222222222"),  # Simple GLNs
        ]
        
        all_passed = True
        
        for sender_gln, receiver_gln in test_scenarios:
            print(f"\n--- Testing GLN Scenario: sender={sender_gln}, receiver={receiver_gln} ---")
            
            # Create configuration
            config_id = self.create_test_configuration(sender_gln, receiver_gln)
            if not config_id:
                all_passed = False
                continue
            
            # Create serial numbers
            serial_id = self.create_test_serial_numbers(config_id)
            if not serial_id:
                all_passed = False
                continue
            
            # Test filename structure
            filename_success = self.test_filename_structure(config_id, sender_gln, receiver_gln)
            if not filename_success:
                all_passed = False
            
            # Test XML generation functionality
            xml_success = self.test_xml_generation_functionality(config_id)
            if not xml_success:
                all_passed = False
        
        return all_passed

    def run_filename_structure_tests(self):
        """Run comprehensive filename structure tests"""
        print("=" * 80)
        print("EPCIS FILENAME STRUCTURE TESTING - REVIEW REQUEST SPECIFIC")
        print("=" * 80)
        print("Testing new naming convention: 'epcis'-{senderGLN}-{receiverGLN}-{YYMMDD}")
        print("Expected pattern example: epcis-1234567890123-9876543210987-250122.xml")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Multiple GLN scenarios
        scenarios_success = self.test_multiple_gln_scenarios()
        
        # Summary
        print("\n" + "=" * 80)
        print("FILENAME STRUCTURE TEST SUMMARY")
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
        
        print("\nFilename Structure Features Tested:")
        print("✓ Configuration creation with sender_gln and receiver_gln")
        print("✓ Serial numbers creation for configurations")
        print("✓ EPCIS filename generation with new naming convention")
        print("✓ Filename verification in response headers")
        print("✓ Date format validation (YYMMDD)")
        print("✓ Multiple GLN combinations")
        print("✓ Existing XML generation functionality preservation")
        
        return passed == total

if __name__ == "__main__":
    tester = FilenameStructureTester()
    success = tester.run_filename_structure_tests()
    sys.exit(0 if success else 1)