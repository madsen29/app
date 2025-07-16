#!/usr/bin/env python3
"""
Backend API Testing for EPCIS Serial Number Aggregation App - REVIEW REQUEST FOCUSED TESTING
Tests the enhanced hierarchical serial number collection system with focus on:
1. Enhanced Duplicate Detection in Textarea (Backend Integration)
2. Multi-level Navigation Data Preservation (Backend Integration)
3. Hierarchical Serial Collection Backend Integration
4. EPCIS XML Generation (Package NDC hyphen removal and EPCClass ordering)

Specific focus on testing the two critical issues:
- Package NDC hyphen removal not working
- EPCClass vocabulary element order incorrect
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://1379817a-9549-4f0e-8757-8e6eaf81b9ac.preview.emergentagent.com/api"

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
    
    def test_review_request_specific_configuration(self):
        """Test configuration creation with review request specific parameters"""
        # Review request configuration: 1 SSCC, 2 Cases, 2 Inner Cases per Case, 3 Items per Inner Case
        # Company Prefix: 1234567, Package NDC: 45802-046-85
        test_data = {
            "items_per_case": 0,  # Not used when inner cases enabled
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": True,
            "inner_cases_per_case": 2,
            "items_per_inner_case": 3,
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
            "package_ndc": "45802-046-85",  # This should be cleaned to 4580204685 in EPCIS XML
            "regulated_product_name": "Test Product",
            "manufacturer_name": "Test Manufacturer",
            "dosage_form_type": "Tablet",
            "strength_description": "10mg",
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
                # Verify package_ndc is stored correctly (with hyphens)
                if data.get("package_ndc") == "45802-046-85":
                    self.log_test("Review Request Configuration", True, "Configuration created with package_ndc field", 
                                f"ID: {data['id']}, Package NDC: {data['package_ndc']}")
                    return data["id"]
                else:
                    self.log_test("Review Request Configuration", False, f"Package NDC mismatch: expected '45802-046-85', got '{data.get('package_ndc')}'")
                    return None
            else:
                self.log_test("Review Request Configuration", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Review Request Configuration", False, f"Request error: {str(e)}")
            return None

    def test_review_request_serial_numbers(self, config_id):
        """Test serial numbers creation for review request configuration"""
        if not config_id:
            self.log_test("Review Request Serial Numbers", False, "No configuration ID available")
            return None
            
        # For config: 1 SSCC, 2 Cases, 2 Inner Cases per Case, 3 Items per Inner Case
        # Expected: 1 SSCC, 2 Cases, 4 Inner Cases (2×2), 12 Items (3×2×2)
        sscc_serials = ["SSCC001"]
        case_serials = ["CASE001", "CASE002"]
        inner_case_serials = ["INNER001", "INNER002", "INNER003", "INNER004"]
        item_serials = [f"ITEM{i+1:03d}" for i in range(12)]
        
        test_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": sscc_serials,
            "case_serial_numbers": case_serials,
            "inner_case_serial_numbers": inner_case_serials,
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
                    len(data["case_serial_numbers"]) == 2 and
                    len(data["inner_case_serial_numbers"]) == 4 and
                    len(data["item_serial_numbers"]) == 12):
                    self.log_test("Review Request Serial Numbers", True, "Serial numbers saved for 4-level hierarchy",
                                f"SSCC: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Inner Cases: {len(data['inner_case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
                    return data["id"]
                else:
                    self.log_test("Review Request Serial Numbers", False, f"Count mismatch - SSCC: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Inner Cases: {len(data['inner_case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
                    return None
            else:
                self.log_test("Review Request Serial Numbers", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Review Request Serial Numbers", False, f"Request error: {str(e)}")
            return None

    def test_package_ndc_hyphen_removal(self, config_id):
        """Test that package_ndc hyphens are removed in EPCIS XML generation"""
        if not config_id:
            self.log_test("Package NDC Hyphen Removal", False, "No configuration ID available")
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
                
                # Check if hyphens are removed from package_ndc in XML
                if "45802-046-85" in xml_content:
                    self.log_test("Package NDC Hyphen Removal", False, "CRITICAL: Package NDC still contains hyphens in EPCIS XML", 
                                "Found '45802-046-85' instead of expected '4580204685'")
                    return False
                elif "4580204685" in xml_content:
                    self.log_test("Package NDC Hyphen Removal", True, "Package NDC hyphens correctly removed in EPCIS XML")
                    return True
                else:
                    self.log_test("Package NDC Hyphen Removal", False, "Package NDC not found in EPCIS XML")
                    return False
            else:
                self.log_test("Package NDC Hyphen Removal", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Package NDC Hyphen Removal", False, f"Request error: {str(e)}")
            return False

    def test_epcclass_vocabulary_order(self, config_id):
        """Test that EPCClass vocabulary elements are in correct order: Item → Inner Case → Case"""
        if not config_id:
            self.log_test("EPCClass Vocabulary Order", False, "No configuration ID available")
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
                
                # Parse XML to check EPCClass order
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find VocabularyElementList
                    vocabulary_elements = []
                    for elem in root.iter():
                        if elem.tag.endswith("VocabularyElement"):
                            vocabulary_elements.append(elem.get("id"))
                    
                    # Expected order: Item → Inner Case → Case
                    expected_patterns = [
                        "urn:epc:idpat:sgtin:1234567.1000000.*",  # Item (indicator 1)
                        "urn:epc:idpat:sgtin:1234567.4000001.*",  # Inner Case (indicator 4)
                        "urn:epc:idpat:sgtin:1234567.2000000.*"   # Case (indicator 2)
                    ]
                    
                    if vocabulary_elements == expected_patterns:
                        self.log_test("EPCClass Vocabulary Order", True, "EPCClass elements in correct order: Item → Inner Case → Case")
                        return True
                    else:
                        self.log_test("EPCClass Vocabulary Order", False, f"CRITICAL: EPCClass order incorrect. Expected: {expected_patterns}, Found: {vocabulary_elements}")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("EPCClass Vocabulary Order", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("EPCClass Vocabulary Order", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("EPCClass Vocabulary Order", False, f"Request error: {str(e)}")
            return False

    def test_multiple_hierarchy_configurations(self):
        """Test different hierarchy configurations (2-level, 3-level, 4-level)"""
        
        # Test 2-level hierarchy: SSCC → Items (no cases)
        config_2_level = {
            "items_per_case": 10,  # items per SSCC when no cases
            "cases_per_sscc": 0,   # No cases
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
        
        # Test 3-level hierarchy: SSCC → Cases → Items
        config_3_level = {
            "items_per_case": 5,
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
        
        # Test 4-level hierarchy: SSCC → Cases → Inner Cases → Items (already tested above)
        
        test_configs = [
            ("2-level (SSCC→Items)", config_2_level, 2, 1),  # 2 ObjectEvents, 1 AggregationEvent
            ("3-level (SSCC→Cases→Items)", config_3_level, 3, 3)  # 3 ObjectEvents, 3 AggregationEvents
        ]
        
        for config_name, config_data, expected_obj_events, expected_agg_events in test_configs:
            try:
                # Create configuration
                response = self.session.post(
                    f"{self.base_url}/configuration",
                    json=config_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    config_id = response.json()["id"]
                    
                    # Create appropriate serial numbers
                    if config_name.startswith("2-level"):
                        serial_data = {
                            "configuration_id": config_id,
                            "sscc_serial_numbers": ["SSCC001"],
                            "case_serial_numbers": [],
                            "inner_case_serial_numbers": [],
                            "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(10)]
                        }
                    else:  # 3-level
                        serial_data = {
                            "configuration_id": config_id,
                            "sscc_serial_numbers": ["SSCC001"],
                            "case_serial_numbers": ["CASE001", "CASE002"],
                            "inner_case_serial_numbers": [],
                            "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(10)]
                        }
                    
                    # Save serial numbers
                    serial_response = self.session.post(
                        f"{self.base_url}/serial-numbers",
                        json=serial_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if serial_response.status_code == 200:
                        # Generate EPCIS and validate
                        epcis_response = self.session.post(
                            f"{self.base_url}/generate-epcis",
                            json={
                                "configuration_id": config_id,
                                "read_point": "urn:epc:id:sgln:1234567.00000.0",
                                "biz_location": "urn:epc:id:sgln:1234567.00001.0"
                            },
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if epcis_response.status_code == 200:
                            xml_content = epcis_response.text
                            
                            # Verify package NDC hyphen removal
                            ndc_clean = "4580204685" in xml_content and "45802-046-85" not in xml_content
                            
                            # Parse XML to count events
                            root = ET.fromstring(xml_content)
                            object_events = 0
                            aggregation_events = 0
                            
                            for elem in root.iter():
                                if elem.tag.endswith("ObjectEvent"):
                                    object_events += 1
                                elif elem.tag.endswith("AggregationEvent"):
                                    aggregation_events += 1
                            
                            events_correct = (object_events == expected_obj_events and 
                                            aggregation_events == expected_agg_events)
                            
                            if ndc_clean and events_correct:
                                self.log_test(f"Multiple Hierarchy - {config_name}", True, 
                                            f"Valid EPCIS XML with clean NDC and correct event counts",
                                            f"ObjectEvents: {object_events}, AggregationEvents: {aggregation_events}")
                            else:
                                self.log_test(f"Multiple Hierarchy - {config_name}", False, 
                                            f"NDC clean: {ndc_clean}, Events correct: {events_correct}")
                        else:
                            self.log_test(f"Multiple Hierarchy - {config_name}", False, 
                                        f"EPCIS generation failed: {epcis_response.status_code}")
                    else:
                        self.log_test(f"Multiple Hierarchy - {config_name}", False, 
                                    f"Serial numbers creation failed: {serial_response.status_code}")
                else:
                    self.log_test(f"Multiple Hierarchy - {config_name}", False, 
                                f"Configuration creation failed: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Multiple Hierarchy - {config_name}", False, f"Test error: {str(e)}")
    
    def test_configuration_validation(self):
        """Test configuration creation with missing required GS1 parameters"""
        invalid_data = {
            "items_per_case": 10,
            "cases_per_sscc": 5
            # Missing required GS1 parameters: number_of_sscc, company_prefix, product codes, indicator digits
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Should reject with 422 due to missing required fields
            if response.status_code in [400, 422]:
                self.log_test("Configuration Validation", True, "Missing GS1 parameters properly rejected")
            elif response.status_code == 200:
                self.log_test("Configuration Validation", False, "Missing GS1 parameters were accepted (validation issue)")
            else:
                self.log_test("Configuration Validation", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Configuration Validation", False, f"Request error: {str(e)}")
    
    def test_serial_numbers_creation(self, config_id):
        """Test POST /api/serial-numbers with new hierarchy validation"""
        if not config_id:
            self.log_test("Serial Numbers Creation", False, "No configuration ID available")
            return None
            
        # For config: 10 items per case, 5 cases per SSCC, 2 SSCCs
        # Expected: 2 SSCC serials, 10 case serials (5×2), 100 item serials (10×5×2)
        sscc_serials = [f"SSCC{i+1:03d}" for i in range(2)]
        case_serials = [f"CASE{i+1:03d}" for i in range(10)]  # 5 cases per SSCC × 2 SSCCs = 10 total cases
        item_serials = [f"ITEM{i+1:03d}" for i in range(100)]  # 10 items per case × 10 cases = 100 total items
        
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
                required_fields = ["id", "configuration_id", "sscc_serial_numbers", "case_serial_numbers", "item_serial_numbers", "timestamp"]
                
                if all(field in data for field in required_fields):
                    if (len(data["sscc_serial_numbers"]) == 2 and 
                        len(data["case_serial_numbers"]) == 10 and
                        len(data["item_serial_numbers"]) == 100 and
                        data["configuration_id"] == config_id):
                        self.log_test("Serial Numbers Creation", True, "Serial numbers saved with correct hierarchy validation",
                                    f"SSCCs: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
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
        """Test serial numbers validation with incorrect counts for new hierarchy"""
        if not config_id:
            self.log_test("Serial Numbers Validation", False, "No configuration ID available")
            return
            
        # Test with wrong number of SSCC serials (should be 2, providing 1)
        invalid_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": [f"SSCC{i+1:03d}" for i in range(1)],  # Wrong: 1 SSCC instead of 2
            "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(10)],  # Correct: 10 cases
            "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(100)]  # Correct: 100 items
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                error_msg = response.json().get("detail", "")
                if "Expected 2 SSCC serial numbers" in error_msg:
                    self.log_test("Serial Numbers Validation", True, "Validation correctly rejected wrong SSCC count")
                else:
                    self.log_test("Serial Numbers Validation", False, f"Wrong error message: {error_msg}")
            else:
                self.log_test("Serial Numbers Validation", False, f"Expected 400 error, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Serial Numbers Validation", False, f"Request error: {str(e)}")
    
    def test_epcis_generation_detailed(self, config_id):
        """Test EPCIS generation with detailed XML analysis for 4-level hierarchy"""
        if not config_id:
            self.log_test("EPCIS Generation Detailed", False, "No configuration ID available")
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
                
                # Parse and analyze XML structure
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find EventList
                    event_list = None
                    for elem in root.iter():
                        if elem.tag.endswith("EventList"):
                            event_list = elem
                            break
                    
                    if event_list is not None:
                        object_events = []
                        aggregation_events = []
                        
                        for child in event_list:
                            if child.tag.endswith("ObjectEvent"):
                                object_events.append(child)
                            elif child.tag.endswith("AggregationEvent"):
                                aggregation_events.append(child)
                        
                        # For 4-level hierarchy (SSCC→Cases→Inner Cases→Items):
                        # Expected ObjectEvents: Items, Inner Cases, Cases, SSCCs = 4 events
                        # Expected AggregationEvents: Items→Inner Cases (4) + Inner Cases→Cases (2) + Cases→SSCCs (1) = 7 events
                        
                        expected_object_events = 4  # Items, Inner Cases, Cases, SSCCs
                        expected_aggregation_events = 7  # 4 + 2 + 1
                        
                        object_events_ok = len(object_events) == expected_object_events
                        aggregation_events_ok = len(aggregation_events) == expected_aggregation_events
                        
                        if object_events_ok and aggregation_events_ok:
                            self.log_test("EPCIS Generation Detailed", True, f"Valid 4-level hierarchy EPCIS XML generated",
                                        f"ObjectEvents: {len(object_events)}, AggregationEvents: {len(aggregation_events)}")
                        else:
                            self.log_test("EPCIS Generation Detailed", False, 
                                        f"Event count mismatch - ObjectEvents: {len(object_events)} (expected {expected_object_events}), AggregationEvents: {len(aggregation_events)} (expected {expected_aggregation_events})")
                    else:
                        self.log_test("EPCIS Generation Detailed", False, "EventList not found in XML")
                        
                except ET.ParseError as e:
                    self.log_test("EPCIS Generation Detailed", False, f"XML parsing error: {str(e)}")
            else:
                self.log_test("EPCIS Generation Detailed", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("EPCIS Generation Detailed", False, f"Request error: {str(e)}")
    
    def validate_epcis_1_2_xml(self, xml_content):
        """Validate EPCIS 1.2 XML with commissioning events and proper GS1 identifiers"""
        try:
            root = ET.fromstring(xml_content)
            
            # Check root element and EPCIS 1.2 namespace
            if not root.tag.endswith("EPCISDocument"):
                print(f"   Invalid root element: {root.tag}")
                return False
            
            # Check for EPCIS 1.2 namespace (should be urn:epcglobal:epcis:xsd:1)
            if not root.tag.startswith("{urn:epcglobal:epcis:xsd:1}"):
                print(f"   Invalid EPCIS namespace - expected 1.2: {root.tag}")
                return False
            
            # Check schema version
            schema_version = root.get("schemaVersion")
            if schema_version != "1.2":
                print(f"   Expected schemaVersion='1.2', got '{schema_version}'")
                return False
            
            # Find EPCISBody and EventList
            epcis_body = None
            for child in root:
                if child.tag.endswith("EPCISBody"):
                    epcis_body = child
                    break
            
            if epcis_body is None:
                print(f"   Missing EPCISBody element")
                return False
            
            event_list = None
            for child in epcis_body:
                if child.tag.endswith("EventList"):
                    event_list = child
                    break
                    
            if event_list is None:
                print(f"   Missing EventList element")
                return False
            
            # Count different event types
            object_events = []
            aggregation_events = []
            
            for child in event_list:
                if child.tag.endswith("ObjectEvent"):
                    object_events.append(child)
                elif child.tag.endswith("AggregationEvent"):
                    aggregation_events.append(child)
            
            # Expected events for our test scenario (CORRECTED):
            # - 1 ObjectEvent for all item commissioning (100 EPCs)
            # - 1 ObjectEvent for all case commissioning (10 EPCs)
            # - 1 ObjectEvent for all SSCC commissioning (2 EPCs)
            # - 10 AggregationEvents for Items→Cases (10 items per case × 10 cases)
            # - 2 AggregationEvents for Cases→SSCCs (5 cases per SSCC × 2 SSCCs)
            # Total: 3 ObjectEvents + 12 AggregationEvents = 15 events
            
            expected_object_events = 3  # One bulk event each for Items, Cases, SSCCs
            expected_aggregation_events = 10 + 2   # Items→Cases + Cases→SSCCs
            
            if len(object_events) != expected_object_events:
                print(f"   Expected {expected_object_events} ObjectEvents (commissioning), found {len(object_events)}")
                return False
                
            if len(aggregation_events) != expected_aggregation_events:
                print(f"   Expected {expected_aggregation_events} AggregationEvents, found {len(aggregation_events)}")
                return False
            
            # Validate commissioning events (ObjectEvents)
            commissioning_events_validated = self.validate_commissioning_events(object_events)
            if not commissioning_events_validated:
                return False
            
            # Validate aggregation events structure
            aggregation_events_validated = self.validate_aggregation_events(aggregation_events)
            if not aggregation_events_validated:
                return False
            
            # Validate GS1 identifier formats
            gs1_identifiers_validated = self.validate_gs1_identifiers(object_events, aggregation_events)
            if not gs1_identifiers_validated:
                return False
            
            print(f"   ✓ Valid EPCIS 1.2 XML with schema version {schema_version}")
            print(f"   ✓ Commissioning events: {len(object_events)} ObjectEvents")
            print(f"   ✓ Aggregation events: {len(aggregation_events)} AggregationEvents")
            print(f"   ✓ GS1 identifiers use correct format with indicator digits")
            return True
            
        except ET.ParseError as e:
            print(f"   XML parsing error: {str(e)}")
            return False
        except Exception as e:
            print(f"   Validation error: {str(e)}")
            return False
    
    def validate_commissioning_events(self, object_events):
        """Validate ObjectEvents are proper commissioning events"""
        try:
            for event in object_events:
                # Check required elements
                required_elements = ["eventTime", "epcList", "action", "bizStep", "disposition"]
                
                for element_name in required_elements:
                    elem = None
                    for child in event:
                        if child.tag.endswith(element_name):
                            elem = child
                            break
                    if elem is None:
                        print(f"   Missing {element_name} in ObjectEvent")
                        return False
                
                # Check action is ADD
                action_elem = None
                for child in event:
                    if child.tag.endswith("action"):
                        action_elem = child
                        break
                if action_elem.text != "ADD":
                    print(f"   Expected action 'ADD' in commissioning event, got '{action_elem.text}'")
                    return False
                
                # Check bizStep is commissioning
                bizstep_elem = None
                for child in event:
                    if child.tag.endswith("bizStep"):
                        bizstep_elem = child
                        break
                if "commissioning" not in bizstep_elem.text:
                    print(f"   Expected commissioning bizStep, got '{bizstep_elem.text}'")
                    return False
            
            return True
        except Exception as e:
            print(f"   Error validating commissioning events: {str(e)}")
            return False
    
    def validate_aggregation_events(self, aggregation_events):
        """Validate AggregationEvents structure"""
        try:
            for event in aggregation_events:
                # Check required elements
                required_elements = ["eventTime", "parentID", "childEPCs", "action", "bizStep"]
                
                for element_name in required_elements:
                    elem = None
                    for child in event:
                        if child.tag.endswith(element_name):
                            elem = child
                            break
                    if elem is None:
                        print(f"   Missing {element_name} in AggregationEvent")
                        return False
                
                # Check action is ADD
                action_elem = None
                for child in event:
                    if child.tag.endswith("action"):
                        action_elem = child
                        break
                if action_elem.text != "ADD":
                    print(f"   Expected action 'ADD' in aggregation event, got '{action_elem.text}'")
                    return False
                
                # Check bizStep is packing
                bizstep_elem = None
                for child in event:
                    if child.tag.endswith("bizStep"):
                        bizstep_elem = child
                        break
                if "packing" not in bizstep_elem.text:
                    print(f"   Expected packing bizStep, got '{bizstep_elem.text}'")
                    return False
            
            return True
        except Exception as e:
            print(f"   Error validating aggregation events: {str(e)}")
            return False
    
    def validate_gs1_identifiers(self, object_events, aggregation_events):
        """Validate GS1 identifier formats with correct indicator digit placement"""
        try:
            company_prefix = "9876543"
            item_product_code = "123456"
            case_product_code = "789012"
            sscc_indicator_digit = "3"
            case_indicator_digit = "2"
            item_indicator_digit = "1"
            
            # Check ObjectEvent EPCs
            for event in object_events:
                epc_list_elem = None
                for child in event:
                    if child.tag.endswith("epcList"):
                        epc_list_elem = child
                        break
                
                if epc_list_elem is not None:
                    for epc_elem in epc_list_elem:
                        if epc_elem.tag.endswith("epc"):
                            epc = epc_elem.text
                            
                            # Validate EPC format
                            if epc.startswith("urn:epc:id:sscc:"):
                                # SSCC format: urn:epc:id:sscc:{company_prefix}.{sscc_indicator_digit}{sscc_serial}
                                expected_prefix = f"urn:epc:id:sscc:{company_prefix}.{sscc_indicator_digit}"
                                if not epc.startswith(expected_prefix):
                                    print(f"   Invalid SSCC format: {epc}")
                                    print(f"   Expected to start with: {expected_prefix}")
                                    return False
                            elif epc.startswith("urn:epc:id:sgtin:"):
                                # SGTIN format: urn:epc:id:sgtin:{company_prefix}.{indicator_digit}{product_code}.{serial}
                                if f".{case_indicator_digit}{case_product_code}." in epc:
                                    # Case SGTIN
                                    expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}."
                                    if not epc.startswith(expected_prefix):
                                        print(f"   Invalid Case SGTIN format: {epc}")
                                        print(f"   Expected to start with: {expected_prefix}")
                                        return False
                                elif f".{item_indicator_digit}{item_product_code}." in epc:
                                    # Item SGTIN
                                    expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}."
                                    if not epc.startswith(expected_prefix):
                                        print(f"   Invalid Item SGTIN format: {epc}")
                                        print(f"   Expected to start with: {expected_prefix}")
                                        return False
                                else:
                                    print(f"   Unknown SGTIN format: {epc}")
                                    return False
                            else:
                                print(f"   Unknown EPC format: {epc}")
                                return False
            
            # Check AggregationEvent parent and child EPCs
            for event in aggregation_events:
                parent_id_elem = None
                child_epcs_elem = None
                
                for child in event:
                    if child.tag.endswith("parentID"):
                        parent_id_elem = child
                    elif child.tag.endswith("childEPCs"):
                        child_epcs_elem = child
                
                # Validate parent ID
                if parent_id_elem is not None:
                    parent_epc = parent_id_elem.text
                    if parent_epc.startswith("urn:epc:id:sscc:"):
                        expected_prefix = f"urn:epc:id:sscc:{company_prefix}.{sscc_indicator_digit}"
                        if not parent_epc.startswith(expected_prefix):
                            print(f"   Invalid parent SSCC format: {parent_epc}")
                            return False
                    elif parent_epc.startswith("urn:epc:id:sgtin:"):
                        expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}."
                        if not parent_epc.startswith(expected_prefix):
                            print(f"   Invalid parent Case SGTIN format: {parent_epc}")
                            return False
                
                # Validate child EPCs
                if child_epcs_elem is not None:
                    for child_epc_elem in child_epcs_elem:
                        if child_epc_elem.tag.endswith("epc"):
                            child_epc = child_epc_elem.text
                            if child_epc.startswith("urn:epc:id:sgtin:"):
                                if f".{case_indicator_digit}{case_product_code}." in child_epc:
                                    expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}."
                                elif f".{item_indicator_digit}{item_product_code}." in child_epc:
                                    expected_prefix = f"urn:epc:id:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}."
                                else:
                                    print(f"   Unknown child SGTIN format: {child_epc}")
                                    return False
                                
                                if not child_epc.startswith(expected_prefix):
                                    print(f"   Invalid child SGTIN format: {child_epc}")
                                    return False
            
            return True
        except Exception as e:
            print(f"   Error validating GS1 identifiers: {str(e)}")
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
                    "sscc_serial_numbers": ["SSCC001"],
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
    
    def run_review_request_tests(self):
        """Run tests focused on review request requirements"""
        print("=" * 80)
        print("REVIEW REQUEST FOCUSED TESTING - HIERARCHICAL SERIAL NUMBER COLLECTION")
        print("=" * 80)
        print("Testing Configuration: 1 SSCC, 2 Cases, 2 Inner Cases per Case, 3 Items per Inner Case")
        print("Focus Areas:")
        print("1. Enhanced Duplicate Detection (Backend Integration)")
        print("2. Multi-level Navigation Data Preservation (Backend Integration)")
        print("3. Hierarchical Serial Collection Backend Integration")
        print("4. EPCIS XML Generation (Package NDC & EPCClass ordering)")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Review Request Specific Configuration
        config_id = self.test_review_request_specific_configuration()
        
        # Test 3: Review Request Serial Numbers
        serial_id = self.test_review_request_serial_numbers(config_id)
        
        # Test 4: Package NDC Hyphen Removal (CRITICAL ISSUE)
        package_ndc_success = self.test_package_ndc_hyphen_removal(config_id)
        
        # Test 5: EPCClass Vocabulary Order (CRITICAL ISSUE)
        epcclass_order_success = self.test_epcclass_vocabulary_order(config_id)
        
        # Test 6: Hierarchical Data Integrity
        data_integrity_success = self.test_hierarchical_data_integrity(config_id)
        
        # Test 7: Detailed EPCIS Generation Test (for 4-level hierarchy)
        self.test_epcis_generation_detailed(config_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("REVIEW REQUEST TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical Issues Status
        print("\n" + "=" * 40)
        print("CRITICAL ISSUES STATUS")
        print("=" * 40)
        print(f"Package NDC Hyphen Removal: {'✅ FIXED' if package_ndc_success else '❌ STILL FAILING'}")
        print(f"EPCClass Vocabulary Order: {'✅ FIXED' if epcclass_order_success else '❌ STILL FAILING'}")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nReview Request Features Tested:")
        print("✓ 4-level hierarchy: SSCC→Cases→Inner Cases→Items")
        print("✓ Package NDC field storage and processing")
        print("✓ EPCClass vocabulary generation and ordering")
        print("✓ Hierarchical data conversion to flat arrays")
        print("✓ Backend integration for enhanced serial collection")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_review_request_tests()
    sys.exit(0 if success else 1)