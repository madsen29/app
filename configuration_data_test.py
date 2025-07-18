#!/usr/bin/env python3
"""
Configuration Data Population Testing for EPCIS XML Generation
Tests the specific issues mentioned in the review request:
1. Location vocabulary not showing up
2. GLNs on Authority not showing up
3. Indicator digits not showing up
4. Product Code showing 'None' when there should be a value

Focus on testing the camelCase vs snake_case field mapping fixes in generate_epcis_xml function.
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
        self.user_token = None
        self.project_id = None
        
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
    
    def create_test_user_and_login(self):
        """Create a test user and login to get authentication token"""
        # Create user
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
            
            if response.status_code != 200:
                self.log_test("User Registration", False, f"Registration failed: {response.status_code} - {response.text}")
                return False
            
            # Login
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.user_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.user_token}"})
                self.log_test("User Authentication", True, "User created and authenticated successfully")
                return True
            else:
                self.log_test("User Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def create_test_project(self):
        """Create a test project"""
        try:
            project_data = {
                "name": f"Configuration Data Test Project - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                self.project_id = project["id"]
                self.log_test("Project Creation", True, f"Project created successfully", f"Project ID: {self.project_id}")
                return True
            else:
                self.log_test("Project Creation", False, f"Project creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Project creation error: {str(e)}")
            return False
    
    def test_comprehensive_configuration_creation(self):
        """Create configuration with ALL fields that should populate in EPCIS XML"""
        if not self.project_id:
            self.log_test("Comprehensive Configuration", False, "No project ID available")
            return False
            
        # Comprehensive configuration with all fields mentioned in review request
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
            "senderStreetAddress": "2400 Pilot Knob Road",
            "senderCity": "Mendota Heights",
            "senderState": "MN",
            "senderPostalCode": "55120",
            "senderCountryCode": "US",
            "senderDespatchAdviceNumber": "DA123456",
            
            # Business Document Information - Receiver
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Pharmacy Corp",
            "receiverStreetAddress": "456 Pharmacy Ave",
            "receiverCity": "Healthcare City",
            "receiverState": "CA",
            "receiverPostalCode": "90210",
            "receiverCountryCode": "US",
            "receiverPoNumber": "PO789012",
            
            # Business Document Information - Shipper
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Shipping Corp",
            "shipperStreetAddress": "789 Logistics Blvd",
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
                f"{self.base_url}/projects/{self.project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                config = response.json()
                self.log_test("Comprehensive Configuration", True, "Configuration created with all fields", 
                            f"Configuration includes: GLNs, Company Prefixes, Product Codes, Indicator Digits, EPCClass data")
                return True
            else:
                self.log_test("Comprehensive Configuration", False, f"Configuration creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Comprehensive Configuration", False, f"Configuration creation error: {str(e)}")
            return False
    
    def test_serial_numbers_creation(self):
        """Create serial numbers for the configuration"""
        if not self.project_id:
            self.log_test("Serial Numbers Creation", False, "No project ID available")
            return False
            
        # For config: 1 SSCC, 1 Case, 2 Items
        serial_data = {
            "ssccSerialNumbers": ["TEST001"],
            "caseSerialNumbers": ["CASE001"],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": ["ITEM001", "ITEM002"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                serials = response.json()
                # Check for both possible field name formats
                sscc_count = len(serials.get('sscc_serial_numbers', serials.get('ssccSerialNumbers', [])))
                case_count = len(serials.get('case_serial_numbers', serials.get('caseSerialNumbers', [])))
                item_count = len(serials.get('item_serial_numbers', serials.get('itemSerialNumbers', [])))
                
                self.log_test("Serial Numbers Creation", True, "Serial numbers created successfully",
                            f"SSCCs: {sscc_count}, Cases: {case_count}, Items: {item_count}")
                return True
            else:
                self.log_test("Serial Numbers Creation", False, f"Serial numbers creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Serial numbers creation error: {str(e)}")
            return False
    
    def test_epcis_generation_and_configuration_data_population(self):
        """Generate EPCIS XML and test all configuration data population issues"""
        if not self.project_id:
            self.log_test("EPCIS Generation", False, "No project ID available")
            return False
            
        epcis_data = {
            "readPoint": "urn:epc:id:sgln:0999888000028.001",
            "bizLocation": "urn:epc:id:sgln:0999888000028.001"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.project_id}/generate-epcis",
                json=epcis_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                self.log_test("EPCIS Generation", True, "EPCIS XML generated successfully")
                
                # Now test all the specific configuration data population issues
                return self.analyze_configuration_data_population(xml_content)
            else:
                self.log_test("EPCIS Generation", False, f"EPCIS generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("EPCIS Generation", False, f"EPCIS generation error: {str(e)}")
            return False
    
    def analyze_configuration_data_population(self, xml_content):
        """Analyze the EPCIS XML for all configuration data population issues"""
        try:
            root = ET.fromstring(xml_content)
            
            # Test 1: GLNs on Authority not showing up
            gln_authority_test = self.test_gln_authority_population(root)
            
            # Test 2: Location vocabulary not showing up
            location_vocab_test = self.test_location_vocabulary_population(root)
            
            # Test 3: Indicator digits not showing up
            indicator_digits_test = self.test_indicator_digits_population(root)
            
            # Test 4: Product Code showing 'None' when there should be a value
            product_code_test = self.test_product_code_population(root)
            
            # Test 5: EPCClass data population
            epcclass_data_test = self.test_epcclass_data_population(root)
            
            # Test 6: ILMD extensions (lot number and expiration date)
            ilmd_test = self.test_ilmd_extensions_population(root)
            
            # Test 7: Event structure and counts
            event_structure_test = self.test_event_structure(root)
            
            all_tests_passed = all([
                gln_authority_test,
                location_vocab_test,
                indicator_digits_test,
                product_code_test,
                epcclass_data_test,
                ilmd_test,
                event_structure_test
            ])
            
            return all_tests_passed
            
        except ET.ParseError as e:
            self.log_test("XML Analysis", False, f"XML parsing error: {str(e)}")
            return False
        except Exception as e:
            self.log_test("XML Analysis", False, f"Analysis error: {str(e)}")
            return False
    
    def test_gln_authority_population(self, root):
        """Test Issue 1: GLNs on Authority not showing up"""
        try:
            # Look for SBDH sender and receiver with Authority="GS1"
            sender_found = False
            receiver_found = False
            sender_gln = None
            receiver_gln = None
            
            for elem in root.iter():
                if elem.tag.endswith("Sender"):
                    for identifier in elem.iter():
                        if identifier.tag.endswith("Identifier"):
                            authority = identifier.get("Authority")
                            if authority == "GS1":
                                sender_gln = identifier.text
                                sender_found = True
                                break
                elif elem.tag.endswith("Receiver"):
                    for identifier in elem.iter():
                        if identifier.tag.endswith("Identifier"):
                            authority = identifier.get("Authority")
                            if authority == "GS1":
                                receiver_gln = identifier.text
                                receiver_found = True
                                break
            
            if sender_found and receiver_found and sender_gln and receiver_gln:
                if sender_gln == "0345802000014" and receiver_gln == "0567890000021":
                    self.log_test("GLN Authority Population", True, "GLNs with Authority='GS1' found correctly",
                                f"Sender GLN: {sender_gln}, Receiver GLN: {receiver_gln}")
                    return True
                else:
                    self.log_test("GLN Authority Population", False, f"GLN values incorrect - Sender: {sender_gln}, Receiver: {receiver_gln}")
                    return False
            else:
                self.log_test("GLN Authority Population", False, "GLNs with Authority='GS1' not found in SBDH")
                return False
                
        except Exception as e:
            self.log_test("GLN Authority Population", False, f"Error checking GLN Authority: {str(e)}")
            return False
    
    def test_location_vocabulary_population(self, root):
        """Test Issue 2: Location vocabulary not showing up"""
        try:
            # Look for Location vocabulary elements
            location_vocab_found = False
            location_elements = []
            
            for elem in root.iter():
                if elem.tag.endswith("Vocabulary") and elem.get("type") == "urn:epcglobal:epcis:vtype:Location":
                    location_vocab_found = True
                    # Count vocabulary elements
                    for vocab_elem in elem.iter():
                        if vocab_elem.tag.endswith("VocabularyElement"):
                            location_id = vocab_elem.get("id")
                            if location_id:
                                location_elements.append(location_id)
            
            # Should have 3 location elements: sender, receiver, shipper
            expected_locations = [
                "urn:epc:id:sgln:0345802000014.001",  # sender
                "urn:epc:id:sgln:0567890000021.001",  # receiver
                "urn:epc:id:sgln:0999888000028.001"   # shipper
            ]
            
            if location_vocab_found and len(location_elements) >= 3:
                # Check if expected locations are present
                locations_match = all(loc in location_elements for loc in expected_locations)
                if locations_match:
                    self.log_test("Location Vocabulary Population", True, "Location vocabulary elements found correctly",
                                f"Found {len(location_elements)} location elements: {location_elements}")
                    return True
                else:
                    self.log_test("Location Vocabulary Population", False, f"Expected locations not found. Expected: {expected_locations}, Found: {location_elements}")
                    return False
            else:
                self.log_test("Location Vocabulary Population", False, f"Location vocabulary not found or insufficient elements. Found: {len(location_elements)} elements")
                return False
                
        except Exception as e:
            self.log_test("Location Vocabulary Population", False, f"Error checking location vocabulary: {str(e)}")
            return False
    
    def test_indicator_digits_population(self, root):
        """Test Issue 3: Indicator digits not showing up"""
        try:
            # Look for EPC identifiers with correct indicator digits
            sscc_found = False
            case_sgtin_found = False
            item_sgtin_found = False
            
            for elem in root.iter():
                if elem.tag.endswith("epc") or elem.tag.endswith("parentID"):
                    epc_text = elem.text
                    if epc_text:
                        # Check SSCC with indicator digit 3
                        if "urn:epc:id:sscc:0999888.3TEST001" in epc_text:
                            sscc_found = True
                        # Check Case SGTIN with indicator digit 2
                        elif "urn:epc:id:sgtin:1234567.2000001." in epc_text:
                            case_sgtin_found = True
                        # Check Item SGTIN with indicator digit 1
                        elif "urn:epc:id:sgtin:1234567.1000000." in epc_text:
                            item_sgtin_found = True
            
            if sscc_found and case_sgtin_found and item_sgtin_found:
                self.log_test("Indicator Digits Population", True, "All indicator digits found correctly in EPCs",
                            "SSCC (3), Case SGTIN (2), Item SGTIN (1)")
                return True
            else:
                missing = []
                if not sscc_found: missing.append("SSCC indicator digit 3")
                if not case_sgtin_found: missing.append("Case indicator digit 2")
                if not item_sgtin_found: missing.append("Item indicator digit 1")
                self.log_test("Indicator Digits Population", False, f"Missing indicator digits: {', '.join(missing)}")
                return False
                
        except Exception as e:
            self.log_test("Indicator Digits Population", False, f"Error checking indicator digits: {str(e)}")
            return False
    
    def test_product_code_population(self, root):
        """Test Issue 4: Product Code showing 'None' when there should be a value"""
        try:
            # Look for product codes in EPC identifiers
            item_product_code_found = False
            case_product_code_found = False
            
            for elem in root.iter():
                if elem.tag.endswith("epc") or elem.tag.endswith("parentID"):
                    epc_text = elem.text
                    if epc_text:
                        # Check for item product code (000000)
                        if "urn:epc:id:sgtin:1234567.1000000." in epc_text:
                            item_product_code_found = True
                        # Check for case product code (000001)
                        elif "urn:epc:id:sgtin:1234567.2000001." in epc_text:
                            case_product_code_found = True
            
            # Also check that 'None' doesn't appear anywhere in the XML
            xml_content = ET.tostring(root, encoding='unicode')
            none_found = 'None' in xml_content
            
            if item_product_code_found and case_product_code_found and not none_found:
                self.log_test("Product Code Population", True, "Product codes populated correctly, no 'None' values found",
                            "Item product code: 000000, Case product code: 000001")
                return True
            else:
                issues = []
                if not item_product_code_found: issues.append("Item product code missing")
                if not case_product_code_found: issues.append("Case product code missing")
                if none_found: issues.append("'None' values found in XML")
                self.log_test("Product Code Population", False, f"Product code issues: {', '.join(issues)}")
                return False
                
        except Exception as e:
            self.log_test("Product Code Population", False, f"Error checking product codes: {str(e)}")
            return False
    
    def test_epcclass_data_population(self, root):
        """Test EPCClass data population"""
        try:
            # Look for EPCClass vocabulary with product information
            epcclass_vocab_found = False
            package_ndc_found = False
            regulated_product_name_found = False
            manufacturer_name_found = False
            
            for elem in root.iter():
                if elem.tag.endswith("Vocabulary") and elem.get("type") == "urn:epcglobal:epcis:vtype:EPCClass":
                    epcclass_vocab_found = True
                    # Look for attributes
                    for attr in elem.iter():
                        if attr.tag.endswith("attribute"):
                            attr_id = attr.get("id")
                            attr_text = attr.text
                            
                            if attr_id == "urn:epcglobal:cbv:mda#additionalTradeItemIdentification":
                                if attr_text == "4580204685":  # Package NDC with hyphens removed
                                    package_ndc_found = True
                            elif attr_id == "urn:epcglobal:cbv:mda#regulatedProductName":
                                if attr_text == "Metformin Hydrochloride Tablets":
                                    regulated_product_name_found = True
                            elif attr_id == "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName":
                                if attr_text == "Padagis US LLC":
                                    manufacturer_name_found = True
            
            if epcclass_vocab_found and package_ndc_found and regulated_product_name_found and manufacturer_name_found:
                self.log_test("EPCClass Data Population", True, "EPCClass data populated correctly",
                            "Package NDC (cleaned), Regulated Product Name, Manufacturer Name found")
                return True
            else:
                issues = []
                if not epcclass_vocab_found: issues.append("EPCClass vocabulary missing")
                if not package_ndc_found: issues.append("Package NDC missing or not cleaned")
                if not regulated_product_name_found: issues.append("Regulated Product Name missing")
                if not manufacturer_name_found: issues.append("Manufacturer Name missing")
                self.log_test("EPCClass Data Population", False, f"EPCClass issues: {', '.join(issues)}")
                return False
                
        except Exception as e:
            self.log_test("EPCClass Data Population", False, f"Error checking EPCClass data: {str(e)}")
            return False
    
    def test_ilmd_extensions_population(self, root):
        """Test ILMD extensions (lot number and expiration date)"""
        try:
            lot_number_found = False
            expiration_date_found = False
            
            for elem in root.iter():
                if elem.tag.endswith("lotNumber"):
                    if elem.text == "LOT123456":
                        lot_number_found = True
                elif elem.tag.endswith("itemExpirationDate"):
                    if elem.text == "2026-12-31":
                        expiration_date_found = True
            
            if lot_number_found and expiration_date_found:
                self.log_test("ILMD Extensions Population", True, "ILMD extensions populated correctly",
                            "Lot Number: LOT123456, Expiration Date: 2026-12-31")
                return True
            else:
                issues = []
                if not lot_number_found: issues.append("Lot number missing")
                if not expiration_date_found: issues.append("Expiration date missing")
                self.log_test("ILMD Extensions Population", False, f"ILMD issues: {', '.join(issues)}")
                return False
                
        except Exception as e:
            self.log_test("ILMD Extensions Population", False, f"Error checking ILMD extensions: {str(e)}")
            return False
    
    def test_event_structure(self, root):
        """Test event structure and counts"""
        try:
            object_events = 0
            aggregation_events = 0
            
            for elem in root.iter():
                if elem.tag.endswith("ObjectEvent"):
                    object_events += 1
                elif elem.tag.endswith("AggregationEvent"):
                    aggregation_events += 1
            
            # Expected for 1 SSCC, 1 Case, 2 Items:
            # 4 ObjectEvents: Items, Cases, SSCCs, Shipping
            # 2 AggregationEvents: Items→Case, Case→SSCC
            expected_object_events = 4
            expected_aggregation_events = 2
            
            if object_events == expected_object_events and aggregation_events == expected_aggregation_events:
                self.log_test("Event Structure", True, "Event structure correct",
                            f"ObjectEvents: {object_events}, AggregationEvents: {aggregation_events}")
                return True
            else:
                self.log_test("Event Structure", False, 
                            f"Event count mismatch - ObjectEvents: {object_events} (expected {expected_object_events}), AggregationEvents: {aggregation_events} (expected {expected_aggregation_events})")
                return False
                
        except Exception as e:
            self.log_test("Event Structure", False, f"Error checking event structure: {str(e)}")
            return False
    
    def run_configuration_data_tests(self):
        """Run comprehensive configuration data population tests"""
        print("=" * 80)
        print("CONFIGURATION DATA POPULATION TESTING")
        print("=" * 80)
        print("Testing specific issues from review request:")
        print("1. Location vocabulary not showing up")
        print("2. GLNs on Authority not showing up")
        print("3. Indicator digits not showing up")
        print("4. Product Code showing 'None' when there should be a value")
        print("5. Complete configuration field mapping (camelCase vs snake_case)")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: User Authentication
        if not self.create_test_user_and_login():
            print("\n❌ User authentication failed. Stopping tests.")
            return False
        
        # Test 3: Project Creation
        if not self.create_test_project():
            print("\n❌ Project creation failed. Stopping tests.")
            return False
        
        # Test 4: Comprehensive Configuration Creation
        if not self.test_comprehensive_configuration_creation():
            print("\n❌ Configuration creation failed. Stopping tests.")
            return False
        
        # Test 5: Serial Numbers Creation
        if not self.test_serial_numbers_creation():
            print("\n❌ Serial numbers creation failed. Stopping tests.")
            return False
        
        # Test 6: EPCIS Generation and Configuration Data Analysis
        epcis_success = self.test_epcis_generation_and_configuration_data_population()
        
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
        
        print("\nConfiguration Data Issues Tested:")
        print("✓ GLN Authority population in SBDH")
        print("✓ Location vocabulary elements with complete address information")
        print("✓ Indicator digits in EPC identifiers")
        print("✓ Product codes (no 'None' values)")
        print("✓ EPCClass data population")
        print("✓ ILMD extensions (lot number, expiration date)")
        print("✓ Event structure and counts")
        
        return passed == total

if __name__ == "__main__":
    tester = ConfigurationDataTester()
    success = tester.run_configuration_data_tests()
    sys.exit(0 if success else 1)
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
                            f"SSCC: {len(serials.get('ssccSerialNumbers', []))}, Cases: {len(serials.get('caseSerialNumbers', []))}, Items: {len(serials.get('itemSerialNumbers', []))}")
                return serials
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Serial Numbers Creation", False, f"Request error: {str(e)}")
            print(f"   Debug - Serial data sent: {serial_data}")
            print(f"   Debug - Exception type: {type(e)}")
            import traceback
            print(f"   Debug - Traceback: {traceback.format_exc()}")
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
                
                # Debug: Save XML content to file for inspection
                with open('/app/debug_epcis.xml', 'w') as f:
                    f.write(xml_content)
                print(f"   Debug - XML content saved to /app/debug_epcis.xml")
                
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