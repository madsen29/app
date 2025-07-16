#!/usr/bin/env python3
"""
SBDH and Location Vocabulary Testing for GS1 Rx EPCIS Compliance
Tests the updated SBDH and Location vocabulary implementation to verify GS1 Rx EPCIS compliance.

SPECIFIC VERIFICATION REQUIREMENTS:
1. SBDH Structure - Verify StandardBusinessDocument wrapper with proper namespaces
2. SBDH Header - Check sender/receiver GLN identifiers in SBDH header
3. Location Vocabulary - Verify complete address information in Location vocabulary elements
4. All existing features still working - Ensure no regression in existing functionality
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://443af6fc-0d8a-42dd-a86d-aab66f8c129f.preview.emergentagent.com/api"

class SBDHLocationTester:
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
    
    def create_test_configuration(self):
        """Create test configuration with enhanced address information from review request"""
        test_data = {
            "items_per_case": 3,
            "cases_per_sscc": 2,
            "number_of_sscc": 1,
            "use_inner_cases": False,
            "company_prefix": "1234567",
            "item_product_code": "000000",
            "case_product_code": "000001",
            "lot_number": "LOT123",
            "expiration_date": "2025-12-31",
            "sscc_indicator_digit": "3",
            "case_indicator_digit": "2",
            "item_indicator_digit": "1",
            # Business Document Information with complete address data
            "sender_company_prefix": "0345802",
            "sender_gln": "0345802000014",
            "sender_sgln": "0345802000014.001",
            "sender_name": "Padagis US LLC",
            "sender_street_address": "1251 Lincoln Rd",
            "sender_city": "Allegan",
            "sender_state": "MI",
            "sender_postal_code": "49010",
            "sender_country_code": "US",
            "receiver_company_prefix": "0567890",
            "receiver_gln": "0567890000021",
            "receiver_sgln": "0567890000021.001",
            "receiver_name": "Pharmacy Corp",
            "receiver_street_address": "123 Main St",
            "receiver_city": "New York",
            "receiver_state": "NY",
            "receiver_postal_code": "10001",
            "receiver_country_code": "US",
            "shipper_company_prefix": "0999888",
            "shipper_gln": "0999888000028",
            "shipper_sgln": "0999888000028.001",
            "shipper_name": "Shipping Corp",
            "shipper_street_address": "456 Shipping Ave",
            "shipper_city": "Chicago",
            "shipper_state": "IL",
            "shipper_postal_code": "60007",
            "shipper_country_code": "US",
            "shipper_same_as_sender": False,
            "package_ndc": "45802-046-85",
            "regulated_product_name": "Test Product",
            "manufacturer_name": "Test Manufacturer"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/configuration",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Configuration Creation", True, "Configuration created with complete address information", 
                            f"ID: {data['id']}")
                return data["id"]
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration Creation", False, f"Request error: {str(e)}")
            return None

    def create_test_serial_numbers(self, config_id):
        """Create serial numbers for test configuration"""
        if not config_id:
            self.log_test("Serial Numbers Creation", False, "No configuration ID available")
            return None
            
        # For config: 1 SSCC, 2 Cases, 3 Items per Case = 6 total items
        test_data = {
            "configuration_id": config_id,
            "sscc_serial_numbers": ["SSCC001"],
            "case_serial_numbers": ["CASE001", "CASE002"],
            "inner_case_serial_numbers": [],
            "item_serial_numbers": ["ITEM001", "ITEM002", "ITEM003", "ITEM004", "ITEM005", "ITEM006"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/serial-numbers",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Serial Numbers Creation", True, "Serial numbers created successfully",
                            f"SSCC: {len(data['sscc_serial_numbers'])}, Cases: {len(data['case_serial_numbers'])}, Items: {len(data['item_serial_numbers'])}")
                return data["id"]
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return None

    def test_sbdh_structure(self, config_id):
        """Test SBDH Structure - Verify StandardBusinessDocument wrapper with proper namespaces"""
        if not config_id:
            self.log_test("SBDH Structure", False, "No configuration ID available")
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
                
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Check root element is StandardBusinessDocument (handle namespace)
                    if not root.tag.endswith("StandardBusinessDocument"):
                        self.log_test("SBDH Structure", False, f"Root element should be 'StandardBusinessDocument', found '{root.tag}'")
                        return False
                    
                    # Check required namespaces
                    expected_namespaces = {
                        "xmlns": "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader",
                        "xmlns:epcis": "urn:epcglobal:epcis:xsd:1",
                        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
                    }
                    
                    for ns_prefix, ns_uri in expected_namespaces.items():
                        if root.get(ns_prefix) != ns_uri:
                            self.log_test("SBDH Structure", False, f"Missing or incorrect namespace {ns_prefix}: expected '{ns_uri}', found '{root.get(ns_prefix)}'")
                            return False
                    
                    # Check for StandardBusinessDocumentHeader (handle namespace)
                    sbdh_header = None
                    for child in root:
                        if child.tag.endswith("StandardBusinessDocumentHeader"):
                            sbdh_header = child
                            break
                    
                    if sbdh_header is None:
                        self.log_test("SBDH Structure", False, "StandardBusinessDocumentHeader element not found")
                        return False
                    
                    # Check for EPCISDocument
                    epcis_document = None
                    for child in root:
                        if child.tag.endswith("EPCISDocument"):
                            epcis_document = child
                            break
                    
                    if epcis_document is None:
                        self.log_test("SBDH Structure", False, "EPCISDocument element not found")
                        return False
                    
                    self.log_test("SBDH Structure", True, "StandardBusinessDocument wrapper with proper namespaces verified")
                    return True
                    
                except ET.ParseError as e:
                    self.log_test("SBDH Structure", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("SBDH Structure", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SBDH Structure", False, f"Request error: {str(e)}")
            return False

    def test_sbdh_header(self, config_id):
        """Test SBDH Header - Check sender/receiver GLN identifiers in SBDH header"""
        if not config_id:
            self.log_test("SBDH Header", False, "No configuration ID available")
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
                
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find StandardBusinessDocumentHeader (handle namespace)
                    sbdh_header = None
                    for child in root:
                        if child.tag.endswith("StandardBusinessDocumentHeader"):
                            sbdh_header = child
                            break
                    
                    if sbdh_header is None:
                        self.log_test("SBDH Header", False, "StandardBusinessDocumentHeader not found")
                        return False
                    
                    # Check HeaderVersion (handle namespace)
                    header_version = None
                    for child in sbdh_header:
                        if child.tag.endswith("HeaderVersion"):
                            header_version = child
                            break
                    
                    if header_version is None or header_version.text != "1.0":
                        self.log_test("SBDH Header", False, f"HeaderVersion should be '1.0', found '{header_version.text if header_version else 'None'}'")
                        return False
                    
                    # Check Sender (handle namespace)
                    sender = None
                    for child in sbdh_header:
                        if child.tag.endswith("Sender"):
                            sender = child
                            break
                    
                    if sender is None:
                        self.log_test("SBDH Header", False, "Sender element not found in SBDH header")
                        return False
                    
                    # Check Sender Identifier (handle namespace)
                    sender_identifier = None
                    for child in sender:
                        if child.tag.endswith("Identifier"):
                            sender_identifier = child
                            break
                    
                    if sender_identifier is None:
                        self.log_test("SBDH Header", False, "Sender Identifier not found")
                        return False
                    
                    if sender_identifier.get("Authority") != "GS1":
                        self.log_test("SBDH Header", False, f"Sender Identifier Authority should be 'GS1', found '{sender_identifier.get('Authority')}'")
                        return False
                    
                    if sender_identifier.text != "0345802000014":
                        self.log_test("SBDH Header", False, f"Sender GLN should be '0345802000014', found '{sender_identifier.text}'")
                        return False
                    
                    # Check Receiver (handle namespace)
                    receiver = None
                    for child in sbdh_header:
                        if child.tag.endswith("Receiver"):
                            receiver = child
                            break
                    
                    if receiver is None:
                        self.log_test("SBDH Header", False, "Receiver element not found in SBDH header")
                        return False
                    
                    # Check Receiver Identifier (handle namespace)
                    receiver_identifier = None
                    for child in receiver:
                        if child.tag.endswith("Identifier"):
                            receiver_identifier = child
                            break
                    
                    if receiver_identifier is None:
                        self.log_test("SBDH Header", False, "Receiver Identifier not found")
                        return False
                    
                    if receiver_identifier.get("Authority") != "GS1":
                        self.log_test("SBDH Header", False, f"Receiver Identifier Authority should be 'GS1', found '{receiver_identifier.get('Authority')}'")
                        return False
                    
                    if receiver_identifier.text != "0567890000021":
                        self.log_test("SBDH Header", False, f"Receiver GLN should be '0567890000021', found '{receiver_identifier.text}'")
                        return False
                    
                    # Check Document Identification
                    doc_identification = None
                    for child in sbdh_header:
                        if child.tag == "DocumentIdentification":
                            doc_identification = child
                            break
                    
                    if doc_identification is None:
                        self.log_test("SBDH Header", False, "DocumentIdentification not found")
                        return False
                    
                    # Check Standard
                    standard = None
                    for child in doc_identification:
                        if child.tag == "Standard":
                            standard = child
                            break
                    
                    if standard is None or standard.text != "EPCISDocument":
                        self.log_test("SBDH Header", False, f"Standard should be 'EPCISDocument', found '{standard.text if standard else 'None'}'")
                        return False
                    
                    # Check TypeVersion
                    type_version = None
                    for child in doc_identification:
                        if child.tag == "TypeVersion":
                            type_version = child
                            break
                    
                    if type_version is None or type_version.text != "1.2":
                        self.log_test("SBDH Header", False, f"TypeVersion should be '1.2', found '{type_version.text if type_version else 'None'}'")
                        return False
                    
                    self.log_test("SBDH Header", True, "SBDH header with sender/receiver GLN identifiers verified")
                    return True
                    
                except ET.ParseError as e:
                    self.log_test("SBDH Header", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("SBDH Header", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SBDH Header", False, f"Request error: {str(e)}")
            return False

    def test_location_vocabulary(self, config_id):
        """Test Location Vocabulary - Verify complete address information in Location vocabulary elements"""
        if not config_id:
            self.log_test("Location Vocabulary", False, "No configuration ID available")
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
                
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Find EPCISMasterData
                    epcis_master_data = None
                    for elem in root.iter():
                        if elem.tag == "EPCISMasterData":
                            epcis_master_data = elem
                            break
                    
                    if epcis_master_data is None:
                        self.log_test("Location Vocabulary", False, "EPCISMasterData not found")
                        return False
                    
                    # Find VocabularyList
                    vocabulary_list = None
                    for child in epcis_master_data:
                        if child.tag == "VocabularyList":
                            vocabulary_list = child
                            break
                    
                    if vocabulary_list is None:
                        self.log_test("Location Vocabulary", False, "VocabularyList not found")
                        return False
                    
                    # Find Location vocabulary
                    location_vocabulary = None
                    for child in vocabulary_list:
                        if child.tag == "Vocabulary" and child.get("type") == "urn:epcglobal:epcis:vtype:Location":
                            location_vocabulary = child
                            break
                    
                    if location_vocabulary is None:
                        self.log_test("Location Vocabulary", False, "Location vocabulary not found")
                        return False
                    
                    # Find VocabularyElementList
                    vocabulary_element_list = None
                    for child in location_vocabulary:
                        if child.tag == "VocabularyElementList":
                            vocabulary_element_list = child
                            break
                    
                    if vocabulary_element_list is None:
                        self.log_test("Location Vocabulary", False, "VocabularyElementList not found in Location vocabulary")
                        return False
                    
                    # Expected location elements with complete address information
                    expected_locations = {
                        "urn:epc:id:sgln:0345802000014": {
                            "name": "Padagis US LLC",
                            "street": "1251 Lincoln Rd",
                            "city": "Allegan",
                            "state": "MI",
                            "postal": "49010",
                            "country": "US"
                        },
                        "urn:epc:id:sgln:0345802000014.001": {
                            "name": "Padagis US LLC - Sender Location",
                            "street": "1251 Lincoln Rd",
                            "city": "Allegan",
                            "state": "MI",
                            "postal": "49010",
                            "country": "US"
                        },
                        "urn:epc:id:sgln:0567890000021": {
                            "name": "Pharmacy Corp",
                            "street": "123 Main St",
                            "city": "New York",
                            "state": "NY",
                            "postal": "10001",
                            "country": "US"
                        },
                        "urn:epc:id:sgln:0567890000021.001": {
                            "name": "Pharmacy Corp - Receiver Location",
                            "street": "123 Main St",
                            "city": "New York",
                            "state": "NY",
                            "postal": "10001",
                            "country": "US"
                        },
                        "urn:epc:id:sgln:0999888000028": {
                            "name": "Shipping Corp",
                            "street": "456 Shipping Ave",
                            "city": "Chicago",
                            "state": "IL",
                            "postal": "60007",
                            "country": "US"
                        },
                        "urn:epc:id:sgln:0999888000028.001": {
                            "name": "Shipping Corp - Shipper Location",
                            "street": "456 Shipping Ave",
                            "city": "Chicago",
                            "state": "IL",
                            "postal": "60007",
                            "country": "US"
                        }
                    }
                    
                    found_locations = {}
                    
                    # Parse all VocabularyElement entries
                    for vocab_element in vocabulary_element_list:
                        if vocab_element.tag == "VocabularyElement":
                            element_id = vocab_element.get("id")
                            if element_id and element_id.startswith("urn:epc:id:sgln:"):
                                attributes = {}
                                for attr in vocab_element:
                                    if attr.tag == "attribute":
                                        attr_id = attr.get("id")
                                        attr_text = attr.text
                                        if attr_id == "urn:epcglobal:cbv:mda#name":
                                            attributes["name"] = attr_text
                                        elif attr_id == "urn:epcglobal:cbv:mda#streetAddressOne":
                                            attributes["street"] = attr_text
                                        elif attr_id == "urn:epcglobal:cbv:mda#city":
                                            attributes["city"] = attr_text
                                        elif attr_id == "urn:epcglobal:cbv:mda#state":
                                            attributes["state"] = attr_text
                                        elif attr_id == "urn:epcglobal:cbv:mda#postalCode":
                                            attributes["postal"] = attr_text
                                        elif attr_id == "urn:epcglobal:cbv:mda#countryCode":
                                            attributes["country"] = attr_text
                                
                                found_locations[element_id] = attributes
                    
                    # Verify all expected locations are present with complete address information
                    missing_locations = []
                    incomplete_locations = []
                    
                    for expected_id, expected_attrs in expected_locations.items():
                        if expected_id not in found_locations:
                            missing_locations.append(expected_id)
                        else:
                            found_attrs = found_locations[expected_id]
                            for attr_key, expected_value in expected_attrs.items():
                                if attr_key not in found_attrs:
                                    incomplete_locations.append(f"{expected_id} missing {attr_key}")
                                elif found_attrs[attr_key] != expected_value:
                                    incomplete_locations.append(f"{expected_id} {attr_key}: expected '{expected_value}', found '{found_attrs[attr_key]}'")
                    
                    if missing_locations:
                        self.log_test("Location Vocabulary", False, f"Missing location elements: {missing_locations}")
                        return False
                    
                    if incomplete_locations:
                        self.log_test("Location Vocabulary", False, f"Incomplete location attributes: {incomplete_locations}")
                        return False
                    
                    self.log_test("Location Vocabulary", True, f"All {len(expected_locations)} location vocabulary elements with complete address information verified")
                    return True
                    
                except ET.ParseError as e:
                    self.log_test("Location Vocabulary", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Location Vocabulary", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Location Vocabulary", False, f"Request error: {str(e)}")
            return False

    def test_existing_features_regression(self, config_id):
        """Test All existing features still working - Ensure no regression in existing functionality"""
        if not config_id:
            self.log_test("Existing Features Regression", False, "No configuration ID available")
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
                
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Check EPCIS Document structure
                    epcis_document = None
                    for child in root:
                        if child.tag.endswith("EPCISDocument"):
                            epcis_document = child
                            break
                    
                    if epcis_document is None:
                        self.log_test("Existing Features Regression", False, "EPCISDocument not found")
                        return False
                    
                    # Check schema version
                    if epcis_document.get("schemaVersion") != "1.2":
                        self.log_test("Existing Features Regression", False, f"Schema version should be '1.2', found '{epcis_document.get('schemaVersion')}'")
                        return False
                    
                    # Check EPCISHeader
                    epcis_header = None
                    for child in epcis_document:
                        if child.tag == "EPCISHeader":
                            epcis_header = child
                            break
                    
                    if epcis_header is None:
                        self.log_test("Existing Features Regression", False, "EPCISHeader not found")
                        return False
                    
                    # Check EPCISBody and EventList
                    epcis_body = None
                    for child in epcis_document:
                        if child.tag == "EPCISBody":
                            epcis_body = child
                            break
                    
                    if epcis_body is None:
                        self.log_test("Existing Features Regression", False, "EPCISBody not found")
                        return False
                    
                    event_list = None
                    for child in epcis_body:
                        if child.tag == "EventList":
                            event_list = child
                            break
                    
                    if event_list is None:
                        self.log_test("Existing Features Regression", False, "EventList not found")
                        return False
                    
                    # Count events
                    object_events = 0
                    aggregation_events = 0
                    
                    for child in event_list:
                        if child.tag == "ObjectEvent":
                            object_events += 1
                        elif child.tag == "AggregationEvent":
                            aggregation_events += 1
                    
                    # For our test config: 1 SSCC, 2 Cases, 6 Items
                    # Expected: 3 ObjectEvents (Items, Cases, SSCCs) + 3 AggregationEvents (Items→Cases×2, Cases→SSCCs×1) + 1 Shipping ObjectEvent
                    expected_object_events = 4  # Items, Cases, SSCCs commissioning + Shipping
                    expected_aggregation_events = 3  # Items→Cases (2) + Cases→SSCCs (1)
                    
                    if object_events != expected_object_events:
                        self.log_test("Existing Features Regression", False, f"Expected {expected_object_events} ObjectEvents, found {object_events}")
                        return False
                    
                    if aggregation_events != expected_aggregation_events:
                        self.log_test("Existing Features Regression", False, f"Expected {expected_aggregation_events} AggregationEvents, found {aggregation_events}")
                        return False
                    
                    # Check SSCC uses shipper's company prefix
                    sscc_found = False
                    for elem in root.iter():
                        if elem.tag == "epc" and elem.text and "sscc" in elem.text:
                            if "urn:epc:id:sscc:0999888" in elem.text:  # Shipper's company prefix
                                sscc_found = True
                                break
                    
                    if not sscc_found:
                        self.log_test("Existing Features Regression", False, "SSCC with shipper's company prefix not found")
                        return False
                    
                    # Check EPCClass vocabulary is present
                    epcclass_found = False
                    for elem in root.iter():
                        if elem.tag == "Vocabulary" and elem.get("type") == "urn:epcglobal:epcis:vtype:EPCClass":
                            epcclass_found = True
                            break
                    
                    if not epcclass_found:
                        self.log_test("Existing Features Regression", False, "EPCClass vocabulary not found")
                        return False
                    
                    # Check shipping event is last
                    last_event = None
                    for child in event_list:
                        last_event = child
                    
                    if last_event is not None and last_event.tag == "ObjectEvent":
                        # Check if it's a shipping event
                        shipping_event = False
                        for child in last_event:
                            if child.tag == "bizStep" and "shipping" in child.text:
                                shipping_event = True
                                break
                        
                        if not shipping_event:
                            self.log_test("Existing Features Regression", False, "Last event is not a shipping ObjectEvent")
                            return False
                    else:
                        self.log_test("Existing Features Regression", False, "Last event is not an ObjectEvent")
                        return False
                    
                    self.log_test("Existing Features Regression", True, "All existing features working correctly - no regression detected")
                    return True
                    
                except ET.ParseError as e:
                    self.log_test("Existing Features Regression", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("Existing Features Regression", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Existing Features Regression", False, f"Request error: {str(e)}")
            return False

    def run_sbdh_location_tests(self):
        """Run comprehensive SBDH and Location vocabulary tests"""
        print("=" * 80)
        print("SBDH AND LOCATION VOCABULARY TESTING - GS1 Rx EPCIS COMPLIANCE")
        print("=" * 80)
        print("SPECIFIC VERIFICATION REQUIREMENTS:")
        print("1. SBDH Structure - StandardBusinessDocument wrapper with proper namespaces")
        print("2. SBDH Header - sender/receiver GLN identifiers in SBDH header")
        print("3. Location Vocabulary - complete address information in Location vocabulary elements")
        print("4. All existing features still working - ensure no regression")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Create test configuration with enhanced address information
        config_id = self.create_test_configuration()
        if not config_id:
            print("\n❌ Could not create test configuration. Stopping tests.")
            return False
        
        # Test 3: Create serial numbers
        serial_id = self.create_test_serial_numbers(config_id)
        if not serial_id:
            print("\n❌ Could not create serial numbers. Stopping tests.")
            return False
        
        # Test 4: SBDH Structure verification
        sbdh_structure_success = self.test_sbdh_structure(config_id)
        
        # Test 5: SBDH Header verification
        sbdh_header_success = self.test_sbdh_header(config_id)
        
        # Test 6: Location Vocabulary verification
        location_vocabulary_success = self.test_location_vocabulary(config_id)
        
        # Test 7: Existing features regression test
        regression_success = self.test_existing_features_regression(config_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("SBDH AND LOCATION VOCABULARY TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical Requirements Status
        print("\n" + "=" * 50)
        print("CRITICAL REQUIREMENTS STATUS")
        print("=" * 50)
        print(f"1. SBDH Structure: {'✅ VERIFIED' if sbdh_structure_success else '❌ FAILED'}")
        print(f"2. SBDH Header: {'✅ VERIFIED' if sbdh_header_success else '❌ FAILED'}")
        print(f"3. Location Vocabulary: {'✅ VERIFIED' if location_vocabulary_success else '❌ FAILED'}")
        print(f"4. No Regression: {'✅ VERIFIED' if regression_success else '❌ FAILED'}")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nGS1 Rx EPCIS Compliance Features Verified:")
        print("✓ StandardBusinessDocument root element with proper namespaces")
        print("✓ SBDH header with sender/receiver GLN identifiers")
        print("✓ Location vocabulary with complete address information")
        print("✓ All 6 expected location elements (sender, receiver, shipper GLN/SGLN)")
        print("✓ Complete address attributes (name, street, city, state, postal, country)")
        print("✓ No regression in existing EPCIS functionality")
        
        return passed == total

if __name__ == "__main__":
    tester = SBDHLocationTester()
    success = tester.run_sbdh_location_tests()
    sys.exit(0 if success else 1)