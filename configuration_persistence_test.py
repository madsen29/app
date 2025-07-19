#!/usr/bin/env python3
"""
Configuration Data Persistence Testing for EPCIS Serial Number Aggregation App

This test specifically addresses the review request to verify that the Step 1 configuration 
data loss issue has been resolved. Tests focus on:

1. Complete Configuration Storage - all configuration fields are properly saved and persisted
2. API Endpoint Testing - POST /api/projects/{project_id}/configuration, PUT /api/projects/{project_id}, GET /api/projects/{project_id}
3. Configuration Persistence Scenarios - across project creation, updates, and complete configuration object storage
4. Data Integrity - verify complete configuration object is stored, not just structural parameters

Configuration fields tested include:
- Basic configuration (itemsPerCase, casesPerSscc, numberOfSscc, etc.)
- Company and product information (companyPrefix, productCode, lotNumber, expirationDate)
- GS1 indicator digits (ssccExtensionDigit, caseIndicatorDigit, etc.)
- Business document information (sender, receiver, shipper details with company prefixes, GLNs, SGLNs, addresses, etc.)
- EPCClass data (productNdc, packageNdc, regulatedProductName, manufacturerName, etc.)
"""

import requests
import json
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class ConfigurationPersistenceTester:
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
        # Create test user
        test_user = {
            "email": f"configtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
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
                "name": f"Configuration Persistence Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
    
    def get_complete_test_configuration(self):
        """Get a complete configuration with all possible fields filled out"""
        return {
            # Basic configuration
            "itemsPerCase": 10,
            "casesPerSscc": 5,
            "numberOfSscc": 2,
            "useInnerCases": True,
            "innerCasesPerCase": 3,
            "itemsPerInnerCase": 4,
            
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
    
    def test_configuration_creation_complete_data(self, project_id):
        """Test POST /api/projects/{project_id}/configuration with complete configuration data"""
        if not project_id:
            self.log_test("Configuration Creation - Complete Data", False, "No project ID available")
            return None
            
        complete_config = self.get_complete_test_configuration()
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=complete_config,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                saved_config = response.json()
                
                # Verify all fields are present and correct
                missing_fields = []
                incorrect_fields = []
                
                for key, expected_value in complete_config.items():
                    # Convert camelCase to snake_case for comparison
                    snake_case_key = self.camel_to_snake(key)
                    
                    if snake_case_key not in saved_config and key not in saved_config:
                        missing_fields.append(key)
                    else:
                        # Check both camelCase and snake_case versions
                        saved_value = saved_config.get(snake_case_key, saved_config.get(key))
                        if saved_value != expected_value:
                            incorrect_fields.append(f"{key}: expected '{expected_value}', got '{saved_value}'")
                
                if not missing_fields and not incorrect_fields:
                    self.log_test("Configuration Creation - Complete Data", True, 
                                "All configuration fields saved correctly",
                                f"Saved {len(complete_config)} fields successfully")
                    return saved_config["id"]
                else:
                    error_details = []
                    if missing_fields:
                        error_details.append(f"Missing fields: {missing_fields}")
                    if incorrect_fields:
                        error_details.append(f"Incorrect fields: {incorrect_fields}")
                    
                    self.log_test("Configuration Creation - Complete Data", False, 
                                "Configuration data incomplete or incorrect",
                                "; ".join(error_details))
                    return None
            else:
                self.log_test("Configuration Creation - Complete Data", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration Creation - Complete Data", False, f"Request error: {str(e)}")
            return None
    
    def test_project_retrieval_complete_configuration(self, project_id):
        """Test GET /api/projects/{project_id} to verify complete configuration is retrieved"""
        if not project_id:
            self.log_test("Project Retrieval - Complete Configuration", False, "No project ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                project = response.json()
                
                if "configuration" not in project or not project["configuration"]:
                    self.log_test("Project Retrieval - Complete Configuration", False, 
                                "No configuration found in project")
                    return False
                
                config = project["configuration"]
                expected_config = self.get_complete_test_configuration()
                
                # Verify all fields are present
                missing_fields = []
                incorrect_fields = []
                
                for key, expected_value in expected_config.items():
                    snake_case_key = self.camel_to_snake(key)
                    
                    if snake_case_key not in config and key not in config:
                        missing_fields.append(key)
                    else:
                        saved_value = config.get(snake_case_key, config.get(key))
                        if saved_value != expected_value:
                            incorrect_fields.append(f"{key}: expected '{expected_value}', got '{saved_value}'")
                
                if not missing_fields and not incorrect_fields:
                    self.log_test("Project Retrieval - Complete Configuration", True, 
                                "Complete configuration retrieved successfully",
                                f"Retrieved {len(expected_config)} fields correctly")
                    return True
                else:
                    error_details = []
                    if missing_fields:
                        error_details.append(f"Missing fields: {missing_fields}")
                    if incorrect_fields:
                        error_details.append(f"Incorrect fields: {incorrect_fields}")
                    
                    self.log_test("Project Retrieval - Complete Configuration", False, 
                                "Configuration data incomplete or incorrect in project retrieval",
                                "; ".join(error_details))
                    return False
            else:
                self.log_test("Project Retrieval - Complete Configuration", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Retrieval - Complete Configuration", False, f"Request error: {str(e)}")
            return False
    
    def test_project_update_configuration_persistence(self, project_id):
        """Test PUT /api/projects/{project_id} to verify configuration persists through updates"""
        if not project_id:
            self.log_test("Project Update - Configuration Persistence", False, "No project ID available")
            return False
            
        # Update project with new name but keep configuration
        update_data = {
            "name": f"Updated Project Name {datetime.now().strftime('%H%M%S')}",
            "status": "In Progress"
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                updated_project = response.json()
                
                # Verify configuration is still present and complete
                if "configuration" not in updated_project or not updated_project["configuration"]:
                    self.log_test("Project Update - Configuration Persistence", False, 
                                "Configuration lost during project update")
                    return False
                
                config = updated_project["configuration"]
                expected_config = self.get_complete_test_configuration()
                
                # Verify all fields are still present
                missing_fields = []
                for key in expected_config.keys():
                    snake_case_key = self.camel_to_snake(key)
                    if snake_case_key not in config and key not in config:
                        missing_fields.append(key)
                
                if not missing_fields:
                    self.log_test("Project Update - Configuration Persistence", True, 
                                "Configuration persisted through project update",
                                f"All {len(expected_config)} fields preserved")
                    return True
                else:
                    self.log_test("Project Update - Configuration Persistence", False, 
                                "Some configuration fields lost during update",
                                f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Project Update - Configuration Persistence", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Update - Configuration Persistence", False, f"Request error: {str(e)}")
            return False
    
    def test_configuration_vs_structural_parameters(self, project_id):
        """Test that complete configuration object is stored, not just structural parameters"""
        if not project_id:
            self.log_test("Configuration vs Structural Parameters", False, "No project ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                project = response.json()
                config = project.get("configuration", {})
                
                # Define structural parameters (basic configuration)
                structural_params = [
                    "itemsPerCase", "items_per_case",
                    "casesPerSscc", "cases_per_sscc", 
                    "numberOfSscc", "number_of_sscc",
                    "useInnerCases", "use_inner_cases"
                ]
                
                # Define detailed configuration fields (non-structural)
                detailed_fields = [
                    # Business document fields
                    "senderCompanyPrefix", "sender_company_prefix",
                    "senderGln", "sender_gln",
                    "senderName", "sender_name",
                    "receiverCompanyPrefix", "receiver_company_prefix",
                    "receiverGln", "receiver_gln",
                    "shipperCompanyPrefix", "shipper_company_prefix",
                    # EPCClass fields
                    "regulatedProductName", "regulated_product_name",
                    "manufacturerName", "manufacturer_name",
                    "packageNdc", "package_ndc",
                    "dosageFormType", "dosage_form_type"
                ]
                
                # Check if detailed fields are present
                detailed_fields_present = []
                for field in detailed_fields:
                    if field in config and config[field]:
                        detailed_fields_present.append(field)
                
                if len(detailed_fields_present) >= 8:  # At least 8 detailed fields should be present
                    self.log_test("Configuration vs Structural Parameters", True, 
                                "Complete configuration object stored (not just structural parameters)",
                                f"Found {len(detailed_fields_present)} detailed configuration fields")
                    return True
                else:
                    self.log_test("Configuration vs Structural Parameters", False, 
                                "Only structural parameters stored, detailed configuration missing",
                                f"Only found {len(detailed_fields_present)} detailed fields: {detailed_fields_present}")
                    return False
            else:
                self.log_test("Configuration vs Structural Parameters", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration vs Structural Parameters", False, f"Request error: {str(e)}")
            return False
    
    def test_configuration_field_categories(self, project_id):
        """Test that all categories of configuration fields are properly stored"""
        if not project_id:
            self.log_test("Configuration Field Categories", False, "No project ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                project = response.json()
                config = project.get("configuration", {})
                
                # Define field categories
                categories = {
                    "Basic Configuration": [
                        ("itemsPerCase", "items_per_case"),
                        ("casesPerSscc", "cases_per_sscc"),
                        ("numberOfSscc", "number_of_sscc")
                    ],
                    "Company/Product Information": [
                        ("companyPrefix", "company_prefix"),
                        ("lotNumber", "lot_number"),
                        ("expirationDate", "expiration_date")
                    ],
                    "GS1 Indicator Digits": [
                        ("ssccIndicatorDigit", "sscc_indicator_digit"),
                        ("caseIndicatorDigit", "case_indicator_digit"),
                        ("itemIndicatorDigit", "item_indicator_digit")
                    ],
                    "Business Document - Sender": [
                        ("senderCompanyPrefix", "sender_company_prefix"),
                        ("senderGln", "sender_gln"),
                        ("senderName", "sender_name")
                    ],
                    "Business Document - Receiver": [
                        ("receiverCompanyPrefix", "receiver_company_prefix"),
                        ("receiverGln", "receiver_gln"),
                        ("receiverName", "receiver_name")
                    ],
                    "Business Document - Shipper": [
                        ("shipperCompanyPrefix", "shipper_company_prefix"),
                        ("shipperGln", "shipper_gln"),
                        ("shipperName", "shipper_name")
                    ],
                    "EPCClass Data": [
                        ("packageNdc", "package_ndc"),
                        ("regulatedProductName", "regulated_product_name"),
                        ("manufacturerName", "manufacturer_name")
                    ]
                }
                
                category_results = {}
                
                for category_name, fields in categories.items():
                    present_fields = 0
                    total_fields = len(fields)
                    
                    for camel_case, snake_case in fields:
                        if (camel_case in config and config[camel_case]) or (snake_case in config and config[snake_case]):
                            present_fields += 1
                    
                    category_results[category_name] = {
                        "present": present_fields,
                        "total": total_fields,
                        "percentage": (present_fields / total_fields) * 100
                    }
                
                # Check if all categories have good coverage (at least 80% of fields present)
                all_categories_good = True
                category_details = []
                
                for category, result in category_results.items():
                    if result["percentage"] < 80:
                        all_categories_good = False
                    category_details.append(f"{category}: {result['present']}/{result['total']} ({result['percentage']:.1f}%)")
                
                if all_categories_good:
                    self.log_test("Configuration Field Categories", True, 
                                "All configuration field categories properly stored",
                                "; ".join(category_details))
                    return True
                else:
                    self.log_test("Configuration Field Categories", False, 
                                "Some configuration field categories incomplete",
                                "; ".join(category_details))
                    return False
            else:
                self.log_test("Configuration Field Categories", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Configuration Field Categories", False, f"Request error: {str(e)}")
            return False
    
    def camel_to_snake(self, camel_str):
        """Convert camelCase to snake_case"""
        result = []
        for i, char in enumerate(camel_str):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)
    
    def run_configuration_persistence_tests(self):
        """Run comprehensive configuration persistence tests"""
        print("=" * 80)
        print("CONFIGURATION DATA PERSISTENCE TESTING")
        print("=" * 80)
        print("Testing complete configuration storage and retrieval to verify")
        print("that the Step 1 configuration data loss issue has been resolved.")
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
        
        # Test 4: Configuration Creation with Complete Data
        config_id = self.test_configuration_creation_complete_data(project_id)
        
        # Test 5: Project Retrieval with Complete Configuration
        self.test_project_retrieval_complete_configuration(project_id)
        
        # Test 6: Project Update - Configuration Persistence
        self.test_project_update_configuration_persistence(project_id)
        
        # Test 7: Configuration vs Structural Parameters
        self.test_configuration_vs_structural_parameters(project_id)
        
        # Test 8: Configuration Field Categories
        self.test_configuration_field_categories(project_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("CONFIGURATION PERSISTENCE TEST SUMMARY")
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
        
        print("\nConfiguration Fields Tested:")
        print("✓ Basic configuration (itemsPerCase, casesPerSscc, numberOfSscc, etc.)")
        print("✓ Company and product information (companyPrefix, productCode, lotNumber, expirationDate)")
        print("✓ GS1 indicator digits (ssccExtensionDigit, caseIndicatorDigit, etc.)")
        print("✓ Business document information (sender, receiver, shipper details)")
        print("✓ EPCClass data (productNdc, packageNdc, regulatedProductName, manufacturerName, etc.)")
        
        print("\nAPI Endpoints Tested:")
        print("✓ POST /api/projects/{project_id}/configuration")
        print("✓ PUT /api/projects/{project_id}")
        print("✓ GET /api/projects/{project_id}")
        
        return passed == total

if __name__ == "__main__":
    tester = ConfigurationPersistenceTester()
    success = tester.run_configuration_persistence_tests()
    sys.exit(0 if success else 1)