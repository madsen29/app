#!/usr/bin/env python3
"""
Auto-Save Backend API Testing for EPCIS Serial Number Aggregation App
Tests the auto-save functionality changes to ensure no regressions in existing functionality.

Focus areas from review request:
1. Project Management: Test project creation, updating, and retrieval
2. Configuration Management: Test configuration creation and updates  
3. Serial Numbers Management: Test serial numbers creation and updates
4. Auto-save Scenarios: Test rapid successive updates to verify backend can handle frequent auto-save requests

Test scenarios:
- Basic API connectivity and health checks
- User authentication flow
- Project CRUD operations
- Configuration creation and updates
- Serial numbers creation and updates
- Rapid successive updates (auto-save simulation)
- EPCIS generation functionality
- Data persistence verification
"""

import requests
import json
import time
import threading
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class AutoSaveBackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_email = "autosave.test@example.com"
        self.test_user_password = "TestPassword123!"
        
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
    
    def test_user_authentication(self):
        """Test user registration and login flow"""
        # First, try to register a test user
        user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "firstName": "AutoSave",
            "lastName": "Tester",
            "companyName": "Test Company",
            "streetAddress": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "postalCode": "12345",
            "countryCode": "US"
        }
        
        try:
            # Try registration (might fail if user exists)
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Now try login
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("User Authentication", True, "User login successful")
                    return True
                else:
                    self.log_test("User Authentication", False, "No access token in response")
                    return False
            else:
                self.log_test("User Authentication", False, f"Login failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_project_management(self):
        """Test project CRUD operations"""
        if not self.auth_token:
            self.log_test("Project Management", False, "No authentication token available")
            return None
            
        # Test project creation
        project_data = {
            "name": f"Auto-Save Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        try:
            # Create project
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                project_id = project.get("id")
                self.log_test("Project Creation", True, f"Project created successfully", f"ID: {project_id}")
                
                # Test project retrieval
                response = self.session.get(f"{self.base_url}/projects/{project_id}")
                if response.status_code == 200:
                    retrieved_project = response.json()
                    if retrieved_project.get("id") == project_id:
                        self.log_test("Project Retrieval", True, "Project retrieved successfully")
                    else:
                        self.log_test("Project Retrieval", False, "Retrieved project ID mismatch")
                        return None
                else:
                    self.log_test("Project Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                    return None
                
                # Test project update
                update_data = {
                    "name": f"Updated {project_data['name']}",
                    "current_step": 2
                }
                
                response = self.session.put(
                    f"{self.base_url}/projects/{project_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    updated_project = response.json()
                    if updated_project.get("name") == update_data["name"]:
                        self.log_test("Project Update", True, "Project updated successfully")
                        return project_id
                    else:
                        self.log_test("Project Update", False, "Project name not updated correctly")
                        return None
                else:
                    self.log_test("Project Update", False, f"HTTP {response.status_code}: {response.text}")
                    return None
                    
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Project Management", False, f"Request error: {str(e)}")
            return None
    
    def test_configuration_management(self, project_id):
        """Test configuration creation and updates"""
        if not project_id:
            self.log_test("Configuration Management", False, "No project ID available")
            return None
            
        # Test configuration creation
        config_data = {
            "itemsPerCase": 10,
            "casesPerSscc": 2,
            "numberOfSscc": 1,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000001",
            "lotNumber": "LOT123",
            "expirationDate": "2025-12-31",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
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
            "packageNdc": "45802-046-85",
            "regulatedProductName": "Test Medication",
            "manufacturerName": "Test Pharma Inc",
            "dosageFormType": "Tablet",
            "strengthDescription": "10mg",
            "netContentDescription": "30 tablets"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                config = response.json()
                self.log_test("Configuration Creation", True, "Configuration created successfully", 
                            f"Company Prefix: {config.get('company_prefix')}, Items per Case: {config.get('items_per_case')}")
                return config.get("id")
            else:
                self.log_test("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Configuration Management", False, f"Request error: {str(e)}")
            return None
    
    def test_serial_numbers_management(self, project_id):
        """Test serial numbers creation and updates"""
        if not project_id:
            self.log_test("Serial Numbers Management", False, "No project ID available")
            return None
            
        # For the configuration: 1 SSCC, 2 Cases, 10 Items per Case = 20 total items
        serial_data = {
            "ssccSerialNumbers": ["SSCC001"],
            "caseSerialNumbers": ["CASE001", "CASE002"],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(20)]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                serials = response.json()
                if (len(serials["sscc_serial_numbers"]) == 1 and 
                    len(serials["case_serial_numbers"]) == 2 and
                    len(serials["item_serial_numbers"]) == 20):
                    self.log_test("Serial Numbers Creation", True, "Serial numbers created successfully",
                                f"SSCC: {len(serials['sscc_serial_numbers'])}, Cases: {len(serials['case_serial_numbers'])}, Items: {len(serials['item_serial_numbers'])}")
                    return serials.get("id")
                else:
                    self.log_test("Serial Numbers Creation", False, "Serial number counts don't match expected values")
                    return None
            else:
                self.log_test("Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Serial Numbers Management", False, f"Request error: {str(e)}")
            return None
    
    def test_rapid_successive_updates(self, project_id):
        """Test rapid successive updates to simulate auto-save functionality"""
        if not project_id:
            self.log_test("Rapid Successive Updates", False, "No project ID available")
            return False
            
        success_count = 0
        total_requests = 10
        request_interval = 0.1  # 100ms between requests
        
        try:
            for i in range(total_requests):
                update_data = {
                    "name": f"Auto-Save Update {i+1}",
                    "current_step": (i % 3) + 1,  # Cycle through steps 1, 2, 3
                    "configuration": {
                        "test_field": f"auto_save_value_{i+1}",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                response = self.session.put(
                    f"{self.base_url}/projects/{project_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    print(f"   Update {i+1} failed: HTTP {response.status_code}")
                
                time.sleep(request_interval)
            
            success_rate = (success_count / total_requests) * 100
            if success_rate >= 90:  # Allow for some failures due to network issues
                self.log_test("Rapid Successive Updates", True, 
                            f"Auto-save simulation successful: {success_count}/{total_requests} requests succeeded ({success_rate:.1f}%)")
                return True
            else:
                self.log_test("Rapid Successive Updates", False, 
                            f"Auto-save simulation failed: only {success_count}/{total_requests} requests succeeded ({success_rate:.1f}%)")
                return False
                
        except Exception as e:
            self.log_test("Rapid Successive Updates", False, f"Request error: {str(e)}")
            return False
    
    def test_concurrent_updates(self, project_id):
        """Test concurrent updates to simulate multiple auto-save requests"""
        if not project_id:
            self.log_test("Concurrent Updates", False, "No project ID available")
            return False
            
        results = []
        
        def update_project(thread_id):
            try:
                # Create a new session for each thread
                session = requests.Session()
                session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                update_data = {
                    "name": f"Concurrent Update Thread {thread_id}",
                    "configuration": {
                        "thread_id": thread_id,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                response = session.put(
                    f"{self.base_url}/projects/{project_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                results.append({
                    "thread_id": thread_id,
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                })
                
            except Exception as e:
                results.append({
                    "thread_id": thread_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Create 5 concurrent threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_project, args=(i+1,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Analyze results
        successful_updates = sum(1 for result in results if result["success"])
        total_updates = len(results)
        success_rate = (successful_updates / total_updates) * 100
        
        if success_rate >= 80:  # Allow for some failures in concurrent scenarios
            self.log_test("Concurrent Updates", True, 
                        f"Concurrent auto-save simulation successful: {successful_updates}/{total_updates} requests succeeded ({success_rate:.1f}%)")
            return True
        else:
            self.log_test("Concurrent Updates", False, 
                        f"Concurrent auto-save simulation failed: only {successful_updates}/{total_updates} requests succeeded ({success_rate:.1f}%)")
            return False
    
    def test_epcis_generation(self, project_id):
        """Test EPCIS generation functionality"""
        if not project_id:
            self.log_test("EPCIS Generation", False, "No project ID available")
            return False
            
        epcis_data = {
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/generate-epcis",
                json=epcis_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Check if response contains XML content
                content = response.text
                if "<?xml" in content and "EPCISDocument" in content:
                    # Check for filename in headers
                    content_disposition = response.headers.get("Content-Disposition", "")
                    if "filename=" in content_disposition:
                        self.log_test("EPCIS Generation", True, "EPCIS XML generated successfully with proper filename")
                        return True
                    else:
                        self.log_test("EPCIS Generation", True, "EPCIS XML generated successfully (no filename header)")
                        return True
                else:
                    self.log_test("EPCIS Generation", False, "Response doesn't contain valid EPCIS XML")
                    return False
            else:
                self.log_test("EPCIS Generation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("EPCIS Generation", False, f"Request error: {str(e)}")
            return False
    
    def test_data_persistence(self, project_id):
        """Test data persistence after multiple updates"""
        if not project_id:
            self.log_test("Data Persistence", False, "No project ID available")
            return False
            
        try:
            # Get current project state
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            if response.status_code == 200:
                project = response.json()
                
                # Verify project has expected data
                has_configuration = project.get("configuration") is not None
                has_serial_numbers = project.get("serial_numbers") is not None
                has_updated_name = "Update" in project.get("name", "")
                
                if has_configuration and has_serial_numbers and has_updated_name:
                    self.log_test("Data Persistence", True, "All project data persisted correctly after multiple updates")
                    return True
                else:
                    missing_data = []
                    if not has_configuration:
                        missing_data.append("configuration")
                    if not has_serial_numbers:
                        missing_data.append("serial_numbers")
                    if not has_updated_name:
                        missing_data.append("updated_name")
                    
                    self.log_test("Data Persistence", False, f"Missing data after updates: {', '.join(missing_data)}")
                    return False
            else:
                self.log_test("Data Persistence", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Data Persistence", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all auto-save backend tests"""
        print("🚀 Starting Auto-Save Backend API Tests...")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_api_health():
            print("❌ API health check failed. Stopping tests.")
            return False
        
        # Authentication
        if not self.test_user_authentication():
            print("❌ Authentication failed. Stopping tests.")
            return False
        
        # Project management
        project_id = self.test_project_management()
        if not project_id:
            print("❌ Project management tests failed. Stopping tests.")
            return False
        
        # Configuration management
        config_id = self.test_configuration_management(project_id)
        if not config_id:
            print("❌ Configuration management tests failed. Continuing with other tests.")
        
        # Serial numbers management
        serial_id = self.test_serial_numbers_management(project_id)
        if not serial_id:
            print("❌ Serial numbers management tests failed. Continuing with other tests.")
        
        # Auto-save specific tests
        self.test_rapid_successive_updates(project_id)
        self.test_concurrent_updates(project_id)
        
        # EPCIS generation
        self.test_epcis_generation(project_id)
        
        # Data persistence verification
        self.test_data_persistence(project_id)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return success_rate >= 80  # Consider 80% success rate as acceptable

if __name__ == "__main__":
    tester = AutoSaveBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)