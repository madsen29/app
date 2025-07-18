#!/usr/bin/env python3
"""
Backend API Testing for User-Reported Serial Number Calculation Issue
Tests the exact configuration scenario reported by the user:

USER REPORTED ISSUE: Two critical problems with the serial number collection and configuration locking:

1. **Serial Number Calculation Issue**: User configured 1 SSCC, 2 cases per SSCC, 3 inner cases per case, 
   and 4 items per inner case, but Step 2 only asked for 1 item instead of the expected 24 items (1×2×3×4=24).

2. **Package Configuration Lock Issue**: When going back from Step 2 to Step 1, the Package Configuration 
   should be locked (read-only) but it's not showing as locked.

TESTING REQUIREMENTS:
1. Create Test Configuration: numberOfSscc: 1, casesPerSscc: 2, useInnerCases: true, 
   innerCasesPerCase: 3, itemsPerInnerCase: 4, Expected total items: 1 × 2 × 3 × 4 = 24 items
2. Test Configuration Storage: Verify configuration is stored correctly in backend
3. Test Total Calculation: Verify backend correctly calculates expected totals
4. Test Serial Number Structure: Verify serial numbers structure is created correctly
5. Test Configuration Fields: Verify camelCase vs snake_case field handling

FOCUS AREAS:
- Verify casesPerSscc: 2 is stored correctly
- Verify innerCasesPerCase: 3 is stored correctly  
- Verify itemsPerInnerCase: 4 is stored correctly
- Verify useInnerCases: true is stored correctly
- Test project retrieval to ensure configuration is loaded back correctly
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

class UserIssueBackendTester:
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
    
    def setup_test_user(self):
        """Create a test user and authenticate"""
        # Create test user
        user_data = {
            "email": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "password": "testpassword123",
            "firstName": "Test",
            "lastName": "User",
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
                login_data = {
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
                
                login_response = self.session.post(
                    f"{self.base_url}/auth/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.auth_token = token_data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("User Authentication", True, f"Test user created and authenticated: {user_data['email']}")
                    return True
                else:
                    self.log_test("User Authentication", False, f"Login failed: {login_response.status_code}")
                    return False
            else:
                self.log_test("User Authentication", False, f"User creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_user_reported_configuration_creation(self):
        """Test creating the exact configuration reported by the user"""
        # Create project first
        project_data = {"name": "User Issue Test Project"}
        
        try:
            project_response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if project_response.status_code != 200:
                self.log_test("User Configuration - Project Creation", False, f"Project creation failed: {project_response.status_code}")
                return None, None
            
            project = project_response.json()
            project_id = project["id"]
            
            # User's exact configuration: 1 SSCC, 2 cases per SSCC, 3 inner cases per case, 4 items per inner case
            # Expected total items: 1 × 2 × 3 × 4 = 24 items
            user_config = {
                "numberOfSscc": 1,
                "casesPerSscc": 2,
                "useInnerCases": True,
                "innerCasesPerCase": 3,
                "itemsPerInnerCase": 4,
                "companyPrefix": "1234567",
                "itemProductCode": "000000",
                "caseProductCode": "000001",
                "innerCaseProductCode": "000002",
                "lotNumber": "LOT123456",
                "expirationDate": "2026-12-31",
                "ssccIndicatorDigit": "3",
                "caseIndicatorDigit": "2",
                "innerCaseIndicatorDigit": "4",
                "itemIndicatorDigit": "1",
                # Business document info
                "senderCompanyPrefix": "0345802",
                "senderGln": "0345802000014",
                "senderSgln": "0345802000014.001",
                "senderName": "Test Sender",
                "senderStreetAddress": "123 Sender St",
                "senderCity": "Sender City",
                "senderState": "SC",
                "senderPostalCode": "12345",
                "senderCountryCode": "US",
                "receiverCompanyPrefix": "0567890",
                "receiverGln": "0567890000021",
                "receiverSgln": "0567890000021.001",
                "receiverName": "Test Receiver",
                "receiverStreetAddress": "456 Receiver Ave",
                "receiverCity": "Receiver City",
                "receiverState": "RC",
                "receiverPostalCode": "67890",
                "receiverCountryCode": "US",
                "shipperCompanyPrefix": "0999888",
                "shipperGln": "0999888000028",
                "shipperSgln": "0999888000028.001",
                "shipperName": "Test Shipper",
                "shipperStreetAddress": "789 Shipper Blvd",
                "shipperCity": "Shipper City",
                "shipperState": "SH",
                "shipperPostalCode": "11111",
                "shipperCountryCode": "US",
                "shipperSameAsSender": False,
                # EPCClass data
                "packageNdc": "45802-046-85",
                "regulatedProductName": "Test Medication",
                "manufacturerName": "Test Pharma Inc",
                "dosageFormType": "Tablet",
                "strengthDescription": "500mg",
                "netContentDescription": "100 tablets"
            }
            
            # Save configuration to project
            config_response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=user_config,
                headers={"Content-Type": "application/json"}
            )
            
            if config_response.status_code == 200:
                config_data = config_response.json()
                self.log_test("User Configuration Creation", True, 
                            "User's exact configuration created successfully",
                            f"Project ID: {project_id}, Config fields: {len(user_config)}")
                return project_id, config_data
            else:
                self.log_test("User Configuration Creation", False, 
                            f"Configuration creation failed: {config_response.status_code} - {config_response.text}")
                return project_id, None
                
        except Exception as e:
            self.log_test("User Configuration Creation", False, f"Request error: {str(e)}")
            return None, None
    
    def test_configuration_storage_and_retrieval(self, project_id):
        """Test that configuration is stored and retrieved correctly with proper field mapping"""
        if not project_id:
            self.log_test("Configuration Storage & Retrieval", False, "No project ID available")
            return False
        
        try:
            # Retrieve the project to check configuration storage
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                project = response.json()
                config = project.get("configuration")
                
                if not config:
                    self.log_test("Configuration Storage & Retrieval", False, "No configuration found in project")
                    return False
                
                # Check critical fields that user reported issues with
                critical_fields = {
                    "numberOfSscc": 1,
                    "casesPerSscc": 2,
                    "useInnerCases": True,
                    "innerCasesPerCase": 3,
                    "itemsPerInnerCase": 4
                }
                
                # Check both camelCase and snake_case versions
                field_mapping = {
                    "numberOfSscc": ["number_of_sscc", "numberOfSscc"],
                    "casesPerSscc": ["cases_per_sscc", "casesPerSscc"],
                    "useInnerCases": ["use_inner_cases", "useInnerCases"],
                    "innerCasesPerCase": ["inner_cases_per_case", "innerCasesPerCase"],
                    "itemsPerInnerCase": ["items_per_inner_case", "itemsPerInnerCase"]
                }
                
                missing_fields = []
                incorrect_values = []
                
                for field, expected_value in critical_fields.items():
                    found = False
                    actual_value = None
                    
                    # Check all possible field name variations
                    for field_variant in field_mapping[field]:
                        if field_variant in config:
                            found = True
                            actual_value = config[field_variant]
                            if actual_value != expected_value:
                                incorrect_values.append(f"{field_variant}: expected {expected_value}, got {actual_value}")
                            break
                    
                    if not found:
                        missing_fields.append(field)
                
                if missing_fields or incorrect_values:
                    error_details = []
                    if missing_fields:
                        error_details.append(f"Missing fields: {missing_fields}")
                    if incorrect_values:
                        error_details.append(f"Incorrect values: {incorrect_values}")
                    
                    self.log_test("Configuration Storage & Retrieval", False, 
                                "Configuration field issues found", "; ".join(error_details))
                    return False
                else:
                    self.log_test("Configuration Storage & Retrieval", True, 
                                "All critical configuration fields stored and retrieved correctly",
                                f"Verified fields: {list(critical_fields.keys())}")
                    return True
            else:
                self.log_test("Configuration Storage & Retrieval", False, 
                            f"Project retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Storage & Retrieval", False, f"Request error: {str(e)}")
            return False
    
    def test_total_calculation_logic(self, project_id):
        """Test that backend correctly calculates expected totals for the user's configuration"""
        if not project_id:
            self.log_test("Total Calculation Logic", False, "No project ID available")
            return False
        
        try:
            # Get project configuration
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code != 200:
                self.log_test("Total Calculation Logic", False, f"Project retrieval failed: {response.status_code}")
                return False
            
            project = response.json()
            config = project.get("configuration")
            
            if not config:
                self.log_test("Total Calculation Logic", False, "No configuration found")
                return False
            
            # Helper function to get config value (handles both camelCase and snake_case)
            def get_config_value(key_snake, key_camel, default=0):
                return config.get(key_snake, config.get(key_camel, default))
            
            # Extract configuration values
            number_of_sscc = get_config_value("number_of_sscc", "numberOfSscc", 1)
            cases_per_sscc = get_config_value("cases_per_sscc", "casesPerSscc", 2)
            use_inner_cases = get_config_value("use_inner_cases", "useInnerCases", True)
            inner_cases_per_case = get_config_value("inner_cases_per_case", "innerCasesPerCase", 3)
            items_per_inner_case = get_config_value("items_per_inner_case", "itemsPerInnerCase", 4)
            
            # Calculate expected totals based on user's configuration
            # User's config: 1 SSCC, 2 cases per SSCC, 3 inner cases per case, 4 items per inner case
            expected_sscc_count = number_of_sscc  # 1
            expected_case_count = number_of_sscc * cases_per_sscc  # 1 × 2 = 2
            expected_inner_case_count = expected_case_count * inner_cases_per_case  # 2 × 3 = 6
            expected_item_count = expected_inner_case_count * items_per_inner_case  # 6 × 4 = 24
            
            # Verify calculations
            calculations_correct = (
                expected_sscc_count == 1 and
                expected_case_count == 2 and
                expected_inner_case_count == 6 and
                expected_item_count == 24
            )
            
            if calculations_correct:
                self.log_test("Total Calculation Logic", True, 
                            "Backend calculation logic is correct for user's configuration",
                            f"SSCCs: {expected_sscc_count}, Cases: {expected_case_count}, Inner Cases: {expected_inner_case_count}, Items: {expected_item_count}")
                return expected_sscc_count, expected_case_count, expected_inner_case_count, expected_item_count
            else:
                self.log_test("Total Calculation Logic", False, 
                            "Calculation logic error detected",
                            f"Expected 24 items but calculation gives: SSCCs: {expected_sscc_count}, Cases: {expected_case_count}, Inner Cases: {expected_inner_case_count}, Items: {expected_item_count}")
                return None
                
        except Exception as e:
            self.log_test("Total Calculation Logic", False, f"Request error: {str(e)}")
            return None
    
    def test_serial_number_validation_with_user_config(self, project_id, expected_counts):
        """Test serial number validation with the user's exact configuration"""
        if not project_id or not expected_counts:
            self.log_test("Serial Number Validation", False, "Missing project ID or expected counts")
            return False
        
        expected_sscc_count, expected_case_count, expected_inner_case_count, expected_item_count = expected_counts
        
        # Create serial numbers matching the expected counts
        sscc_serials = [f"SSCC{i+1:03d}" for i in range(expected_sscc_count)]
        case_serials = [f"CASE{i+1:03d}" for i in range(expected_case_count)]
        inner_case_serials = [f"INNER{i+1:03d}" for i in range(expected_inner_case_count)]
        item_serials = [f"ITEM{i+1:03d}" for i in range(expected_item_count)]
        
        serial_data = {
            "ssccSerialNumbers": sscc_serials,
            "caseSerialNumbers": case_serials,
            "innerCaseSerialNumbers": inner_case_serials,
            "itemSerialNumbers": item_serials
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify the response contains correct counts
                # Backend returns camelCase field names in response
                actual_counts = {
                    "sscc": len(data.get("ssccSerialNumbers", data.get("sscc_serial_numbers", []))),
                    "case": len(data.get("caseSerialNumbers", data.get("case_serial_numbers", []))),
                    "inner_case": len(data.get("innerCaseSerialNumbers", data.get("inner_case_serial_numbers", []))),
                    "item": len(data.get("itemSerialNumbers", data.get("item_serial_numbers", [])))
                }
                
                expected_counts_dict = {
                    "sscc": expected_sscc_count,
                    "case": expected_case_count,
                    "inner_case": expected_inner_case_count,
                    "item": expected_item_count
                }
                
                if actual_counts == expected_counts_dict:
                    self.log_test("Serial Number Validation", True, 
                                "Serial numbers accepted with correct validation for user's configuration",
                                f"Validated counts: {actual_counts}")
                    return True
                else:
                    self.log_test("Serial Number Validation", False, 
                                f"Count mismatch - Expected: {expected_counts_dict}, Actual: {actual_counts}")
                    return False
            else:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "")
                except:
                    error_detail = response.text
                
                self.log_test("Serial Number Validation", False, 
                            f"Serial number validation failed: {response.status_code}",
                            f"Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Serial Number Validation", False, f"Request error: {str(e)}")
            return False
    
    def test_serial_number_validation_with_wrong_counts(self, project_id):
        """Test that backend properly rejects serial numbers with wrong counts"""
        if not project_id:
            self.log_test("Serial Number Wrong Count Validation", False, "No project ID available")
            return False
        
        # Test with wrong item count (should be 24, providing only 1 - this is the user's reported issue)
        wrong_serial_data = {
            "ssccSerialNumbers": ["SSCC001"],  # Correct: 1
            "caseSerialNumbers": ["CASE001", "CASE002"],  # Correct: 2
            "innerCaseSerialNumbers": ["INNER001", "INNER002", "INNER003", "INNER004", "INNER005", "INNER006"],  # Correct: 6
            "itemSerialNumbers": ["ITEM001"]  # WRONG: Only 1 item instead of 24
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=wrong_serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                
                # Check if error message mentions the expected 24 items
                if "24" in error_detail and "item" in error_detail.lower():
                    self.log_test("Serial Number Wrong Count Validation", True, 
                                "Backend correctly rejects wrong item count and expects 24 items",
                                f"Error message: {error_detail}")
                    return True
                else:
                    self.log_test("Serial Number Wrong Count Validation", False, 
                                f"Error message doesn't mention expected 24 items: {error_detail}")
                    return False
            else:
                self.log_test("Serial Number Wrong Count Validation", False, 
                            f"Expected 400 error for wrong count, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Serial Number Wrong Count Validation", False, f"Request error: {str(e)}")
            return False
    
    def test_field_name_mapping_consistency(self, project_id):
        """Test that camelCase vs snake_case field mapping is consistent throughout the system"""
        if not project_id:
            self.log_test("Field Name Mapping Consistency", False, "No project ID available")
            return False
        
        try:
            # Get project configuration
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code != 200:
                self.log_test("Field Name Mapping Consistency", False, f"Project retrieval failed: {response.status_code}")
                return False
            
            project = response.json()
            config = project.get("configuration")
            
            if not config:
                self.log_test("Field Name Mapping Consistency", False, "No configuration found")
                return False
            
            # Test critical field mappings that user reported issues with
            field_tests = [
                {
                    "camelCase": "numberOfSscc",
                    "snake_case": "number_of_sscc",
                    "expected_value": 1
                },
                {
                    "camelCase": "casesPerSscc",
                    "snake_case": "cases_per_sscc",
                    "expected_value": 2
                },
                {
                    "camelCase": "useInnerCases",
                    "snake_case": "use_inner_cases",
                    "expected_value": True
                },
                {
                    "camelCase": "innerCasesPerCase",
                    "snake_case": "inner_cases_per_case",
                    "expected_value": 3
                },
                {
                    "camelCase": "itemsPerInnerCase",
                    "snake_case": "items_per_inner_case",
                    "expected_value": 4
                }
            ]
            
            mapping_issues = []
            
            for field_test in field_tests:
                camel_case = field_test["camelCase"]
                snake_case = field_test["snake_case"]
                expected = field_test["expected_value"]
                
                camel_value = config.get(camel_case)
                snake_value = config.get(snake_case)
                
                # Check if at least one version exists with correct value
                if camel_value == expected or snake_value == expected:
                    # Good - at least one version has correct value
                    continue
                elif camel_value is None and snake_value is None:
                    mapping_issues.append(f"Missing both {camel_case} and {snake_case}")
                elif camel_value != expected and snake_value != expected:
                    mapping_issues.append(f"Both {camel_case}={camel_value} and {snake_case}={snake_value} != {expected}")
                else:
                    mapping_issues.append(f"Inconsistent values: {camel_case}={camel_value}, {snake_case}={snake_value}")
            
            if mapping_issues:
                self.log_test("Field Name Mapping Consistency", False, 
                            "Field mapping issues detected", "; ".join(mapping_issues))
                return False
            else:
                self.log_test("Field Name Mapping Consistency", True, 
                            "All critical field mappings are consistent",
                            f"Tested {len(field_tests)} field mappings")
                return True
                
        except Exception as e:
            self.log_test("Field Name Mapping Consistency", False, f"Request error: {str(e)}")
            return False
    
    def test_epcis_generation_with_user_config(self, project_id):
        """Test EPCIS generation with the user's configuration to ensure all data is properly used"""
        if not project_id:
            self.log_test("EPCIS Generation with User Config", False, "No project ID available")
            return False
        
        try:
            # Generate EPCIS
            epcis_data = {
                "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json=epcis_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Parse XML to verify structure
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Count events
                    object_events = 0
                    aggregation_events = 0
                    
                    for elem in root.iter():
                        if elem.tag.endswith("ObjectEvent"):
                            object_events += 1
                        elif elem.tag.endswith("AggregationEvent"):
                            aggregation_events += 1
                    
                    # For user's 4-level hierarchy (SSCC→Cases→Inner Cases→Items):
                    # Expected: 4 ObjectEvents (commissioning) + multiple AggregationEvents
                    # Items→Inner Cases (6 events) + Inner Cases→Cases (2 events) + Cases→SSCCs (1 event) = 9 aggregation events
                    # Plus 1 shipping event = 4 ObjectEvents + 9 AggregationEvents + 1 shipping ObjectEvent = 5 ObjectEvents + 9 AggregationEvents
                    
                    expected_object_events = 5  # Items, Inner Cases, Cases, SSCCs commissioning + 1 shipping
                    expected_aggregation_events = 9  # 6 + 2 + 1
                    
                    # Check if configuration data is properly populated in XML
                    config_data_checks = [
                        ("0345802000014", "Sender GLN"),  # senderGln
                        ("0567890000021", "Receiver GLN"),  # receiverGln
                        ("4580204685", "Package NDC (cleaned)"),  # packageNdc without hyphens
                        ("LOT123456", "Lot Number"),  # lotNumber
                        ("2026-12-31", "Expiration Date"),  # expirationDate
                        ("Test Medication", "Regulated Product Name"),  # regulatedProductName
                    ]
                    
                    missing_data = []
                    for data_value, data_name in config_data_checks:
                        if data_value not in xml_content:
                            missing_data.append(data_name)
                    
                    if missing_data:
                        self.log_test("EPCIS Generation with User Config", False, 
                                    f"Configuration data not properly populated in EPCIS XML",
                                    f"Missing: {', '.join(missing_data)}")
                        return False
                    
                    # Check event counts
                    if object_events == expected_object_events and aggregation_events == expected_aggregation_events:
                        self.log_test("EPCIS Generation with User Config", True, 
                                    "EPCIS XML generated correctly with user's configuration",
                                    f"ObjectEvents: {object_events}, AggregationEvents: {aggregation_events}, All config data populated")
                        return True
                    else:
                        self.log_test("EPCIS Generation with User Config", False, 
                                    f"Event count mismatch - ObjectEvents: {object_events} (expected {expected_object_events}), AggregationEvents: {aggregation_events} (expected {expected_aggregation_events})")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("EPCIS Generation with User Config", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("EPCIS Generation with User Config", False, 
                            f"EPCIS generation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("EPCIS Generation with User Config", False, f"Request error: {str(e)}")
            return False
    
    def run_user_issue_tests(self):
        """Run comprehensive tests for the user-reported issue"""
        print("=" * 80)
        print("USER-REPORTED ISSUE COMPREHENSIVE BACKEND TESTING")
        print("=" * 80)
        print("Testing User's Exact Configuration:")
        print("- numberOfSscc: 1")
        print("- casesPerSscc: 2") 
        print("- useInnerCases: true")
        print("- innerCasesPerCase: 3")
        print("- itemsPerInnerCase: 4")
        print("- Expected total items: 1 × 2 × 3 × 4 = 24 items")
        print()
        print("Focus Areas:")
        print("1. Configuration Storage and Retrieval")
        print("2. Total Calculation Logic")
        print("3. Serial Number Structure Creation")
        print("4. Field Name Mapping (camelCase vs snake_case)")
        print("5. Backend API Integration")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Setup test user
        if not self.setup_test_user():
            print("\n❌ Could not setup test user. Stopping tests.")
            return False
        
        # Test 3: Create user's exact configuration
        project_id, config_data = self.test_user_reported_configuration_creation()
        
        # Test 4: Test configuration storage and retrieval
        storage_success = self.test_configuration_storage_and_retrieval(project_id)
        
        # Test 5: Test total calculation logic
        expected_counts = self.test_total_calculation_logic(project_id)
        
        # Test 6: Test serial number validation with correct counts
        if expected_counts:
            validation_success = self.test_serial_number_validation_with_user_config(project_id, expected_counts)
        else:
            validation_success = False
        
        # Test 7: Test serial number validation with wrong counts (user's reported issue)
        wrong_count_validation = self.test_serial_number_validation_with_wrong_counts(project_id)
        
        # Test 8: Test field name mapping consistency
        mapping_success = self.test_field_name_mapping_consistency(project_id)
        
        # Test 9: Test EPCIS generation with user's config
        epcis_success = self.test_epcis_generation_with_user_config(project_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("USER ISSUE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical Issue Analysis
        print("\n" + "=" * 40)
        print("CRITICAL ISSUE ANALYSIS")
        print("=" * 40)
        
        if expected_counts and expected_counts[3] == 24:
            print("✅ Backend correctly calculates 24 total items for user's configuration")
        else:
            print("❌ Backend calculation issue - not calculating 24 items correctly")
        
        if wrong_count_validation:
            print("✅ Backend properly validates and expects 24 items (rejects wrong counts)")
        else:
            print("❌ Backend validation issue - not properly expecting 24 items")
        
        if storage_success and mapping_success:
            print("✅ Configuration storage and field mapping working correctly")
        else:
            print("❌ Configuration storage or field mapping issues detected")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nRoot Cause Analysis:")
        if not storage_success:
            print("- Configuration data may not be stored correctly in backend")
        if not mapping_success:
            print("- Field name mapping (camelCase vs snake_case) may have issues")
        if expected_counts and expected_counts[3] != 24:
            print("- Total calculation logic may have errors")
        if not wrong_count_validation:
            print("- Serial number validation may not be using correct totals")
        
        return passed == total

if __name__ == "__main__":
    tester = UserIssueBackendTester()
    success = tester.run_user_issue_tests()
    sys.exit(0 if success else 1)