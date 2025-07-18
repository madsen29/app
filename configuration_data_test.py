#!/usr/bin/env python3
"""
Configuration Data Population Testing for EPCIS Generation
Tests the critical user-reported issue: "Configuration data isn't populating correctly in the generated EPCIS file"

Focus Areas:
1. Complete workflow: User → Project → Configuration → Serial Numbers → EPCIS Generation
2. Verify all configuration fields are properly populated in generated EPCIS XML
3. Check POST /api/projects/{project_id}/generate-epcis endpoint specifically
4. Validate configuration data from project is correctly passed to generate_epcis_xml function
5. Test different types of configuration data:
   - Business Document Information (sender, receiver, shipper details)
   - Product Information (company prefix, product codes, lot number, expiration date)
   - GS1 Indicator Digits (SSCC, case, inner case, item indicator digits)
   - EPCClass data (package NDC, regulated product name, manufacturer, etc.)
   - Packaging Configuration (number of SSCCs, cases per SSCC, items per case, etc.)

Test Scenarios:
- Create test project with comprehensive configuration data
- Add serial numbers to the project
- Generate EPCIS XML and verify all configuration fields are populated correctly
- Pay special attention to get_config_value helper function and field mapping
- Check for missing or empty configuration fields in generated XML
- Verify business document information appears in SBDH section
- Confirm EPCClass data appears in vocabulary elements
- Ensure location vocabulary contains complete address information
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

class ConfigurationDataTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None
        
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
    
    def setup_test_user(self):
        """Create and authenticate a test user"""
        # Create test user
        user_data = {
            "email": f"configtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
            "password": "TestPassword123!",
            "firstName": "Config",
            "lastName": "Tester",
            "companyName": "Test Company",
            "streetAddress": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "postalCode": "12345",
            "countryCode": "US"
        }
        
        try:
            # Register user
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                user_info = response.json()
                self.test_user_id = user_info["id"]
                
                # Login to get token
                login_response = self.session.post(
                    f"{self.base_url}/auth/login",
                    json={"email": user_data["email"], "password": user_data["password"]},
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.auth_token = token_data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("User Setup", True, f"Test user created and authenticated: {user_data['email']}")
                    return True
                else:
                    self.log_test("User Setup", False, f"Login failed: {login_response.status_code}")
                    return False
            else:
                self.log_test("User Setup", False, f"User registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Setup", False, f"Setup error: {str(e)}")
            return False
    
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
    
    def create_comprehensive_test_project(self):
        """Create a test project with comprehensive configuration data"""
        project_data = {
            "name": f"Configuration Test Project - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                self.log_test("Project Creation", True, f"Test project created: {project['name']}", f"Project ID: {project['id']}")
                return project["id"]
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Request error: {str(e)}")
            return None
    
    def create_comprehensive_configuration(self, project_id):
        """Create comprehensive configuration with all possible fields"""
        if not project_id:
            self.log_test("Configuration Creation", False, "No project ID available")
            return None
        
        # Comprehensive configuration with all field categories
        config_data = {
            # Basic Configuration
            "itemsPerCase": 2,
            "casesPerSscc": 1,
            "numberOfSscc": 1,
            "useInnerCases": False,
            
            # Company/Product Information
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000001",
            "lotNumber": "LOT123456",
            "expirationDate": "2026-12-31",
            
            # GS1 Indicator Digits
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            
            # Business Document Information - Sender
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "senderName": "Padagis US LLC",
            "senderStreetAddress": "420 Saw Mill River Road",
            "senderCity": "Ardsley",
            "senderState": "NY",
            "senderPostalCode": "10502",
            "senderCountryCode": "US",
            "senderDespatchAdviceNumber": "DA123456",
            
            # Business Document Information - Receiver
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Pharmacy Corp",
            "receiverStreetAddress": "789 Main Street",
            "receiverCity": "Anytown",
            "receiverState": "CA",
            "receiverPostalCode": "90210",
            "receiverCountryCode": "US",
            "receiverPoNumber": "PO789012",
            
            # Business Document Information - Shipper
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Shipping Corp",
            "shipperStreetAddress": "456 Logistics Ave",
            "shipperCity": "Distribution Center",
            "shipperState": "TX",
            "shipperPostalCode": "75001",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False,
            
            # EPCClass Data
            "productNdc": "45802-046-85",
            "packageNdc": "45802-046-85",
            "regulatedProductName": "Metformin Hydrochloride Tablets",
            "manufacturerName": "Padagis US LLC",
            "dosageFormType": "Tablet",
            "strengthDescription": "500 mg",
            "netContentDescription": "100 tablets"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                config = response.json()
                self.log_test("Configuration Creation", True, "Comprehensive configuration created with all field categories", 
                            f"Config ID: {config['id']}")
                return config
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration Creation", False, f"Request error: {str(e)}")
            return None
    
    def create_test_serial_numbers(self, project_id):
        """Create serial numbers for the test configuration"""
        if not project_id:
            self.log_test("Serial Numbers Creation", False, "No project ID available")
            return None
        
        # For config: 1 SSCC, 1 Case, 2 Items
        serial_data = {
            "ssccSerialNumbers": ["TEST001"],
            "caseSerialNumbers": ["CASE001"],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": ["ITEM001", "ITEM002"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                serials = response.json()
                self.log_test("Serial Numbers Creation", True, "Serial numbers created successfully", 
                            f"SSCC: {len(serials['sscc_serial_numbers'])}, Cases: {len(serials['case_serial_numbers'])}, Items: {len(serials['item_serial_numbers'])}")
                return serials
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            return None
    
    def test_epcis_generation_configuration_population(self, project_id):
        """Test EPCIS generation and verify all configuration data is properly populated"""
        if not project_id:
            self.log_test("EPCIS Configuration Population", False, "No project ID available")
            return False
        
        epcis_request = {
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json=epcis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Parse XML for detailed analysis
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Test all configuration field categories
                    results = {
                        "sbdh_business_document": self.verify_sbdh_business_document_info(root),
                        "location_vocabulary": self.verify_location_vocabulary(root),
                        "epcclass_vocabulary": self.verify_epcclass_vocabulary(root),
                        "gs1_identifiers": self.verify_gs1_identifiers(root),
                        "ilmd_extensions": self.verify_ilmd_extensions(root),
                        "event_structure": self.verify_event_structure(root)
                    }
                    
                    # Count successful verifications
                    successful_verifications = sum(1 for success in results.values() if success)
                    total_verifications = len(results)
                    
                    if successful_verifications == total_verifications:
                        self.log_test("EPCIS Configuration Population", True, 
                                    f"All configuration data properly populated in EPCIS XML ({successful_verifications}/{total_verifications})")
                        return True
                    else:
                        failed_categories = [category for category, success in results.items() if not success]
                        self.log_test("EPCIS Configuration Population", False, 
                                    f"Configuration data missing or incorrect in EPCIS XML ({successful_verifications}/{total_verifications})",
                                    f"Failed categories: {', '.join(failed_categories)}")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("EPCIS Configuration Population", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("EPCIS Configuration Population", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("EPCIS Configuration Population", False, f"Request error: {str(e)}")
            return False
    
    def verify_sbdh_business_document_info(self, root):
        """Verify SBDH contains business document information"""
        try:
            # Find SBDH header
            sbdh_found = False
            sender_gln_found = False
            receiver_gln_found = False
            
            for elem in root.iter():
                if elem.tag.endswith("StandardBusinessDocumentHeader"):
                    sbdh_found = True
                elif elem.tag.endswith("Sender"):
                    for child in elem:
                        if child.tag.endswith("Identifier") and child.text == "0345802000014":
                            sender_gln_found = True
                elif elem.tag.endswith("Receiver"):
                    for child in elem:
                        if child.tag.endswith("Identifier") and child.text == "0567890000021":
                            receiver_gln_found = True
            
            success = sbdh_found and sender_gln_found and receiver_gln_found
            if success:
                print("   ✓ SBDH Business Document Information: All sender/receiver GLNs found")
            else:
                print(f"   ❌ SBDH Business Document Information: SBDH={sbdh_found}, Sender GLN={sender_gln_found}, Receiver GLN={receiver_gln_found}")
            
            return success
            
        except Exception as e:
            print(f"   ❌ SBDH verification error: {str(e)}")
            return False
    
    def verify_location_vocabulary(self, root):
        """Verify location vocabulary contains complete address information"""
        try:
            location_elements_found = 0
            expected_locations = [
                "0345802000014.001",  # sender_sgln
                "0567890000021.001",  # receiver_sgln
                "0999888000028.001"   # shipper_sgln
            ]
            
            address_attributes_found = 0
            expected_attributes = ["name", "streetAddressOne", "city", "state", "postalCode", "countryCode"]
            
            for elem in root.iter():
                if elem.tag.endswith("VocabularyElement"):
                    element_id = elem.get("id", "")
                    if any(location in element_id for location in expected_locations):
                        location_elements_found += 1
                        
                        # Check for address attributes
                        for attr_elem in elem:
                            if attr_elem.tag.endswith("attribute"):
                                attr_id = attr_elem.get("id", "")
                                if any(attr in attr_id for attr in expected_attributes):
                                    address_attributes_found += 1
            
            success = location_elements_found >= 3 and address_attributes_found >= 6
            if success:
                print(f"   ✓ Location Vocabulary: {location_elements_found} location elements with {address_attributes_found} address attributes")
            else:
                print(f"   ❌ Location Vocabulary: {location_elements_found} location elements, {address_attributes_found} address attributes")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Location vocabulary verification error: {str(e)}")
            return False
    
    def verify_epcclass_vocabulary(self, root):
        """Verify EPCClass vocabulary contains product information"""
        try:
            epcclass_elements_found = 0
            package_ndc_found = False
            regulated_product_name_found = False
            manufacturer_found = False
            
            for elem in root.iter():
                if elem.tag.endswith("VocabularyElement"):
                    element_id = elem.get("id", "")
                    if "urn:epc:idpat:sgtin:" in element_id:
                        epcclass_elements_found += 1
                        
                        # Check for EPCClass attributes
                        for attr_elem in elem:
                            if attr_elem.tag.endswith("attribute"):
                                attr_id = attr_elem.get("id", "")
                                attr_text = attr_elem.text or ""
                                
                                if "additionalTradeItemIdentification" in attr_id and "4580204685" in attr_text:
                                    package_ndc_found = True
                                elif "regulatedProductName" in attr_id and "Metformin" in attr_text:
                                    regulated_product_name_found = True
                                elif "manufacturerOfTradeItemPartyName" in attr_id and "Padagis" in attr_text:
                                    manufacturer_found = True
            
            success = epcclass_elements_found >= 2 and package_ndc_found and regulated_product_name_found and manufacturer_found
            if success:
                print(f"   ✓ EPCClass Vocabulary: {epcclass_elements_found} elements with product information")
            else:
                print(f"   ❌ EPCClass Vocabulary: {epcclass_elements_found} elements, NDC={package_ndc_found}, Product={regulated_product_name_found}, Manufacturer={manufacturer_found}")
            
            return success
            
        except Exception as e:
            print(f"   ❌ EPCClass vocabulary verification error: {str(e)}")
            return False
    
    def verify_gs1_identifiers(self, root):
        """Verify GS1 identifiers use correct company prefixes and indicator digits"""
        try:
            sscc_correct = False
            case_sgtin_correct = False
            item_sgtin_correct = False
            
            for elem in root.iter():
                if elem.tag.endswith("epc") or elem.tag.endswith("parentID"):
                    epc_text = elem.text or ""
                    
                    # Check SSCC uses shipper company prefix
                    if "urn:epc:id:sscc:0999888.3TEST001" in epc_text:
                        sscc_correct = True
                    # Check Case SGTIN uses correct format
                    elif "urn:epc:id:sgtin:1234567.2000001.CASE001" in epc_text:
                        case_sgtin_correct = True
                    # Check Item SGTIN uses correct format
                    elif "urn:epc:id:sgtin:1234567.1000000.ITEM001" in epc_text or "urn:epc:id:sgtin:1234567.1000000.ITEM002" in epc_text:
                        item_sgtin_correct = True
            
            success = sscc_correct and case_sgtin_correct and item_sgtin_correct
            if success:
                print("   ✓ GS1 Identifiers: All identifiers use correct company prefixes and indicator digits")
            else:
                print(f"   ❌ GS1 Identifiers: SSCC={sscc_correct}, Case SGTIN={case_sgtin_correct}, Item SGTIN={item_sgtin_correct}")
            
            return success
            
        except Exception as e:
            print(f"   ❌ GS1 identifiers verification error: {str(e)}")
            return False
    
    def verify_ilmd_extensions(self, root):
        """Verify ILMD extensions contain lot number and expiration date"""
        try:
            lot_number_found = False
            expiration_date_found = False
            
            for elem in root.iter():
                if elem.tag.endswith("lotNumber") and elem.text == "LOT123456":
                    lot_number_found = True
                elif elem.tag.endswith("itemExpirationDate") and elem.text == "2026-12-31":
                    expiration_date_found = True
            
            success = lot_number_found and expiration_date_found
            if success:
                print("   ✓ ILMD Extensions: Lot number and expiration date found in commissioning events")
            else:
                print(f"   ❌ ILMD Extensions: Lot number={lot_number_found}, Expiration date={expiration_date_found}")
            
            return success
            
        except Exception as e:
            print(f"   ❌ ILMD extensions verification error: {str(e)}")
            return False
    
    def verify_event_structure(self, root):
        """Verify event structure is correct for the configuration"""
        try:
            object_events = 0
            aggregation_events = 0
            shipping_events = 0
            
            for elem in root.iter():
                if elem.tag.endswith("ObjectEvent"):
                    object_events += 1
                    # Check if it's a shipping event
                    for child in elem:
                        if child.tag.endswith("bizStep") and "shipping" in child.text:
                            shipping_events += 1
                elif elem.tag.endswith("AggregationEvent"):
                    aggregation_events += 1
            
            # Expected for 1 SSCC, 1 Case, 2 Items:
            # 3 ObjectEvents (Items, Cases, SSCCs commissioning) + 1 Shipping ObjectEvent = 4 total
            # 2 AggregationEvents (Items→Case, Case→SSCC)
            expected_object_events = 4  # Including shipping event
            expected_aggregation_events = 2
            expected_shipping_events = 1
            
            success = (object_events == expected_object_events and 
                      aggregation_events == expected_aggregation_events and
                      shipping_events == expected_shipping_events)
            
            if success:
                print(f"   ✓ Event Structure: {object_events} ObjectEvents (including {shipping_events} shipping), {aggregation_events} AggregationEvents")
            else:
                print(f"   ❌ Event Structure: {object_events} ObjectEvents (expected {expected_object_events}), {aggregation_events} AggregationEvents (expected {expected_aggregation_events}), {shipping_events} shipping events (expected {expected_shipping_events})")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Event structure verification error: {str(e)}")
            return False
    
    def test_configuration_field_mapping(self, project_id):
        """Test that get_config_value helper function properly maps camelCase/snake_case fields"""
        if not project_id:
            self.log_test("Configuration Field Mapping", False, "No project ID available")
            return False
        
        try:
            # Get project to check configuration storage
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                project = response.json()
                config = project.get("configuration", {})
                
                # Check that both camelCase and snake_case fields are accessible
                field_mappings = [
                    ("numberOfSscc", "number_of_sscc", 1),
                    ("itemsPerCase", "items_per_case", 2),
                    ("casesPerSscc", "cases_per_sscc", 1),
                    ("companyPrefix", "company_prefix", "1234567"),
                    ("senderGln", "sender_gln", "0345802000014"),
                    ("packageNdc", "package_ndc", "45802-046-85")
                ]
                
                mapping_success = True
                for camel_key, snake_key, expected_value in field_mappings:
                    camel_value = config.get(camel_key)
                    snake_value = config.get(snake_key)
                    
                    if camel_value != expected_value and snake_value != expected_value:
                        print(f"   ❌ Field mapping failed for {camel_key}/{snake_key}: camel={camel_value}, snake={snake_value}, expected={expected_value}")
                        mapping_success = False
                
                if mapping_success:
                    self.log_test("Configuration Field Mapping", True, "All configuration fields properly stored and accessible")
                    return True
                else:
                    self.log_test("Configuration Field Mapping", False, "Some configuration fields not properly mapped")
                    return False
            else:
                self.log_test("Configuration Field Mapping", False, f"Failed to retrieve project: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Field Mapping", False, f"Request error: {str(e)}")
            return False
    
    def run_configuration_data_tests(self):
        """Run comprehensive configuration data population tests"""
        print("=" * 80)
        print("CONFIGURATION DATA POPULATION TESTING")
        print("=" * 80)
        print("USER REPORTED ISSUE: Configuration data isn't populating correctly in the generated EPCIS file")
        print("Testing Focus Areas:")
        print("1. Complete workflow: User → Project → Configuration → Serial Numbers → EPCIS Generation")
        print("2. Business Document Information (sender, receiver, shipper details)")
        print("3. Product Information (company prefix, product codes, lot number, expiration date)")
        print("4. GS1 Indicator Digits (SSCC, case, inner case, item indicator digits)")
        print("5. EPCClass data (package NDC, regulated product name, manufacturer, etc.)")
        print("6. Packaging Configuration (number of SSCCs, cases per SSCC, items per case, etc.)")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Setup test user
        if not self.setup_test_user():
            print("\n❌ Failed to setup test user. Stopping tests.")
            return False
        
        # Test 3: Create test project
        project_id = self.create_comprehensive_test_project()
        if not project_id:
            print("\n❌ Failed to create test project. Stopping tests.")
            return False
        
        # Test 4: Create comprehensive configuration
        config = self.create_comprehensive_configuration(project_id)
        if not config:
            print("\n❌ Failed to create configuration. Stopping tests.")
            return False
        
        # Test 5: Test configuration field mapping
        self.test_configuration_field_mapping(project_id)
        
        # Test 6: Create serial numbers
        serials = self.create_test_serial_numbers(project_id)
        if not serials:
            print("\n❌ Failed to create serial numbers. Stopping tests.")
            return False
        
        # Test 7: Test EPCIS generation and configuration population
        epcis_success = self.test_epcis_generation_configuration_population(project_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("CONFIGURATION DATA POPULATION TEST SUMMARY")
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
                    if result['details']:
                        print(f"    Details: {result['details']}")
        
        print("\nConfiguration Data Categories Tested:")
        print("✓ Business Document Information (SBDH)")
        print("✓ Location Vocabulary (sender, receiver, shipper addresses)")
        print("✓ EPCClass Vocabulary (product information)")
        print("✓ GS1 Identifiers (company prefixes, indicator digits)")
        print("✓ ILMD Extensions (lot number, expiration date)")
        print("✓ Event Structure (commissioning, aggregation, shipping)")
        print("✓ Configuration Field Mapping (camelCase/snake_case)")
        
        # Critical issue status
        print(f"\nCRITICAL ISSUE STATUS: {'✅ RESOLVED' if epcis_success else '❌ CONFIGURATION DATA NOT POPULATING CORRECTLY'}")
        
        return passed == total

if __name__ == "__main__":
    tester = ConfigurationDataTester()
    success = tester.run_configuration_data_tests()
    sys.exit(0 if success else 1)