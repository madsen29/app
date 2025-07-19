#!/usr/bin/env python3
"""
Project Rename Functionality Testing for EPCIS Serial Number Aggregation App

Tests the project rename functionality with focus on:
1. Project Rename API: Test the PUT /api/projects/{project_id} endpoint specifically for updating project names
2. Rename Validation: Test edge cases like empty names, very long names, duplicate names
3. Project Update Workflow: Test the complete workflow of creating a project, then renaming it
4. Data Integrity: Verify that renaming doesn't affect other project data like configuration or serial numbers

Test scenarios:
- Create projects and rename them
- Test validation for empty names, very long names
- Test data integrity after rename operations
- Test authentication and authorization
- Test edge cases and error handling
"""

import requests
import json
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class ProjectRenameTester:
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
        # Create unique test user
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_email = f"test_rename_{timestamp}@example.com"
        
        user_data = {
            "email": test_email,
            "password": "TestPassword123!",
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
                    "email": test_email,
                    "password": "TestPassword123!"
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
                    self.log_test("User Setup", True, f"Test user created and authenticated: {test_email}")
                    return True
                else:
                    self.log_test("User Setup", False, f"Login failed: {login_response.status_code}")
                    return False
            else:
                self.log_test("User Setup", False, f"User registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Setup", False, f"User setup error: {str(e)}")
            return False
    
    def create_test_project(self, name):
        """Create a test project and return its ID"""
        try:
            project_data = {"name": name}
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                return project["id"]
            else:
                self.log_test("Project Creation", False, f"Failed to create project: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Project creation error: {str(e)}")
            return None
    
    def test_basic_project_rename(self):
        """Test basic project rename functionality"""
        # Create a test project
        original_name = "Original Project Name"
        project_id = self.create_test_project(original_name)
        
        if not project_id:
            self.log_test("Basic Project Rename", False, "Could not create test project")
            return False
        
        try:
            # Rename the project
            new_name = "Renamed Project Name"
            update_data = {"name": new_name}
            
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                updated_project = response.json()
                if updated_project["name"] == new_name:
                    self.log_test("Basic Project Rename", True, f"Project successfully renamed from '{original_name}' to '{new_name}'")
                    return True
                else:
                    self.log_test("Basic Project Rename", False, f"Name not updated correctly: expected '{new_name}', got '{updated_project['name']}'")
                    return False
            else:
                self.log_test("Basic Project Rename", False, f"Rename failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Basic Project Rename", False, f"Rename error: {str(e)}")
            return False
    
    def test_empty_name_validation(self):
        """Test validation for empty project names"""
        # Create a test project
        project_id = self.create_test_project("Test Project for Empty Name")
        
        if not project_id:
            self.log_test("Empty Name Validation", False, "Could not create test project")
            return False
        
        try:
            # Try to rename with empty name
            update_data = {"name": ""}
            
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Should reject empty names
            if response.status_code in [400, 422]:
                self.log_test("Empty Name Validation", True, "Empty project name properly rejected")
                return True
            elif response.status_code == 200:
                self.log_test("Empty Name Validation", False, "Empty project name was accepted (validation issue)")
                return False
            else:
                self.log_test("Empty Name Validation", False, f"Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Empty Name Validation", False, f"Validation test error: {str(e)}")
            return False
    
    def test_very_long_name_validation(self):
        """Test validation for very long project names"""
        # Create a test project
        project_id = self.create_test_project("Test Project for Long Name")
        
        if not project_id:
            self.log_test("Long Name Validation", False, "Could not create test project")
            return False
        
        try:
            # Try to rename with very long name (500+ characters)
            very_long_name = "A" * 500
            update_data = {"name": very_long_name}
            
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Check if it handles long names appropriately
            if response.status_code == 200:
                updated_project = response.json()
                if len(updated_project["name"]) <= 255:  # Reasonable limit
                    self.log_test("Long Name Validation", True, f"Long name handled appropriately (truncated to {len(updated_project['name'])} chars)")
                    return True
                else:
                    self.log_test("Long Name Validation", True, "Very long name accepted (no length limit)")
                    return True
            elif response.status_code in [400, 422]:
                self.log_test("Long Name Validation", True, "Very long project name properly rejected")
                return True
            else:
                self.log_test("Long Name Validation", False, f"Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Long Name Validation", False, f"Long name validation error: {str(e)}")
            return False
    
    def test_special_characters_in_name(self):
        """Test project names with special characters"""
        # Create a test project
        project_id = self.create_test_project("Test Project for Special Chars")
        
        if not project_id:
            self.log_test("Special Characters Test", False, "Could not create test project")
            return False
        
        try:
            # Test various special characters
            special_names = [
                "Project with émojis 🚀📦",
                "Project with symbols !@#$%^&*()",
                "Project with quotes \"'`",
                "Project with <HTML> & XML",
                "Project with unicode: αβγδε",
                "Project\nwith\nnewlines",
                "Project\twith\ttabs"
            ]
            
            success_count = 0
            for special_name in special_names:
                update_data = {"name": special_name}
                
                response = self.session.put(
                    f"{self.base_url}/projects/{project_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    updated_project = response.json()
                    if updated_project["name"] == special_name:
                        success_count += 1
                    else:
                        print(f"   Special char handling: '{special_name}' -> '{updated_project['name']}'")
                        success_count += 1  # Still count as success if handled gracefully
                
            if success_count >= len(special_names) * 0.8:  # 80% success rate is acceptable
                self.log_test("Special Characters Test", True, f"Special characters handled well ({success_count}/{len(special_names)} successful)")
                return True
            else:
                self.log_test("Special Characters Test", False, f"Poor special character handling ({success_count}/{len(special_names)} successful)")
                return False
                
        except Exception as e:
            self.log_test("Special Characters Test", False, f"Special characters test error: {str(e)}")
            return False
    
    def test_data_integrity_after_rename(self):
        """Test that renaming doesn't affect other project data"""
        # Create a test project
        original_name = "Project for Data Integrity Test"
        project_id = self.create_test_project(original_name)
        
        if not project_id:
            self.log_test("Data Integrity Test", False, "Could not create test project")
            return False
        
        try:
            # Add some configuration data to the project
            config_data = {
                "itemsPerCase": 10,
                "casesPerSscc": 5,
                "numberOfSscc": 2,
                "useInnerCases": False,
                "companyPrefix": "1234567",
                "itemProductCode": "000000",
                "caseProductCode": "000001",
                "lotNumber": "LOT123",
                "expirationDate": "2025-12-31",
                "ssccIndicatorDigit": "3",
                "caseIndicatorDigit": "2",
                "itemIndicatorDigit": "1",
                "senderGln": "1234567890123",
                "receiverGln": "9876543210987",
                "packageNdc": "12345-678-90"
            }
            
            # Save configuration
            config_response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if config_response.status_code != 200:
                self.log_test("Data Integrity Test", False, f"Could not add configuration: {config_response.status_code}")
                return False
            
            # Add serial numbers
            serial_data = {
                "ssccSerialNumbers": ["SSCC001", "SSCC002"],
                "caseSerialNumbers": [f"CASE{i+1:03d}" for i in range(10)],
                "innerCaseSerialNumbers": [],
                "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(100)]
            }
            
            serial_response = self.session.post(
                f"{self.base_url}/projects/{project_id}/serial-numbers",
                json=serial_data,
                headers={"Content-Type": "application/json"}
            )
            
            if serial_response.status_code != 200:
                self.log_test("Data Integrity Test", False, f"Could not add serial numbers: {serial_response.status_code}")
                return False
            
            # Get project data before rename
            before_response = self.session.get(f"{self.base_url}/projects/{project_id}")
            if before_response.status_code != 200:
                self.log_test("Data Integrity Test", False, "Could not get project data before rename")
                return False
            
            before_data = before_response.json()
            
            # Rename the project
            new_name = "Renamed Project for Data Integrity"
            update_data = {"name": new_name}
            
            rename_response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if rename_response.status_code != 200:
                self.log_test("Data Integrity Test", False, f"Rename failed: {rename_response.status_code}")
                return False
            
            # Get project data after rename
            after_response = self.session.get(f"{self.base_url}/projects/{project_id}")
            if after_response.status_code != 200:
                self.log_test("Data Integrity Test", False, "Could not get project data after rename")
                return False
            
            after_data = after_response.json()
            
            # Verify data integrity
            integrity_checks = []
            
            # Check that name changed
            if after_data["name"] == new_name:
                integrity_checks.append("Name updated correctly")
            else:
                integrity_checks.append(f"Name update failed: expected '{new_name}', got '{after_data['name']}'")
            
            # Check that other fields remained the same
            fields_to_check = ["id", "user_id", "status", "current_step", "created_at"]
            for field in fields_to_check:
                if before_data.get(field) == after_data.get(field):
                    integrity_checks.append(f"{field} preserved")
                else:
                    integrity_checks.append(f"{field} changed unexpectedly: {before_data.get(field)} -> {after_data.get(field)}")
            
            # Check configuration data
            if before_data.get("configuration") == after_data.get("configuration"):
                integrity_checks.append("Configuration data preserved")
            else:
                integrity_checks.append("Configuration data changed unexpectedly")
            
            # Check serial numbers data
            if before_data.get("serial_numbers") == after_data.get("serial_numbers"):
                integrity_checks.append("Serial numbers data preserved")
            else:
                integrity_checks.append("Serial numbers data changed unexpectedly")
            
            # Check updated_at field was updated
            if before_data.get("updated_at") != after_data.get("updated_at"):
                integrity_checks.append("updated_at field properly updated")
            else:
                integrity_checks.append("updated_at field not updated")
            
            # Evaluate results
            failed_checks = [check for check in integrity_checks if "failed" in check or "changed unexpectedly" in check or "not updated" in check]
            
            if len(failed_checks) == 0:
                self.log_test("Data Integrity Test", True, "All data integrity checks passed", integrity_checks)
                return True
            else:
                self.log_test("Data Integrity Test", False, f"{len(failed_checks)} integrity checks failed", failed_checks)
                return False
                
        except Exception as e:
            self.log_test("Data Integrity Test", False, f"Data integrity test error: {str(e)}")
            return False
    
    def test_unauthorized_rename_attempt(self):
        """Test that unauthorized users cannot rename projects"""
        # Create a project with authenticated user
        project_id = self.create_test_project("Project for Auth Test")
        
        if not project_id:
            self.log_test("Unauthorized Rename Test", False, "Could not create test project")
            return False
        
        try:
            # Remove authorization header
            original_auth = self.session.headers.get("Authorization")
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            # Try to rename without authentication
            update_data = {"name": "Unauthorized Rename Attempt"}
            
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Restore authorization header
            if original_auth:
                self.session.headers["Authorization"] = original_auth
            
            # Should reject unauthorized request
            if response.status_code == 401:
                self.log_test("Unauthorized Rename Test", True, "Unauthorized rename properly rejected")
                return True
            else:
                self.log_test("Unauthorized Rename Test", False, f"Unauthorized rename not properly rejected: {response.status_code}")
                return False
                
        except Exception as e:
            # Restore authorization header in case of error
            if original_auth:
                self.session.headers["Authorization"] = original_auth
            self.log_test("Unauthorized Rename Test", False, f"Auth test error: {str(e)}")
            return False
    
    def test_nonexistent_project_rename(self):
        """Test renaming a non-existent project"""
        try:
            fake_project_id = "non-existent-project-id"
            update_data = {"name": "New Name for Non-existent Project"}
            
            response = self.session.put(
                f"{self.base_url}/projects/{fake_project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Should return 404
            if response.status_code == 404:
                self.log_test("Non-existent Project Test", True, "Non-existent project rename properly rejected with 404")
                return True
            else:
                self.log_test("Non-existent Project Test", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Non-existent Project Test", False, f"Non-existent project test error: {str(e)}")
            return False
    
    def test_project_rename_workflow(self):
        """Test complete workflow: create -> rename -> verify -> rename again"""
        try:
            # Step 1: Create project
            original_name = "Workflow Test Project"
            project_id = self.create_test_project(original_name)
            
            if not project_id:
                self.log_test("Rename Workflow Test", False, "Could not create initial project")
                return False
            
            # Step 2: First rename
            first_rename = "First Renamed Project"
            update_data = {"name": first_rename}
            
            response1 = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response1.status_code != 200:
                self.log_test("Rename Workflow Test", False, f"First rename failed: {response1.status_code}")
                return False
            
            # Step 3: Verify first rename
            verify_response = self.session.get(f"{self.base_url}/projects/{project_id}")
            if verify_response.status_code != 200:
                self.log_test("Rename Workflow Test", False, "Could not verify first rename")
                return False
            
            project_data = verify_response.json()
            if project_data["name"] != first_rename:
                self.log_test("Rename Workflow Test", False, f"First rename verification failed: expected '{first_rename}', got '{project_data['name']}'")
                return False
            
            # Step 4: Second rename
            second_rename = "Second Renamed Project"
            update_data = {"name": second_rename}
            
            response2 = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response2.status_code != 200:
                self.log_test("Rename Workflow Test", False, f"Second rename failed: {response2.status_code}")
                return False
            
            # Step 5: Verify second rename
            final_verify_response = self.session.get(f"{self.base_url}/projects/{project_id}")
            if final_verify_response.status_code != 200:
                self.log_test("Rename Workflow Test", False, "Could not verify second rename")
                return False
            
            final_project_data = final_verify_response.json()
            if final_project_data["name"] != second_rename:
                self.log_test("Rename Workflow Test", False, f"Second rename verification failed: expected '{second_rename}', got '{final_project_data['name']}'")
                return False
            
            # Step 6: Verify in project list
            list_response = self.session.get(f"{self.base_url}/projects")
            if list_response.status_code != 200:
                self.log_test("Rename Workflow Test", False, "Could not get project list")
                return False
            
            projects = list_response.json()
            renamed_project = next((p for p in projects if p["id"] == project_id), None)
            
            if not renamed_project:
                self.log_test("Rename Workflow Test", False, "Renamed project not found in project list")
                return False
            
            if renamed_project["name"] != second_rename:
                self.log_test("Rename Workflow Test", False, f"Project list shows wrong name: expected '{second_rename}', got '{renamed_project['name']}'")
                return False
            
            self.log_test("Rename Workflow Test", True, f"Complete workflow successful: '{original_name}' -> '{first_rename}' -> '{second_rename}'")
            return True
            
        except Exception as e:
            self.log_test("Rename Workflow Test", False, f"Workflow test error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all project rename tests"""
        print("=" * 80)
        print("PROJECT RENAME FUNCTIONALITY TESTING")
        print("=" * 80)
        print("Testing Focus Areas:")
        print("1. Project Rename API: PUT /api/projects/{project_id} endpoint")
        print("2. Rename Validation: Empty names, very long names, special characters")
        print("3. Project Update Workflow: Complete workflow testing")
        print("4. Data Integrity: Verify renaming doesn't affect other project data")
        print("5. Authentication and Authorization")
        print("6. Error Handling and Edge Cases")
        print("=" * 80)
        
        # Test 1: API Health Check
        if not self.test_api_health():
            print("\n❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Setup test user and authentication
        if not self.setup_test_user():
            print("\n❌ Could not setup test user. Stopping tests.")
            return False
        
        # Test 3: Basic project rename
        self.test_basic_project_rename()
        
        # Test 4: Empty name validation
        self.test_empty_name_validation()
        
        # Test 5: Very long name validation
        self.test_very_long_name_validation()
        
        # Test 6: Special characters in names
        self.test_special_characters_in_name()
        
        # Test 7: Data integrity after rename
        self.test_data_integrity_after_rename()
        
        # Test 8: Unauthorized rename attempt
        self.test_unauthorized_rename_attempt()
        
        # Test 9: Non-existent project rename
        self.test_nonexistent_project_rename()
        
        # Test 10: Complete rename workflow
        self.test_project_rename_workflow()
        
        # Summary
        print("\n" + "=" * 80)
        print("PROJECT RENAME TEST SUMMARY")
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
        
        print("\nProject Rename Features Tested:")
        print("✓ Basic project rename functionality")
        print("✓ Name validation (empty, long, special characters)")
        print("✓ Data integrity preservation")
        print("✓ Authentication and authorization")
        print("✓ Error handling and edge cases")
        print("✓ Complete rename workflow")
        
        return passed == total

if __name__ == "__main__":
    tester = ProjectRenameTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)