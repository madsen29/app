#!/usr/bin/env python3
"""
Backend API Testing for Project Management and Dashboard Features
Tests the backend API endpoints with focus on:
1. Project Management: Test project creation, listing, and deletion
2. Batch Delete Simulation: Test multiple sequential project deletions to simulate batch delete operations
3. Pagination Support: Test project listing with different numbers of projects
4. Edge Cases: Test deletion of non-existent projects and empty project lists

Test scenarios:
- Create multiple projects to test pagination
- Test project listing with various project counts
- Simulate batch delete operations with sequential deletions
- Test edge cases like deleting non-existent projects
- Verify empty project lists are handled correctly
"""

import requests
import json
from datetime import datetime
import sys
import os
import time

# Get backend URL from environment
BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

class ProjectManagementTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_email = "testuser@projectmanagement.com"
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
    
    def setup_test_user(self):
        """Create and authenticate test user"""
        # Try to register user (might already exist)
        user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
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
            # Try to register
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.log_test("User Registration", True, "Test user registered successfully")
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_test("User Registration", True, "Test user already exists")
            else:
                self.log_test("User Registration", False, f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Registration error: {str(e)}")
            return False
        
        # Login to get token
        try:
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
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("User Authentication", True, "Successfully authenticated test user")
                return True
            else:
                self.log_test("User Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Login error: {str(e)}")
            return False
    
    def cleanup_existing_projects(self):
        """Clean up any existing projects for the test user"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            if response.status_code == 200:
                projects = response.json()
                for project in projects:
                    delete_response = self.session.delete(f"{self.base_url}/projects/{project['id']}")
                    if delete_response.status_code == 200:
                        print(f"   Cleaned up existing project: {project['name']}")
                self.log_test("Project Cleanup", True, f"Cleaned up {len(projects)} existing projects")
                return True
            else:
                self.log_test("Project Cleanup", False, f"Failed to get projects for cleanup: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Project Cleanup", False, f"Cleanup error: {str(e)}")
            return False
    
    def test_empty_project_list(self):
        """Test that empty project list is handled correctly"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            if response.status_code == 200:
                projects = response.json()
                if isinstance(projects, list) and len(projects) == 0:
                    self.log_test("Empty Project List", True, "Empty project list handled correctly")
                    return True
                else:
                    self.log_test("Empty Project List", False, f"Expected empty list, got: {projects}")
                    return False
            else:
                self.log_test("Empty Project List", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Empty Project List", False, f"Request error: {str(e)}")
            return False
    
    def test_project_creation(self, project_count=10):
        """Test creating multiple projects"""
        created_projects = []
        
        for i in range(project_count):
            project_data = {
                "name": f"Test Project {i+1:02d} - Dashboard Testing"
            }
            
            try:
                response = self.session.post(
                    f"{self.base_url}/projects",
                    json=project_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    project = response.json()
                    created_projects.append(project)
                else:
                    self.log_test(f"Project Creation {i+1}", False, f"HTTP {response.status_code}: {response.text}")
                    return []
                    
            except Exception as e:
                self.log_test(f"Project Creation {i+1}", False, f"Request error: {str(e)}")
                return []
        
        if len(created_projects) == project_count:
            self.log_test("Bulk Project Creation", True, f"Successfully created {project_count} projects", 
                        f"Project IDs: {[p['id'][:8] for p in created_projects]}")
            return created_projects
        else:
            self.log_test("Bulk Project Creation", False, f"Expected {project_count} projects, created {len(created_projects)}")
            return created_projects
    
    def test_project_listing_pagination(self, expected_count):
        """Test project listing with different numbers of projects"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            if response.status_code == 200:
                projects = response.json()
                if isinstance(projects, list):
                    actual_count = len(projects)
                    if actual_count == expected_count:
                        self.log_test("Project Listing Pagination", True, 
                                    f"Correctly retrieved {actual_count} projects")
                        return projects
                    else:
                        self.log_test("Project Listing Pagination", False, 
                                    f"Expected {expected_count} projects, got {actual_count}")
                        return projects
                else:
                    self.log_test("Project Listing Pagination", False, f"Expected list, got: {type(projects)}")
                    return []
            else:
                self.log_test("Project Listing Pagination", False, f"HTTP {response.status_code}: {response.text}")
                return []
        except Exception as e:
            self.log_test("Project Listing Pagination", False, f"Request error: {str(e)}")
            return []
    
    def test_single_project_deletion(self, project_id, project_name):
        """Test deleting a single project"""
        try:
            response = self.session.delete(f"{self.base_url}/projects/{project_id}")
            if response.status_code == 200:
                data = response.json()
                if "deleted successfully" in data.get("message", ""):
                    self.log_test("Single Project Deletion", True, f"Successfully deleted project: {project_name}")
                    return True
                else:
                    self.log_test("Single Project Deletion", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Single Project Deletion", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Single Project Deletion", False, f"Request error: {str(e)}")
            return False
    
    def test_batch_delete_simulation(self, projects):
        """Test batch delete by performing multiple sequential deletions"""
        if not projects:
            self.log_test("Batch Delete Simulation", False, "No projects provided for batch deletion")
            return False
        
        # Delete first 5 projects to simulate batch delete
        batch_size = min(5, len(projects))
        batch_projects = projects[:batch_size]
        
        successful_deletions = 0
        start_time = time.time()
        
        for i, project in enumerate(batch_projects):
            try:
                response = self.session.delete(f"{self.base_url}/projects/{project['id']}")
                if response.status_code == 200:
                    successful_deletions += 1
                    print(f"   Batch delete {i+1}/{batch_size}: {project['name']} - SUCCESS")
                else:
                    print(f"   Batch delete {i+1}/{batch_size}: {project['name']} - FAILED ({response.status_code})")
                    
                # Small delay to simulate realistic batch operations
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   Batch delete {i+1}/{batch_size}: {project['name']} - ERROR ({str(e)})")
        
        end_time = time.time()
        duration = end_time - start_time
        
        if successful_deletions == batch_size:
            self.log_test("Batch Delete Simulation", True, 
                        f"Successfully deleted {successful_deletions}/{batch_size} projects in batch operation",
                        f"Duration: {duration:.2f}s, Average: {duration/batch_size:.3f}s per deletion")
            return True
        else:
            self.log_test("Batch Delete Simulation", False, 
                        f"Only {successful_deletions}/{batch_size} deletions succeeded")
            return False
    
    def test_delete_nonexistent_project(self):
        """Test deleting a non-existent project (edge case)"""
        fake_project_id = "nonexistent-project-id-12345"
        
        try:
            response = self.session.delete(f"{self.base_url}/projects/{fake_project_id}")
            if response.status_code == 404:
                data = response.json()
                if "not found" in data.get("detail", "").lower():
                    self.log_test("Delete Nonexistent Project", True, "Correctly returned 404 for non-existent project")
                    return True
                else:
                    self.log_test("Delete Nonexistent Project", False, f"Unexpected 404 response: {data}")
                    return False
            else:
                self.log_test("Delete Nonexistent Project", False, 
                            f"Expected 404, got {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Delete Nonexistent Project", False, f"Request error: {str(e)}")
            return False
    
    def test_project_listing_after_deletions(self, expected_remaining):
        """Test project listing after batch deletions"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            if response.status_code == 200:
                projects = response.json()
                actual_count = len(projects)
                if actual_count == expected_remaining:
                    self.log_test("Project Listing After Deletions", True, 
                                f"Correctly shows {actual_count} remaining projects after batch deletion")
                    return projects
                else:
                    self.log_test("Project Listing After Deletions", False, 
                                f"Expected {expected_remaining} remaining projects, got {actual_count}")
                    return projects
            else:
                self.log_test("Project Listing After Deletions", False, f"HTTP {response.status_code}: {response.text}")
                return []
        except Exception as e:
            self.log_test("Project Listing After Deletions", False, f"Request error: {str(e)}")
            return []
    
    def test_project_details_retrieval(self, project_id):
        """Test retrieving individual project details"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            if response.status_code == 200:
                project = response.json()
                required_fields = ['id', 'name', 'user_id', 'status', 'current_step', 'created_at']
                missing_fields = [field for field in required_fields if field not in project]
                
                if not missing_fields:
                    self.log_test("Project Details Retrieval", True, 
                                f"Successfully retrieved project details",
                                f"Project: {project['name']}, Status: {project['status']}, Step: {project['current_step']}")
                    return project
                else:
                    self.log_test("Project Details Retrieval", False, 
                                f"Missing required fields: {missing_fields}")
                    return None
            else:
                self.log_test("Project Details Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Project Details Retrieval", False, f"Request error: {str(e)}")
            return None
    
    def run_comprehensive_tests(self):
        """Run all project management tests"""
        print("🚀 Starting Project Management and Dashboard Features Testing")
        print("=" * 80)
        
        # 1. Basic connectivity
        if not self.test_api_health():
            print("❌ API health check failed. Stopping tests.")
            return False
        
        # 2. Setup test user
        if not self.setup_test_user():
            print("❌ User setup failed. Stopping tests.")
            return False
        
        # 3. Clean up existing projects
        if not self.cleanup_existing_projects():
            print("❌ Project cleanup failed. Stopping tests.")
            return False
        
        # 4. Test empty project list
        if not self.test_empty_project_list():
            print("❌ Empty project list test failed.")
        
        # 5. Create multiple projects for testing
        print("\n📝 Creating test projects...")
        created_projects = self.test_project_creation(10)
        if not created_projects:
            print("❌ Project creation failed. Stopping tests.")
            return False
        
        # 6. Test project listing with full list
        print("\n📋 Testing project listing...")
        projects = self.test_project_listing_pagination(10)
        if not projects:
            print("❌ Project listing failed.")
            return False
        
        # 7. Test individual project details
        print("\n🔍 Testing project details retrieval...")
        if projects:
            self.test_project_details_retrieval(projects[0]['id'])
        
        # 8. Test batch delete simulation
        print("\n🗑️ Testing batch delete simulation...")
        if not self.test_batch_delete_simulation(projects):
            print("❌ Batch delete simulation failed.")
        
        # 9. Test project listing after deletions
        print("\n📋 Testing project listing after deletions...")
        remaining_projects = self.test_project_listing_after_deletions(5)  # Should have 5 left after deleting 5
        
        # 10. Test edge case: delete non-existent project
        print("\n⚠️ Testing edge cases...")
        self.test_delete_nonexistent_project()
        
        # 11. Clean up remaining projects
        print("\n🧹 Cleaning up remaining test projects...")
        for project in remaining_projects:
            self.test_single_project_deletion(project['id'], project['name'])
        
        # 12. Verify empty list after cleanup
        print("\n✅ Verifying cleanup...")
        self.test_empty_project_list()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed_tests == 0

def main():
    """Main test execution"""
    tester = ProjectManagementTester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 All project management tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()