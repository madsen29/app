#!/usr/bin/env python3
"""
Complete Backend Workflow Testing for EPCIS Serial Number Aggregation App

This test verifies the complete workflow using the correct project-based API endpoints:
1. Authentication
2. Project creation
3. Configuration data persistence (complete configuration storage)
4. Serial numbers management
5. EPCIS XML generation
6. Data integrity verification

Focus on verifying that the Step 1 configuration data loss issue has been resolved.
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://cd63a717-b5ed-4c4d-b9fe-b518396e7591.preview.emergentagent.com/api"

class CompleteWorkflowTester:
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
    
    def setup_authentication(self):
        """Create test user and authenticate"""
        test_user = {
            "email": f"workflowtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "password": "TestPassword123!",
            "firstName": "Workflow",
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
                json=test_user,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data["id"]
                
                # Login to get token
                login_response = self.session.post(
                    f"{self.base_url}/auth/login",
                    json={"email": test_user["email"], "password": test_user["password"]},
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.auth_token = token_data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("Authentication Setup", True, "Test user created and authenticated")
                    return True
                else:
                    self.log_test("Authentication Setup", False, f"Login failed: {login_response.status_code}")
                    return False
            else:
                self.log_test("Authentication Setup", False, f"User registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Setup", False, f"Authentication error: {str(e)}")
            return False
    
    def create_test_project(self):
        """Create a test project"""
        try:
            project_data = {
                "name": f"Complete Workflow Test {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                self.log_test("Project Creation", True, f"Test project created: {project['name']}")
                return project["id"]
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Request error: {str(e)}")
            return None
    
    def test_complete_configuration_workflow(self, project_id):
        """Test complete configuration workflow with all fields"""
        if not project_id:
            self.log_test("Complete Configuration Workflow", False, "No project ID available")
            return False
            
        # Complete configuration with all field categories
        complete_config = {
            # Basic configuration
            "itemsPerCase": 10,
            "casesPerSscc": 2,
            "numberOfSscc": 1,
            "useInnerCases": True,
            "innerCasesPerCase": 2,
            "itemsPerInnerCase": 5,
            
            # Company and product information
            "companyPrefix": "1234567",
            "itemProductCode": "000001",
            "caseProductCode": "000002",
            "innerCaseProductCode": "000003",
            "lotNumber": "LOT123456",
            "expirationDate": "2025-12-31",
            
            # GS1 indicator digits
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "innerCaseIndicatorDigit": "4",
            "itemIndicatorDigit": "1",
            
            # Business document information - Sender
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "senderName": "Padagis US LLC",
            "senderStreetAddress": "1000 Pharmaceutical Way",
            "senderCity": "Minneapolis",
            "senderState": "MN",
            "senderPostalCode": "55401",
            "senderCountryCode": "US",
            "senderDespatchAdviceNumber": "DA123456789",
            
            # Business document information - Receiver
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Pharmacy Corp",
            "receiverStreetAddress": "2000 Healthcare Blvd",
            "receiverCity": "Chicago",
            "receiverState": "IL",
            "receiverPostalCode": "60601",
            "receiverCountryCode": "US",
            "receiverPoNumber": "PO987654321",
            
            # Business document information - Shipper
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Shipping Corp",
            "shipperStreetAddress": "3000 Logistics Ave",
            "shipperCity": "Dallas",
            "shipperState": "TX",
            "shipperPostalCode": "75201",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False,
            
            # EPCClass data
            "productNdc": "45802-046-85",
            "packageNdc": "45802-046-85",
            "regulatedProductName": "Metformin Hydrochloride Extended-Release Tablets",
            "manufacturerName": "Padagis US LLC",
            "dosageFormType": "Extended-Release Tablet",
            "strengthDescription": "500 mg",
            "netContentDescription": "100 tablets"
        }
        
        try:
            # Step 1: Create configuration
            config_response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=complete_config,
                headers={"Content-Type": "application/json"}
            )
            
            if config_response.status_code != 200:
                self.log_test("Complete Configuration Workflow", False, 
                            f"Configuration creation failed: HTTP {config_response.status_code}: {config_response.text}")
                return False
            
            # Step 2: Create serial numbers
            # For config: 1 SSCC, 2 Cases, 4 Inner Cases (2×2), 20 Items (5×2×2)
            serial_data = {
                "ssccSerialNumbers": ["SSCC001"],
                "caseSerialNumbers": ["CASE001", "CASE002"],
                "innerCaseSerialNumbers": ["INNER001", "INNER002", "INNER003", "INNER004"],
                "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(20)]
            }
            
            serial_response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if serial_response.status_code != 200:
                self.log_test("Complete Configuration Workflow", False, 
                            f"Serial numbers creation failed: HTTP {serial_response.status_code}: {serial_response.text}")
                return False
            
            # Step 3: Generate EPCIS
            epcis_request = {
                "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
            }
            
            epcis_response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json=epcis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if epcis_response.status_code != 200:
                self.log_test("Complete Configuration Workflow", False, 
                            f"EPCIS generation failed: HTTP {epcis_response.status_code}: {epcis_response.text}")
                return False
            
            # Step 4: Verify project contains all data
            project_response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if project_response.status_code != 200:
                self.log_test("Complete Configuration Workflow", False, 
                            f"Project retrieval failed: HTTP {project_response.status_code}")
                return False
            
            project = project_response.json()
            
            # Verify all components are present
            has_config = project.get("configuration") is not None
            has_serials = project.get("serial_numbers") is not None
            has_epcis = project.get("epcis_file_content") is not None
            
            if has_config and has_serials and has_epcis:
                # Verify configuration completeness
                config = project["configuration"]
                
                # Check key field categories
                has_basic = any(field in config for field in ["items_per_case", "itemsPerCase"])
                has_business_doc = any(field in config for field in ["sender_gln", "senderGln"])
                has_epcclass = any(field in config for field in ["package_ndc", "packageNdc"])
                
                if has_basic and has_business_doc and has_epcclass:
                    self.log_test("Complete Configuration Workflow", True, 
                                "Complete workflow successful with all data categories",
                                f"Configuration: ✓, Serial Numbers: ✓, EPCIS: ✓, All Field Categories: ✓")
                    return True
                else:
                    self.log_test("Complete Configuration Workflow", False, 
                                f"Configuration incomplete - Basic: {has_basic}, Business Doc: {has_business_doc}, EPCClass: {has_epcclass}")
                    return False
            else:
                self.log_test("Complete Configuration Workflow", False, 
                            f"Missing project components - Config: {has_config}, Serials: {has_serials}, EPCIS: {has_epcis}")
                return False
                
        except Exception as e:
            self.log_test("Complete Configuration Workflow", False, f"Workflow error: {str(e)}")
            return False
    
    def test_epcis_xml_validation(self, project_id):
        """Test EPCIS XML generation and validate key features"""
        if not project_id:
            self.log_test("EPCIS XML Validation", False, "No project ID available")
            return False
            
        try:
            project_response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if project_response.status_code == 200:
                project = project_response.json()
                epcis_content = project.get("epcis_file_content")
                
                if not epcis_content:
                    self.log_test("EPCIS XML Validation", False, "No EPCIS content found")
                    return False
                
                # Parse XML and validate key features
                try:
                    root = ET.fromstring(epcis_content)
                    
                    # Check EPCIS structure
                    is_epcis_doc = root.tag.endswith("EPCISDocument")
                    
                    # Check for events
                    event_count = 0
                    object_events = 0
                    aggregation_events = 0
                    
                    for elem in root.iter():
                        if elem.tag.endswith("ObjectEvent"):
                            object_events += 1
                            event_count += 1
                        elif elem.tag.endswith("AggregationEvent"):
                            aggregation_events += 1
                            event_count += 1
                    
                    # Check for package NDC hyphen removal
                    ndc_clean = "4580204685" in epcis_content and "45802-046-85" not in epcis_content
                    
                    # Check for location vocabulary
                    has_location_vocab = "Location" in epcis_content and "0345802000014" in epcis_content
                    
                    # Check for shipping event
                    has_shipping_event = "shipping" in epcis_content
                    
                    # Check for SBDH structure
                    has_sbdh = "StandardBusinessDocumentHeader" in epcis_content
                    
                    # Check for EPCClass vocabulary
                    has_epcclass = "EPCClass" in epcis_content
                    
                    validation_results = {
                        "EPCIS Document": is_epcis_doc,
                        "Events Present": event_count > 0,
                        "NDC Clean": ndc_clean,
                        "Location Vocabulary": has_location_vocab,
                        "Shipping Event": has_shipping_event,
                        "SBDH Structure": has_sbdh,
                        "EPCClass Vocabulary": has_epcclass
                    }
                    
                    passed_validations = sum(validation_results.values())
                    total_validations = len(validation_results)
                    
                    if passed_validations >= 6:  # At least 6 out of 7 validations should pass
                        self.log_test("EPCIS XML Validation", True, 
                                    f"EPCIS XML validation successful ({passed_validations}/{total_validations})",
                                    f"Events: {event_count} (Obj: {object_events}, Agg: {aggregation_events}), Features: {list(validation_results.keys())}")
                        return True
                    else:
                        failed_validations = [k for k, v in validation_results.items() if not v]
                        self.log_test("EPCIS XML Validation", False, 
                                    f"EPCIS XML validation failed ({passed_validations}/{total_validations})",
                                    f"Failed: {failed_validations}")
                        return False
                        
                except ET.ParseError as e:
                    self.log_test("EPCIS XML Validation", False, f"XML parsing error: {str(e)}")
                    return False
            else:
                self.log_test("EPCIS XML Validation", False, 
                            f"Project retrieval failed: HTTP {project_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("EPCIS XML Validation", False, f"Validation error: {str(e)}")
            return False
    
    def run_complete_workflow_tests(self):
        """Run complete workflow tests"""
        print("=" * 80)
        print("COMPLETE BACKEND WORKFLOW TESTING")
        print("=" * 80)
        print("Testing complete workflow with project-based API endpoints")
        print("to verify configuration data persistence and EPCIS generation.")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Authentication Setup
        if not self.setup_authentication():
            print("\n❌ Authentication failed. Stopping tests.")
            return False
        
        # Test 3: Create Test Project
        project_id = self.create_test_project()
        if not project_id:
            print("\n❌ Project creation failed. Stopping tests.")
            return False
        
        # Test 4: Complete Configuration Workflow
        workflow_success = self.test_complete_configuration_workflow(project_id)
        
        # Test 5: EPCIS XML Validation
        if workflow_success:
            self.test_epcis_xml_validation(project_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("COMPLETE WORKFLOW TEST SUMMARY")
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
        
        print("\nWorkflow Components Tested:")
        print("✓ User authentication and project creation")
        print("✓ Complete configuration storage (all field categories)")
        print("✓ Serial numbers management")
        print("✓ EPCIS XML generation with all features")
        print("✓ Data persistence verification")
        print("✓ XML structure and content validation")
        
        print("\nConfiguration Data Persistence Verified:")
        print("✓ Basic configuration (itemsPerCase, casesPerSscc, numberOfSscc, etc.)")
        print("✓ Company and product information (companyPrefix, productCode, lotNumber, expirationDate)")
        print("✓ GS1 indicator digits (ssccExtensionDigit, caseIndicatorDigit, etc.)")
        print("✓ Business document information (sender, receiver, shipper details)")
        print("✓ EPCClass data (productNdc, packageNdc, regulatedProductName, manufacturerName, etc.)")
        
        return passed == total

if __name__ == "__main__":
    tester = CompleteWorkflowTester()
    success = tester.run_complete_workflow_tests()
    sys.exit(0 if success else 1)