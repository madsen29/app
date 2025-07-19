#!/usr/bin/env python3
"""
Additional Project Rename Edge Case Testing

Focus on specific edge cases and validation scenarios for project rename functionality.
"""

import requests
import json
from datetime import datetime
import sys

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class ProjectRenameEdgeCaseTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        
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
        """Create a test user and authenticate"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_email = f"test_edge_{timestamp}@example.com"
        
        user_data = {
            "email": test_email,
            "password": "TestPassword123!",
            "firstName": "Edge",
            "lastName": "Tester",
            "companyName": "Edge Test Company"
        }
        
        try:
            # Register user
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
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
                    return True
            return False
        except:
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
            return None
        except:
            return None
    
    def test_duplicate_project_names(self):
        """Test if duplicate project names are allowed"""
        try:
            # Create first project
            project_name = "Duplicate Name Test"
            project1_id = self.create_test_project(project_name)
            
            if not project1_id:
                self.log_test("Duplicate Names Test", False, "Could not create first project")
                return False
            
            # Create second project with same name
            project2_id = self.create_test_project(project_name)
            
            if not project2_id:
                self.log_test("Duplicate Names Test", False, "Could not create second project")
                return False
            
            # Try to rename first project to same name as second
            update_data = {"name": project_name}
            response = self.session.put(
                f"{self.base_url}/projects/{project1_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.log_test("Duplicate Names Test", True, "Duplicate project names are allowed (no uniqueness constraint)")
                return True
            else:
                self.log_test("Duplicate Names Test", True, f"Duplicate names rejected with status {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Duplicate Names Test", False, f"Test error: {str(e)}")
            return False
    
    def test_whitespace_only_names(self):
        """Test project names with only whitespace"""
        project_id = self.create_test_project("Whitespace Test Project")
        
        if not project_id:
            self.log_test("Whitespace Names Test", False, "Could not create test project")
            return False
        
        try:
            whitespace_names = [
                "   ",  # spaces only
                "\t\t\t",  # tabs only
                "\n\n\n",  # newlines only
                " \t \n ",  # mixed whitespace
            ]
            
            results = []
            for ws_name in whitespace_names:
                update_data = {"name": ws_name}
                response = self.session.put(
                    f"{self.base_url}/projects/{project_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    updated_project = response.json()
                    results.append(f"'{ws_name}' -> '{updated_project['name']}'")
                else:
                    results.append(f"'{ws_name}' rejected with {response.status_code}")
            
            self.log_test("Whitespace Names Test", True, "Whitespace name handling tested", results)
            return True
            
        except Exception as e:
            self.log_test("Whitespace Names Test", False, f"Test error: {str(e)}")
            return False
    
    def test_null_and_missing_name_field(self):
        """Test null and missing name field in update request"""
        project_id = self.create_test_project("Null Test Project")
        
        if not project_id:
            self.log_test("Null/Missing Name Test", False, "Could not create test project")
            return False
        
        try:
            # Test with null name
            update_data = {"name": None}
            response1 = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Test with missing name field
            update_data = {"status": "In Progress"}  # Update without name field
            response2 = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            results = [
                f"Null name: {response1.status_code}",
                f"Missing name field: {response2.status_code}"
            ]
            
            self.log_test("Null/Missing Name Test", True, "Null and missing name field handling tested", results)
            return True
            
        except Exception as e:
            self.log_test("Null/Missing Name Test", False, f"Test error: {str(e)}")
            return False
    
    def test_concurrent_rename_operations(self):
        """Test concurrent rename operations on the same project"""
        project_id = self.create_test_project("Concurrent Test Project")
        
        if not project_id:
            self.log_test("Concurrent Rename Test", False, "Could not create test project")
            return False
        
        try:
            import threading
            import time
            
            results = []
            
            def rename_project(new_name, result_list):
                try:
                    update_data = {"name": new_name}
                    response = self.session.put(
                        f"{self.base_url}/projects/{project_id}",
                        json=update_data,
                        headers={"Content-Type": "application/json"}
                    )
                    result_list.append((new_name, response.status_code))
                except Exception as e:
                    result_list.append((new_name, f"Error: {str(e)}"))
            
            # Start multiple concurrent rename operations
            threads = []
            for i in range(3):
                thread = threading.Thread(
                    target=rename_project, 
                    args=(f"Concurrent Name {i+1}", results)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check final project name
            final_response = self.session.get(f"{self.base_url}/projects/{project_id}")
            if final_response.status_code == 200:
                final_name = final_response.json()["name"]
                results.append(f"Final name: {final_name}")
            
            self.log_test("Concurrent Rename Test", True, "Concurrent rename operations tested", results)
            return True
            
        except Exception as e:
            self.log_test("Concurrent Rename Test", False, f"Test error: {str(e)}")
            return False
    
    def test_project_rename_with_epcis_generation(self):
        """Test renaming a project that has completed EPCIS generation"""
        project_id = self.create_test_project("EPCIS Test Project")
        
        if not project_id:
            self.log_test("EPCIS Rename Test", False, "Could not create test project")
            return False
        
        try:
            # Add minimal configuration
            config_data = {
                "itemsPerCase": 5,
                "casesPerSscc": 2,
                "numberOfSscc": 1,
                "useInnerCases": False,
                "companyPrefix": "1234567",
                "itemProductCode": "000000",
                "caseProductCode": "000001",
                "ssccIndicatorDigit": "3",
                "caseIndicatorDigit": "2",
                "itemIndicatorDigit": "1"
            }
            
            config_response = self.session.post(
                f"{self.base_url}/projects/{project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if config_response.status_code == 200:
                # Add serial numbers
                serial_data = {
                    "ssccSerialNumbers": ["SSCC001"],
                    "caseSerialNumbers": ["CASE001", "CASE002"],
                    "innerCaseSerialNumbers": [],
                    "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(10)]
                }
                
                serial_response = self.session.post(
                    f"{self.base_url}/projects/{project_id}/serial-numbers",
                    json=serial_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if serial_response.status_code == 200:
                    # Generate EPCIS
                    epcis_data = {
                        "readPoint": "urn:epc:id:sgln:1234567.00000.0",
                        "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
                    }
                    
                    epcis_response = self.session.post(
                        f"{self.base_url}/projects/{project_id}/generate-epcis",
                        json=epcis_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if epcis_response.status_code == 200:
                        # Now try to rename the completed project
                        update_data = {"name": "Renamed EPCIS Project"}
                        rename_response = self.session.put(
                            f"{self.base_url}/projects/{project_id}",
                            json=update_data,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if rename_response.status_code == 200:
                            self.log_test("EPCIS Rename Test", True, "Successfully renamed project with completed EPCIS generation")
                            return True
                        else:
                            self.log_test("EPCIS Rename Test", False, f"Could not rename completed project: {rename_response.status_code}")
                            return False
            
            self.log_test("EPCIS Rename Test", False, "Could not complete EPCIS generation setup")
            return False
            
        except Exception as e:
            self.log_test("EPCIS Rename Test", False, f"Test error: {str(e)}")
            return False
    
    def run_edge_case_tests(self):
        """Run all edge case tests"""
        print("=" * 80)
        print("PROJECT RENAME EDGE CASE TESTING")
        print("=" * 80)
        
        if not self.setup_test_user():
            print("❌ Could not setup test user. Stopping tests.")
            return False
        
        # Run edge case tests
        self.test_duplicate_project_names()
        self.test_whitespace_only_names()
        self.test_null_and_missing_name_field()
        self.test_concurrent_rename_operations()
        self.test_project_rename_with_epcis_generation()
        
        # Summary
        print("\n" + "=" * 80)
        print("EDGE CASE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        return passed == total

if __name__ == "__main__":
    tester = ProjectRenameEdgeCaseTester()
    success = tester.run_edge_case_tests()
    sys.exit(0 if success else 1)