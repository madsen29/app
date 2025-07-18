#!/usr/bin/env python3
"""
Advanced Project Management Testing - Focus on Review Request Requirements
Tests specific dashboard features mentioned in the review request:
1. Project Management with various project counts
2. Batch Delete Simulation with different batch sizes
3. Pagination Support with stress testing
4. Edge Cases and error handling
"""

import requests
import json
from datetime import datetime
import sys
import os
import time
import concurrent.futures
import threading

# Get backend URL from environment
BACKEND_URL = "https://cd63a717-b5ed-4c4d-b9fe-b518396e7591.preview.emergentagent.com/api"

class AdvancedProjectTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_email = "advancedtest@projectmanagement.com"
        self.test_user_password = "AdvancedTest123!"
        
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
        """Create and authenticate test user"""
        user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "firstName": "Advanced",
            "lastName": "Tester",
            "companyName": "Advanced Test Company",
            "streetAddress": "456 Advanced St",
            "city": "Advanced City",
            "state": "AC",
            "postalCode": "54321",
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
                self.log_test("Advanced User Registration", True, "Test user registered successfully")
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_test("Advanced User Registration", True, "Test user already exists")
            else:
                self.log_test("Advanced User Registration", False, f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Advanced User Registration", False, f"Registration error: {str(e)}")
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
                self.log_test("Advanced User Authentication", True, "Successfully authenticated test user")
                return True
            else:
                self.log_test("Advanced User Authentication", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Advanced User Authentication", False, f"Login error: {str(e)}")
            return False
    
    def cleanup_all_projects(self):
        """Clean up all existing projects"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            if response.status_code == 200:
                projects = response.json()
                for project in projects:
                    self.session.delete(f"{self.base_url}/projects/{project['id']}")
                self.log_test("Advanced Project Cleanup", True, f"Cleaned up {len(projects)} existing projects")
                return True
            else:
                self.log_test("Advanced Project Cleanup", False, f"Failed to get projects: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Advanced Project Cleanup", False, f"Cleanup error: {str(e)}")
            return False
    
    def test_large_scale_project_creation(self, count=25):
        """Test creating a large number of projects"""
        print(f"\n📝 Creating {count} projects for large-scale testing...")
        created_projects = []
        start_time = time.time()
        
        for i in range(count):
            project_data = {
                "name": f"Large Scale Project {i+1:03d} - Dashboard Stress Test"
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
                    if (i + 1) % 5 == 0:
                        print(f"   Created {i+1}/{count} projects...")
                else:
                    self.log_test(f"Large Scale Creation {i+1}", False, f"HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                self.log_test(f"Large Scale Creation {i+1}", False, f"Request error: {str(e)}")
                break
        
        end_time = time.time()
        duration = end_time - start_time
        
        if len(created_projects) == count:
            self.log_test("Large Scale Project Creation", True, 
                        f"Successfully created {count} projects",
                        f"Duration: {duration:.2f}s, Average: {duration/count:.3f}s per project")
            return created_projects
        else:
            self.log_test("Large Scale Project Creation", False, 
                        f"Only created {len(created_projects)}/{count} projects")
            return created_projects
    
    def test_pagination_with_large_dataset(self, expected_count):
        """Test project listing with large dataset"""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/projects")
            end_time = time.time()
            
            if response.status_code == 200:
                projects = response.json()
                actual_count = len(projects)
                duration = end_time - start_time
                
                if actual_count == expected_count:
                    self.log_test("Large Dataset Pagination", True, 
                                f"Successfully retrieved {actual_count} projects",
                                f"Response time: {duration:.3f}s for {actual_count} projects")
                    return projects
                else:
                    self.log_test("Large Dataset Pagination", False, 
                                f"Expected {expected_count}, got {actual_count}")
                    return projects
            else:
                self.log_test("Large Dataset Pagination", False, f"HTTP {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Large Dataset Pagination", False, f"Request error: {str(e)}")
            return []
    
    def test_concurrent_batch_deletions(self, projects, batch_size=10):
        """Test concurrent batch deletions to simulate real dashboard usage"""
        if len(projects) < batch_size:
            self.log_test("Concurrent Batch Deletions", False, "Not enough projects for batch test")
            return False
        
        batch_projects = projects[:batch_size]
        successful_deletions = 0
        failed_deletions = 0
        lock = threading.Lock()
        
        def delete_project(project):
            nonlocal successful_deletions, failed_deletions
            try:
                # Create a new session for each thread to avoid conflicts
                thread_session = requests.Session()
                thread_session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                response = thread_session.delete(f"{self.base_url}/projects/{project['id']}")
                
                with lock:
                    if response.status_code == 200:
                        successful_deletions += 1
                        print(f"   Concurrent delete: {project['name']} - SUCCESS")
                    else:
                        failed_deletions += 1
                        print(f"   Concurrent delete: {project['name']} - FAILED ({response.status_code})")
                        
            except Exception as e:
                with lock:
                    failed_deletions += 1
                    print(f"   Concurrent delete: {project['name']} - ERROR ({str(e)})")
        
        print(f"\n🔄 Testing concurrent deletion of {batch_size} projects...")
        start_time = time.time()
        
        # Use ThreadPoolExecutor for concurrent deletions
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(delete_project, project) for project in batch_projects]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if successful_deletions == batch_size:
            self.log_test("Concurrent Batch Deletions", True, 
                        f"Successfully deleted {successful_deletions}/{batch_size} projects concurrently",
                        f"Duration: {duration:.2f}s, Average: {duration/batch_size:.3f}s per deletion")
            return True
        else:
            self.log_test("Concurrent Batch Deletions", False, 
                        f"Only {successful_deletions}/{batch_size} deletions succeeded, {failed_deletions} failed")
            return False
    
    def test_sequential_batch_deletions(self, projects, batch_size=10):
        """Test sequential batch deletions with timing analysis"""
        if len(projects) < batch_size:
            self.log_test("Sequential Batch Deletions", False, "Not enough projects for batch test")
            return False
        
        batch_projects = projects[:batch_size]
        successful_deletions = 0
        deletion_times = []
        
        print(f"\n⏭️ Testing sequential deletion of {batch_size} projects...")
        
        for i, project in enumerate(batch_projects):
            try:
                start_time = time.time()
                response = self.session.delete(f"{self.base_url}/projects/{project['id']}")
                end_time = time.time()
                
                deletion_time = end_time - start_time
                deletion_times.append(deletion_time)
                
                if response.status_code == 200:
                    successful_deletions += 1
                    print(f"   Sequential delete {i+1}/{batch_size}: {project['name']} - SUCCESS ({deletion_time:.3f}s)")
                else:
                    print(f"   Sequential delete {i+1}/{batch_size}: {project['name']} - FAILED ({response.status_code})")
                    
            except Exception as e:
                print(f"   Sequential delete {i+1}/{batch_size}: {project['name']} - ERROR ({str(e)})")
        
        if successful_deletions == batch_size:
            avg_time = sum(deletion_times) / len(deletion_times)
            total_time = sum(deletion_times)
            self.log_test("Sequential Batch Deletions", True, 
                        f"Successfully deleted {successful_deletions}/{batch_size} projects sequentially",
                        f"Total: {total_time:.2f}s, Average: {avg_time:.3f}s per deletion")
            return True
        else:
            self.log_test("Sequential Batch Deletions", False, 
                        f"Only {successful_deletions}/{batch_size} deletions succeeded")
            return False
    
    def test_edge_cases_comprehensive(self):
        """Test comprehensive edge cases"""
        print("\n⚠️ Testing comprehensive edge cases...")
        
        # Test 1: Delete with malformed project ID
        try:
            response = self.session.delete(f"{self.base_url}/projects/malformed-id-123")
            if response.status_code == 404:
                self.log_test("Edge Case: Malformed ID", True, "Correctly handled malformed project ID")
            else:
                self.log_test("Edge Case: Malformed ID", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_test("Edge Case: Malformed ID", False, f"Error: {str(e)}")
        
        # Test 2: Delete with empty project ID
        try:
            response = self.session.delete(f"{self.base_url}/projects/")
            # This should return 404 or 405 (Method Not Allowed)
            if response.status_code in [404, 405]:
                self.log_test("Edge Case: Empty ID", True, f"Correctly handled empty project ID ({response.status_code})")
            else:
                self.log_test("Edge Case: Empty ID", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_test("Edge Case: Empty ID", False, f"Error: {str(e)}")
        
        # Test 3: Multiple rapid requests to same project
        # First create a project
        project_data = {"name": "Edge Case Test Project"}
        try:
            response = self.session.post(f"{self.base_url}/projects", json=project_data)
            if response.status_code == 200:
                project = response.json()
                project_id = project['id']
                
                # Try to delete it multiple times rapidly
                delete_responses = []
                for i in range(3):
                    delete_response = self.session.delete(f"{self.base_url}/projects/{project_id}")
                    delete_responses.append(delete_response.status_code)
                    time.sleep(0.01)  # Very small delay
                
                # First should succeed (200), others should fail (404)
                if delete_responses[0] == 200 and all(code == 404 for code in delete_responses[1:]):
                    self.log_test("Edge Case: Rapid Deletes", True, "Correctly handled rapid deletion attempts")
                else:
                    self.log_test("Edge Case: Rapid Deletes", False, f"Unexpected responses: {delete_responses}")
            else:
                self.log_test("Edge Case: Rapid Deletes", False, "Failed to create test project")
        except Exception as e:
            self.log_test("Edge Case: Rapid Deletes", False, f"Error: {str(e)}")
    
    def test_performance_metrics(self, projects):
        """Test performance metrics for dashboard operations"""
        if not projects:
            self.log_test("Performance Metrics", False, "No projects available for performance testing")
            return
        
        print("\n📊 Testing performance metrics...")
        
        # Test project listing performance
        list_times = []
        for i in range(5):
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/projects")
            end_time = time.time()
            
            if response.status_code == 200:
                list_times.append(end_time - start_time)
            time.sleep(0.1)
        
        if list_times:
            avg_list_time = sum(list_times) / len(list_times)
            max_list_time = max(list_times)
            min_list_time = min(list_times)
            
            # Consider good performance if average is under 1 second
            if avg_list_time < 1.0:
                self.log_test("Performance: Project Listing", True, 
                            f"Good listing performance",
                            f"Avg: {avg_list_time:.3f}s, Min: {min_list_time:.3f}s, Max: {max_list_time:.3f}s")
            else:
                self.log_test("Performance: Project Listing", False, 
                            f"Slow listing performance: {avg_list_time:.3f}s average")
        
        # Test individual project retrieval performance
        if projects:
            detail_times = []
            for i in range(min(5, len(projects))):
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/projects/{projects[i]['id']}")
                end_time = time.time()
                
                if response.status_code == 200:
                    detail_times.append(end_time - start_time)
                time.sleep(0.1)
            
            if detail_times:
                avg_detail_time = sum(detail_times) / len(detail_times)
                
                if avg_detail_time < 0.5:
                    self.log_test("Performance: Project Details", True, 
                                f"Good detail retrieval performance: {avg_detail_time:.3f}s average")
                else:
                    self.log_test("Performance: Project Details", False, 
                                f"Slow detail retrieval: {avg_detail_time:.3f}s average")
    
    def run_advanced_tests(self):
        """Run all advanced project management tests"""
        print("🚀 Starting Advanced Project Management Testing")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_user():
            print("❌ User setup failed. Stopping tests.")
            return False
        
        if not self.cleanup_all_projects():
            print("❌ Project cleanup failed. Stopping tests.")
            return False
        
        # Large scale testing
        created_projects = self.test_large_scale_project_creation(25)
        if not created_projects:
            print("❌ Large scale project creation failed.")
            return False
        
        # Pagination testing
        projects = self.test_pagination_with_large_dataset(25)
        
        # Performance testing
        self.test_performance_metrics(projects)
        
        # Batch deletion testing - concurrent
        remaining_after_concurrent = len(projects) - 10
        if self.test_concurrent_batch_deletions(projects, 10):
            # Verify remaining count
            updated_projects = self.test_pagination_with_large_dataset(remaining_after_concurrent)
            
            # Sequential batch deletion
            if len(updated_projects) >= 10:
                self.test_sequential_batch_deletions(updated_projects, 10)
        
        # Edge cases
        self.test_edge_cases_comprehensive()
        
        # Final cleanup
        print("\n🧹 Final cleanup...")
        self.cleanup_all_projects()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 ADVANCED TEST SUMMARY")
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
    tester = AdvancedProjectTester()
    success = tester.run_advanced_tests()
    
    if success:
        print("\n🎉 All advanced project management tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some advanced tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()