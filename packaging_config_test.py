#!/usr/bin/env python3
"""
Packaging Configuration Testing for EPCIS Serial Number Aggregation App
Tests the recent changes to ensure packaging configuration works correctly with empty default values.

Focus Areas from Review Request:
1. Configuration Creation: Test that configurations can be created with empty default values for packaging configuration fields
2. Configuration Validation: Test that backend properly handles empty string values for packaging configuration fields when they are required
3. Project Creation and Configuration: Test the complete workflow of creating a project and setting up packaging configuration
4. Package Hierarchy Logic: Test that package hierarchy calculations work correctly when packaging configuration is properly set vs. when it's empty
5. Existing Projects: Test that existing projects with pre-populated packaging configuration values still work correctly

Test scenarios:
- Create configurations with empty packaging configuration fields
- Test validation of required vs optional packaging fields
- Test complete project workflow with packaging configuration
- Test hierarchy calculations with empty vs populated packaging fields
- Test existing projects with pre-populated values
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://cd63a717-b5ed-4c4d-b9fe-b518396e7591.preview.emergentagent.com/api"

class PackagingConfigTester:
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
            "email": f"packagingtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
            "password": "TestPassword123!",
            "firstName": "Packaging",
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
                    self.log_test("User Authentication", True, f"Test user created and authenticated: {user_data['email']}")
                    return True
                else:
                    self.log_test("User Authentication", False, f"Login failed: {login_response.status_code}")
                    return False
            else:
                self.log_test("User Authentication", False, f"User creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_configuration_with_empty_defaults(self):
        """Test 1: Configuration Creation with Empty Default Values"""
        # Test configuration with minimal required fields and empty packaging fields
        minimal_config = {
            "itemsPerCase": 10,
            "casesPerSscc": 2,
            "numberOfSscc": 1,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000001",
            "caseProductCode": "000002",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            # Empty packaging configuration fields (should use defaults)
            "lotNumber": "",
            "expirationDate": "",
            "senderCompanyPrefix": "",
            "senderGln": "",
            "senderSgln": "",
            "senderName": "",
            "senderStreetAddress": "",
            "senderCity": "",
            "senderState": "",
            "senderPostalCode": "",
            "senderCountryCode": "",
            "receiverCompanyPrefix": "",
            "receiverGln": "",
            "receiverSgln": "",
            "receiverName": "",
            "receiverStreetAddress": "",
            "receiverCity": "",
            "receiverState": "",
            "receiverPostalCode": "",
            "receiverCountryCode": "",
            "shipperCompanyPrefix": "",
            "shipperGln": "",
            "shipperSgln": "",
            "shipperName": "",
            "shipperStreetAddress": "",
            "shipperCity": "",
            "shipperState": "",
            "shipperPostalCode": "",
            "shipperCountryCode": "",
            "shipperSameAsSender": False,
            "productNdc": "",
            "packageNdc": "",
            "regulatedProductName": "",
            "manufacturerName": "",
            "dosageFormType": "",
            "strengthDescription": "",
            "netContentDescription": ""
        }
        
        try:
            # Create a project first
            project_response = self.session.post(
                f"{self.base_url}/projects",
                json={"name": "Empty Defaults Test Project"},
                headers={"Content-Type": "application/json"}
            )
            
            if project_response.status_code == 200:
                project_data = project_response.json()
                project_id = project_data["id"]
                
                # Create configuration for the project
                config_response = self.session.post(
                    f"{self.base_url}/projects/{project_id}/configuration",
                    json=minimal_config,
                    headers={"Content-Type": "application/json"}
                )
                
                if config_response.status_code == 200:
                    config_data = config_response.json()
                    
                    # Verify empty fields are stored as empty strings
                    empty_fields_correct = all([
                        config_data.get("lot_number") == "",
                        config_data.get("expiration_date") == "",
                        config_data.get("sender_company_prefix") == "",
                        config_data.get("package_ndc") == "",
                        config_data.get("regulated_product_name") == ""
                    ])
                    
                    if empty_fields_correct:
                        self.log_test("Configuration with Empty Defaults", True, 
                                    "Configuration created successfully with empty packaging fields",
                                    f"Project ID: {project_id}, Config ID: {config_data['id']}")
                        return project_id, config_data["id"]
                    else:
                        self.log_test("Configuration with Empty Defaults", False, 
                                    "Empty fields not stored correctly", config_data)
                        return None, None
                else:
                    self.log_test("Configuration with Empty Defaults", False, 
                                f"Configuration creation failed: {config_response.status_code} - {config_response.text}")
                    return None, None
            else:
                self.log_test("Configuration with Empty Defaults", False, 
                            f"Project creation failed: {project_response.status_code}")
                return None, None
                
        except Exception as e:
            self.log_test("Configuration with Empty Defaults", False, f"Request error: {str(e)}")
            return None, None
    
    def test_configuration_validation_empty_required(self):
        """Test 2: Configuration Validation with Empty Required Fields"""
        # Test configuration missing truly required fields (not packaging fields)
        invalid_config = {
            "itemsPerCase": 10,
            "casesPerSscc": 2,
            # Missing numberOfSscc (required)
            "useInnerCases": False,
            # Missing companyPrefix (required)
            "itemProductCode": "000001",
            "caseProductCode": "000002",
            # Missing indicator digits (required)
            # All packaging fields empty (should be OK)
            "lotNumber": "",
            "expirationDate": "",
            "packageNdc": ""
        }
        
        try:
            # Create a project first
            project_response = self.session.post(
                f"{self.base_url}/projects",
                json={"name": "Validation Test Project"},
                headers={"Content-Type": "application/json"}
            )
            
            if project_response.status_code == 200:
                project_data = project_response.json()
                project_id = project_data["id"]
                
                # Try to create invalid configuration
                config_response = self.session.post(
                    f"{self.base_url}/projects/{project_id}/configuration",
                    json=invalid_config,
                    headers={"Content-Type": "application/json"}
                )
                
                # Should fail with validation error
                if config_response.status_code in [400, 422]:
                    self.log_test("Configuration Validation Empty Required", True, 
                                "Properly rejected configuration with missing required fields",
                                f"Status: {config_response.status_code}")
                    return True
                else:
                    self.log_test("Configuration Validation Empty Required", False, 
                                f"Should have rejected invalid config, got: {config_response.status_code}")
                    return False
            else:
                self.log_test("Configuration Validation Empty Required", False, 
                            f"Project creation failed: {project_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Validation Empty Required", False, f"Request error: {str(e)}")
            return False
    
    def test_complete_project_workflow_empty_packaging(self, project_id):
        """Test 3: Complete Project Workflow with Empty Packaging Configuration"""
        if not project_id:
            self.log_test("Complete Project Workflow", False, "No project ID available")
            return False
        
        try:
            # Create serial numbers for the project (2 SSCCs, 4 cases, 40 items)
            serial_data = {
                "ssccSerialNumbers": ["SSCC001", "SSCC002"],
                "caseSerialNumbers": ["CASE001", "CASE002", "CASE003", "CASE004"],
                "innerCaseSerialNumbers": [],
                "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(40)]  # 10 items per case × 4 cases
            }
            
            serial_response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if serial_response.status_code == 200:
                # Generate EPCIS XML
                epcis_response = self.session.post(
                    f"{self.base_url}/projects/{project_id}/generate-epcis",
                    json={
                        "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                        "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if epcis_response.status_code == 200:
                    xml_content = epcis_response.text
                    
                    # Verify XML is valid and contains expected elements
                    try:
                        root = ET.fromstring(xml_content)
                        
                        # Check for basic EPCIS structure
                        has_epcis_header = any(elem.tag.endswith("EPCISHeader") for elem in root.iter())
                        has_event_list = any(elem.tag.endswith("EventList") for elem in root.iter())
                        
                        # Count events
                        object_events = sum(1 for elem in root.iter() if elem.tag.endswith("ObjectEvent"))
                        aggregation_events = sum(1 for elem in root.iter() if elem.tag.endswith("AggregationEvent"))
                        
                        if has_epcis_header and has_event_list and object_events > 0 and aggregation_events > 0:
                            self.log_test("Complete Project Workflow", True, 
                                        "Complete workflow successful with empty packaging configuration",
                                        f"ObjectEvents: {object_events}, AggregationEvents: {aggregation_events}")
                            return True
                        else:
                            self.log_test("Complete Project Workflow", False, 
                                        "Generated XML missing expected elements")
                            return False
                            
                    except ET.ParseError as e:
                        self.log_test("Complete Project Workflow", False, f"Invalid XML generated: {str(e)}")
                        return False
                else:
                    self.log_test("Complete Project Workflow", False, 
                                f"EPCIS generation failed: {epcis_response.status_code}")
                    return False
            else:
                self.log_test("Complete Project Workflow", False, 
                            f"Serial numbers creation failed: {serial_response.status_code} - {serial_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Complete Project Workflow", False, f"Workflow error: {str(e)}")
            return False
    
    def test_hierarchy_calculations_empty_vs_populated(self):
        """Test 4: Package Hierarchy Logic with Empty vs Populated Packaging Configuration"""
        
        # Test 1: Configuration with empty packaging fields
        empty_packaging_config = {
            "itemsPerCase": 5,
            "casesPerSscc": 3,
            "numberOfSscc": 2,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000001",
            "caseProductCode": "000002",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            # Empty packaging fields
            "lotNumber": "",
            "expirationDate": "",
            "packageNdc": "",
            "regulatedProductName": ""
        }
        
        # Test 2: Configuration with populated packaging fields
        populated_packaging_config = {
            "itemsPerCase": 5,
            "casesPerSscc": 3,
            "numberOfSscc": 2,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000001",
            "caseProductCode": "000002",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            # Populated packaging fields
            "lotNumber": "LOT123",
            "expirationDate": "2025-12-31",
            "packageNdc": "12345-678-90",
            "regulatedProductName": "Test Medicine"
        }
        
        test_configs = [
            ("Empty Packaging Fields", empty_packaging_config),
            ("Populated Packaging Fields", populated_packaging_config)
        ]
        
        hierarchy_results = []
        
        for config_name, config_data in test_configs:
            try:
                # Create project
                project_response = self.session.post(
                    f"{self.base_url}/projects",
                    json={"name": f"Hierarchy Test - {config_name}"},
                    headers={"Content-Type": "application/json"}
                )
                
                if project_response.status_code == 200:
                    project_id = project_response.json()["id"]
                    
                    # Create configuration
                    config_response = self.session.post(
                        f"{self.base_url}/projects/{project_id}/configuration",
                        json=config_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if config_response.status_code == 200:
                        # Create serial numbers (2 SSCCs × 3 cases × 5 items = 30 total items)
                        serial_data = {
                            "ssccSerialNumbers": ["SSCC001", "SSCC002"],
                            "caseSerialNumbers": [f"CASE{i+1:03d}" for i in range(6)],  # 3 cases per SSCC × 2 SSCCs
                            "innerCaseSerialNumbers": [],
                            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(30)]  # 5 items per case × 6 cases
                        }
                        
                        serial_response = self.session.post(
                            f"{self.base_url}/projects/{project_id}/serial-numbers",
                            json=serial_data,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if serial_response.status_code == 200:
                            hierarchy_results.append((config_name, True, "Hierarchy calculations working"))
                        else:
                            hierarchy_results.append((config_name, False, f"Serial validation failed: {serial_response.status_code}"))
                    else:
                        hierarchy_results.append((config_name, False, f"Config creation failed: {config_response.status_code}"))
                else:
                    hierarchy_results.append((config_name, False, f"Project creation failed: {project_response.status_code}"))
                    
            except Exception as e:
                hierarchy_results.append((config_name, False, f"Error: {str(e)}"))
        
        # Evaluate results
        all_successful = all(result[1] for result in hierarchy_results)
        
        if all_successful:
            self.log_test("Package Hierarchy Logic", True, 
                        "Hierarchy calculations work correctly with both empty and populated packaging fields",
                        f"Results: {hierarchy_results}")
        else:
            failed_configs = [result[0] for result in hierarchy_results if not result[1]]
            self.log_test("Package Hierarchy Logic", False, 
                        f"Hierarchy calculations failed for: {failed_configs}",
                        f"Results: {hierarchy_results}")
        
        return all_successful
    
    def test_existing_projects_with_prepopulated_values(self):
        """Test 5: Existing Projects with Pre-populated Packaging Configuration Values"""
        
        # Create a project with fully populated packaging configuration (simulating existing project)
        full_config = {
            "itemsPerCase": 8,
            "casesPerSscc": 4,
            "numberOfSscc": 1,
            "useInnerCases": True,
            "innerCasesPerCase": 2,
            "itemsPerInnerCase": 4,
            "companyPrefix": "9876543",
            "itemProductCode": "111111",
            "caseProductCode": "222222",
            "innerCaseProductCode": "333333",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "innerCaseIndicatorDigit": "4",
            "itemIndicatorDigit": "1",
            # Pre-populated packaging fields
            "lotNumber": "BATCH456",
            "expirationDate": "2026-06-30",
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "senderName": "Sender Company LLC",
            "senderStreetAddress": "456 Sender Ave",
            "senderCity": "Sender City",
            "senderState": "SC",
            "senderPostalCode": "54321",
            "senderCountryCode": "US",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Receiver Corp",
            "receiverStreetAddress": "789 Receiver Blvd",
            "receiverCity": "Receiver Town",
            "receiverState": "RT",
            "receiverPostalCode": "67890",
            "receiverCountryCode": "US",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Shipper Inc",
            "shipperStreetAddress": "321 Shipper St",
            "shipperCity": "Shipper Village",
            "shipperState": "SV",
            "shipperPostalCode": "13579",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False,
            "productNdc": "11111-222-33",
            "packageNdc": "44444-555-66",
            "regulatedProductName": "Advanced Test Medicine",
            "manufacturerName": "Test Pharma Inc",
            "dosageFormType": "Capsule",
            "strengthDescription": "25mg",
            "netContentDescription": "60 capsules"
        }
        
        try:
            # Create project
            project_response = self.session.post(
                f"{self.base_url}/projects",
                json={"name": "Pre-populated Values Test Project"},
                headers={"Content-Type": "application/json"}
            )
            
            if project_response.status_code == 200:
                project_id = project_response.json()["id"]
                
                # Create configuration with pre-populated values
                config_response = self.session.post(
                    f"{self.base_url}/projects/{project_id}/configuration",
                    json=full_config,
                    headers={"Content-Type": "application/json"}
                )
                
                if config_response.status_code == 200:
                    config_data = config_response.json()
                    
                    # Verify all pre-populated values are stored correctly
                    values_preserved = all([
                        config_data.get("lot_number") == "BATCH456",
                        config_data.get("expiration_date") == "2026-06-30",
                        config_data.get("sender_gln") == "0345802000014",
                        config_data.get("package_ndc") == "44444-555-66",
                        config_data.get("regulated_product_name") == "Advanced Test Medicine",
                        config_data.get("manufacturer_name") == "Test Pharma Inc"
                    ])
                    
                    if values_preserved:
                        # Test complete workflow with pre-populated values
                        # Create serial numbers for 4-level hierarchy: 1 SSCC, 4 Cases, 8 Inner Cases, 32 Items
                        serial_data = {
                            "ssccSerialNumbers": ["SSCC001"],
                            "caseSerialNumbers": ["CASE001", "CASE002", "CASE003", "CASE004"],
                            "innerCaseSerialNumbers": [f"INNER{i+1:03d}" for i in range(8)],  # 2 inner cases per case × 4 cases
                            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(32)]  # 4 items per inner case × 8 inner cases
                        }
                        
                        serial_response = self.session.post(
                            f"{self.base_url}/projects/{project_id}/serial-numbers",
                            json=serial_data,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if serial_response.status_code == 200:
                            # Generate EPCIS to test complete functionality
                            epcis_response = self.session.post(
                                f"{self.base_url}/projects/{project_id}/generate-epcis",
                                json={
                                    "readPoint": "urn:epc:id:sgln:9876543.00000.0",
                                    "bizLocation": "urn:epc:id:sgln:9876543.00001.0"
                                },
                                headers={"Content-Type": "application/json"}
                            )
                            
                            if epcis_response.status_code == 200:
                                xml_content = epcis_response.text
                                
                                # Verify pre-populated values appear in XML
                                has_lot_number = "BATCH456" in xml_content
                                has_expiration = "2026-06-30" in xml_content
                                has_package_ndc = "4444455566" in xml_content  # Hyphens removed
                                has_sender_gln = "0345802000014" in xml_content
                                
                                if has_lot_number and has_expiration and has_package_ndc and has_sender_gln:
                                    self.log_test("Existing Projects Pre-populated Values", True, 
                                                "Pre-populated packaging configuration values work correctly",
                                                "All values preserved and appear in generated EPCIS XML")
                                    return True
                                else:
                                    self.log_test("Existing Projects Pre-populated Values", False, 
                                                f"Pre-populated values missing from XML - Lot: {has_lot_number}, Exp: {has_expiration}, NDC: {has_package_ndc}, GLN: {has_sender_gln}")
                                    return False
                            else:
                                self.log_test("Existing Projects Pre-populated Values", False, 
                                            f"EPCIS generation failed: {epcis_response.status_code}")
                                return False
                        else:
                            self.log_test("Existing Projects Pre-populated Values", False, 
                                        f"Serial numbers creation failed: {serial_response.status_code}")
                            return False
                    else:
                        self.log_test("Existing Projects Pre-populated Values", False, 
                                    "Pre-populated values not stored correctly", config_data)
                        return False
                else:
                    self.log_test("Existing Projects Pre-populated Values", False, 
                                f"Configuration creation failed: {config_response.status_code}")
                    return False
            else:
                self.log_test("Existing Projects Pre-populated Values", False, 
                            f"Project creation failed: {project_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Existing Projects Pre-populated Values", False, f"Test error: {str(e)}")
            return False
    
    def test_configuration_field_defaults(self):
        """Test 6: Verify Configuration Field Default Values"""
        
        # Test configuration with only absolutely required fields
        minimal_required_config = {
            "itemsPerCase": 12,
            "casesPerSscc": 1,
            "numberOfSscc": 1,
            "companyPrefix": "1111111",
            "itemProductCode": "999999",
            "caseProductCode": "888888",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1"
            # All other fields should get default values
        }
        
        try:
            # Create project
            project_response = self.session.post(
                f"{self.base_url}/projects",
                json={"name": "Field Defaults Test Project"},
                headers={"Content-Type": "application/json"}
            )
            
            if project_response.status_code == 200:
                project_id = project_response.json()["id"]
                
                # Create configuration with minimal fields
                config_response = self.session.post(
                    f"{self.base_url}/projects/{project_id}/configuration",
                    json=minimal_required_config,
                    headers={"Content-Type": "application/json"}
                )
                
                if config_response.status_code == 200:
                    config_data = config_response.json()
                    
                    # Verify default values are applied correctly
                    expected_defaults = {
                        "use_inner_cases": False,
                        "inner_cases_per_case": 0,
                        "items_per_inner_case": 0,
                        "inner_case_product_code": "",
                        "inner_case_indicator_digit": "",
                        "lot_number": "",
                        "expiration_date": "",
                        "sender_company_prefix": "",
                        "sender_gln": "",
                        "package_ndc": "",
                        "regulated_product_name": "",
                        "shipper_same_as_sender": False
                    }
                    
                    defaults_correct = True
                    incorrect_defaults = []
                    
                    for field, expected_value in expected_defaults.items():
                        actual_value = config_data.get(field)
                        if actual_value != expected_value:
                            defaults_correct = False
                            incorrect_defaults.append(f"{field}: expected '{expected_value}', got '{actual_value}'")
                    
                    if defaults_correct:
                        self.log_test("Configuration Field Defaults", True, 
                                    "All configuration fields have correct default values",
                                    f"Verified {len(expected_defaults)} default fields")
                        return True
                    else:
                        self.log_test("Configuration Field Defaults", False, 
                                    f"Incorrect default values: {incorrect_defaults}")
                        return False
                else:
                    self.log_test("Configuration Field Defaults", False, 
                                f"Configuration creation failed: {config_response.status_code}")
                    return False
            else:
                self.log_test("Configuration Field Defaults", False, 
                            f"Project creation failed: {project_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Field Defaults", False, f"Test error: {str(e)}")
            return False
    
    def run_packaging_configuration_tests(self):
        """Run all packaging configuration tests"""
        print("=" * 80)
        print("PACKAGING CONFIGURATION TESTING - EMPTY DEFAULT VALUES")
        print("=" * 80)
        print("Testing recent changes to ensure packaging configuration works correctly")
        print("with empty default values for packaging configuration fields.")
        print()
        print("Focus Areas:")
        print("1. Configuration Creation with Empty Default Values")
        print("2. Configuration Validation for Required vs Optional Fields")
        print("3. Complete Project Workflow with Empty Packaging Configuration")
        print("4. Package Hierarchy Logic with Empty vs Populated Fields")
        print("5. Existing Projects with Pre-populated Values")
        print("6. Configuration Field Default Values")
        print("=" * 80)
        
        # Test 0: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 0.1: Setup test user
        if not self.setup_test_user():
            print("\n❌ Could not setup test user. Stopping tests.")
            return False
        
        # Test 1: Configuration Creation with Empty Default Values
        project_id, config_id = self.test_configuration_with_empty_defaults()
        
        # Test 2: Configuration Validation with Empty Required Fields
        self.test_configuration_validation_empty_required()
        
        # Test 3: Complete Project Workflow with Empty Packaging Configuration
        self.test_complete_project_workflow_empty_packaging(project_id)
        
        # Test 4: Package Hierarchy Logic with Empty vs Populated Packaging Configuration
        self.test_hierarchy_calculations_empty_vs_populated()
        
        # Test 5: Existing Projects with Pre-populated Packaging Configuration Values
        self.test_existing_projects_with_prepopulated_values()
        
        # Test 6: Configuration Field Default Values
        self.test_configuration_field_defaults()
        
        # Summary
        print("\n" + "=" * 80)
        print("PACKAGING CONFIGURATION TEST SUMMARY")
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
        
        print("\nPackaging Configuration Features Tested:")
        print("✓ Configuration creation with empty default values")
        print("✓ Validation of required vs optional packaging fields")
        print("✓ Complete project workflow with empty packaging configuration")
        print("✓ Hierarchy calculations with empty vs populated packaging fields")
        print("✓ Existing projects with pre-populated packaging values")
        print("✓ Configuration field default value handling")
        
        return passed == total

if __name__ == "__main__":
    tester = PackagingConfigTester()
    success = tester.run_packaging_configuration_tests()
    sys.exit(0 if success else 1)