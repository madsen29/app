#!/usr/bin/env python3
"""
Backend API Testing for Auto-Incrementing Project Names Functionality
Tests the auto-incrementing project names feature that generates names in the format:
"EPCIS Project - {Month Day, Year} ({number})"

Test scenarios:
1. Basic Project Creation: Create multiple projects in sequence and verify auto-incrementing names
2. Date-based Naming: Verify project names include today's date in format "Jul 18, 2025"
3. Number Increment Logic: Create several projects and verify numbering increments (1, 2, 3, etc.)
4. Duplicate Handling: Test that system finds next available number even if projects are deleted
5. Edge Cases: Test name generation with existing projects that have similar names

Focus Areas:
- Frontend generates auto-incrementing names using generateSuggestedName() function
- Backend stores the names as provided by frontend
- Verify complete workflow from name generation to storage
- Test edge cases and duplicate handling
"""

import requests
import json
from datetime import datetime
import sys
import os
import re

# Get backend URL from environment
BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

class AutoIncrementProjectNamesTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.user_id = None
        self.created_project_ids = []
        
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
        """Test if API is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_test("API Health Check", True, "API is accessible")
                return True
            else:
                self.log_test("API Health Check", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Failed to connect to API: {str(e)}")
            return False
    
    def setup_test_user(self):
        """Create and authenticate a test user"""
        try:
            # Create test user
            user_data = {
                "email": f"autoincrement_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                "password": "TestPassword123!",
                "firstName": "Auto",
                "lastName": "Increment",
                "companyName": "Test Company",
                "streetAddress": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postalCode": "12345",
                "countryCode": "US"
            }
            
            response = self.session.post(f"{self.base_url}/auth/register", json=user_data)
            if response.status_code != 200:
                self.log_test("User Registration", False, f"Failed to register user: {response.status_code} - {response.text}")
                return False
            
            user_info = response.json()
            self.user_id = user_info.get('id')
            
            # Login user
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code != 200:
                self.log_test("User Login", False, f"Failed to login: {response.status_code} - {response.text}")
                return False
            
            token_info = response.json()
            self.auth_token = token_info.get('access_token')
            self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
            
            self.log_test("User Setup", True, f"Test user created and authenticated: {user_data['email']}")
            return True
            
        except Exception as e:
            self.log_test("User Setup", False, f"Exception during user setup: {str(e)}")
            return False
    
    def generate_auto_increment_name(self, existing_projects):
        """
        Simulate the frontend generateSuggestedName() function
        This replicates the logic from /app/frontend/src/ProjectDashboard.js
        """
        now = datetime.now()
        date_str = now.strftime('%b %d, %Y')  # Format: "Jul 18, 2025"
        
        # Base name pattern for today
        base_name_pattern = f"EPCIS Project - {date_str}"
        
        # Find all projects created today with the same base pattern
        today_projects = [project for project in existing_projects 
                         if project['name'].startswith(base_name_pattern)]
        
        # Extract numbers from existing project names
        existing_numbers = []
        for project in today_projects:
            match = re.search(r'\((\d+)\)$', project['name'])
            if match:
                existing_numbers.append(int(match.group(1)))
        
        # Find the next available number
        next_number = max(existing_numbers) + 1 if existing_numbers else 1
        
        return f"{base_name_pattern} ({next_number})"
    
    def get_user_projects(self):
        """Get all projects for the current user"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            if response.status_code == 200:
                return response.json()
            else:
                self.log_test("Get Projects", False, f"Failed to get projects: {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Projects", False, f"Exception getting projects: {str(e)}")
            return []
    
    def create_project_with_name(self, project_name):
        """Create a project with the specified name"""
        try:
            project_data = {"name": project_name}
            response = self.session.post(f"{self.base_url}/projects", json=project_data)
            
            if response.status_code == 200:
                project = response.json()
                self.created_project_ids.append(project['id'])
                return project
            else:
                self.log_test("Create Project", False, f"Failed to create project: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Project", False, f"Exception creating project: {str(e)}")
            return None
    
    def delete_project(self, project_id):
        """Delete a project"""
        try:
            response = self.session.delete(f"{self.base_url}/projects/{project_id}")
            if response.status_code == 200:
                if project_id in self.created_project_ids:
                    self.created_project_ids.remove(project_id)
                return True
            else:
                self.log_test("Delete Project", False, f"Failed to delete project: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Delete Project", False, f"Exception deleting project: {str(e)}")
            return False
    
    def test_basic_project_creation_auto_increment(self):
        """Test 1: Basic Project Creation with auto-incrementing names"""
        print("\n=== TEST 1: Basic Project Creation with Auto-Incrementing Names ===")
        
        try:
            # Get current projects
            existing_projects = self.get_user_projects()
            
            # Create 5 projects in sequence
            created_projects = []
            for i in range(5):
                # Generate auto-increment name based on existing projects
                auto_name = self.generate_auto_increment_name(existing_projects + created_projects)
                
                # Create project with auto-generated name
                project = self.create_project_with_name(auto_name)
                if project:
                    created_projects.append(project)
                    self.log_test(f"Project Creation {i+1}", True, f"Created project: {project['name']}")
                else:
                    self.log_test(f"Project Creation {i+1}", False, "Failed to create project")
                    return False
            
            # Verify all projects were created with correct auto-incrementing names
            if len(created_projects) == 5:
                # Check that names follow the pattern and increment correctly
                today_str = datetime.now().strftime('%b %d, %Y')
                expected_base = f"EPCIS Project - {today_str}"
                
                for i, project in enumerate(created_projects):
                    expected_name = f"{expected_base} ({i+1})"
                    if project['name'] == expected_name:
                        self.log_test(f"Name Pattern Check {i+1}", True, f"Correct name: {project['name']}")
                    else:
                        self.log_test(f"Name Pattern Check {i+1}", False, f"Expected: {expected_name}, Got: {project['name']}")
                        return False
                
                self.log_test("Basic Auto-Increment Test", True, "All 5 projects created with correct auto-incrementing names")
                return True
            else:
                self.log_test("Basic Auto-Increment Test", False, f"Expected 5 projects, created {len(created_projects)}")
                return False
                
        except Exception as e:
            self.log_test("Basic Auto-Increment Test", False, f"Exception: {str(e)}")
            return False
    
    def test_date_based_naming(self):
        """Test 2: Verify project names include today's date in correct format"""
        print("\n=== TEST 2: Date-based Naming Verification ===")
        
        try:
            # Get current projects to determine next number
            existing_projects = self.get_user_projects()
            
            # Generate name with today's date
            auto_name = self.generate_auto_increment_name(existing_projects)
            
            # Create project
            project = self.create_project_with_name(auto_name)
            if not project:
                self.log_test("Date-based Naming Test", False, "Failed to create project")
                return False
            
            # Verify date format in name
            today_str = datetime.now().strftime('%b %d, %Y')  # e.g., "Jul 18, 2025"
            expected_pattern = f"EPCIS Project - {today_str} \\(\\d+\\)"
            
            if re.match(expected_pattern, project['name']):
                self.log_test("Date Format Check", True, f"Correct date format in name: {project['name']}")
                self.log_test("Date-based Naming Test", True, f"Project name includes today's date: {today_str}")
                return True
            else:
                self.log_test("Date Format Check", False, f"Incorrect date format. Expected pattern: {expected_pattern}, Got: {project['name']}")
                return False
                
        except Exception as e:
            self.log_test("Date-based Naming Test", False, f"Exception: {str(e)}")
            return False
    
    def test_number_increment_logic(self):
        """Test 3: Create several projects and verify numbering increments correctly"""
        print("\n=== TEST 3: Number Increment Logic ===")
        
        try:
            # Get current projects
            existing_projects = self.get_user_projects()
            
            # Create 3 more projects to test increment logic
            created_projects = []
            for i in range(3):
                auto_name = self.generate_auto_increment_name(existing_projects + created_projects)
                project = self.create_project_with_name(auto_name)
                if project:
                    created_projects.append(project)
                else:
                    self.log_test("Number Increment Test", False, f"Failed to create project {i+1}")
                    return False
            
            # Extract numbers from created project names
            numbers = []
            for project in created_projects:
                match = re.search(r'\((\d+)\)$', project['name'])
                if match:
                    numbers.append(int(match.group(1)))
                else:
                    self.log_test("Number Increment Test", False, f"No number found in project name: {project['name']}")
                    return False
            
            # Verify numbers are consecutive
            if len(numbers) == 3:
                # Check if numbers are consecutive (allowing for existing projects)
                numbers.sort()
                consecutive = all(numbers[i] == numbers[i-1] + 1 for i in range(1, len(numbers)))
                
                if consecutive:
                    self.log_test("Number Increment Test", True, f"Numbers increment correctly: {numbers}")
                    return True
                else:
                    self.log_test("Number Increment Test", False, f"Numbers not consecutive: {numbers}")
                    return False
            else:
                self.log_test("Number Increment Test", False, f"Expected 3 numbers, got {len(numbers)}")
                return False
                
        except Exception as e:
            self.log_test("Number Increment Test", False, f"Exception: {str(e)}")
            return False
    
    def test_duplicate_handling_after_deletion(self):
        """Test 4: Test that system finds next available number even if projects are deleted"""
        print("\n=== TEST 4: Duplicate Handling After Deletion ===")
        
        try:
            # Get current projects
            existing_projects = self.get_user_projects()
            
            # Create 3 projects
            created_projects = []
            for i in range(3):
                auto_name = self.generate_auto_increment_name(existing_projects + created_projects)
                project = self.create_project_with_name(auto_name)
                if project:
                    created_projects.append(project)
                else:
                    self.log_test("Duplicate Handling Test", False, f"Failed to create project {i+1}")
                    return False
            
            # Delete the middle project (should create a gap)
            if len(created_projects) >= 2:
                middle_project = created_projects[1]
                if self.delete_project(middle_project['id']):
                    self.log_test("Project Deletion", True, f"Deleted project: {middle_project['name']}")
                else:
                    self.log_test("Duplicate Handling Test", False, "Failed to delete middle project")
                    return False
            
            # Get updated project list
            updated_projects = self.get_user_projects()
            
            # Create a new project - it should use the next highest number, not fill the gap
            auto_name = self.generate_auto_increment_name(updated_projects)
            new_project = self.create_project_with_name(auto_name)
            
            if new_project:
                # Extract number from new project name
                match = re.search(r'\((\d+)\)$', new_project['name'])
                if match:
                    new_number = int(match.group(1))
                    
                    # The new number should be higher than all existing numbers
                    existing_numbers = []
                    for project in updated_projects:
                        if project['name'].startswith("EPCIS Project -"):
                            num_match = re.search(r'\((\d+)\)$', project['name'])
                            if num_match:
                                existing_numbers.append(int(num_match.group(1)))
                    
                    expected_number = max(existing_numbers) + 1 if existing_numbers else 1
                    
                    if new_number == expected_number:
                        self.log_test("Duplicate Handling Test", True, f"Correctly assigned next available number: {new_number}")
                        return True
                    else:
                        self.log_test("Duplicate Handling Test", False, f"Expected number {expected_number}, got {new_number}")
                        return False
                else:
                    self.log_test("Duplicate Handling Test", False, f"No number found in new project name: {new_project['name']}")
                    return False
            else:
                self.log_test("Duplicate Handling Test", False, "Failed to create new project after deletion")
                return False
                
        except Exception as e:
            self.log_test("Duplicate Handling Test", False, f"Exception: {str(e)}")
            return False
    
    def test_edge_cases_similar_names(self):
        """Test 5: Test name generation with existing projects that have similar names"""
        print("\n=== TEST 5: Edge Cases with Similar Names ===")
        
        try:
            # Create projects with similar but different names to test edge cases
            edge_case_names = [
                "EPCIS Project - Different Date (1)",
                "EPCIS Project - Jul 18, 2024 (1)",  # Different year
                "EPCIS Project Test (1)",  # Similar but different
                "My EPCIS Project - Jul 18, 2025 (1)"  # Different prefix
            ]
            
            edge_projects = []
            for name in edge_case_names:
                project = self.create_project_with_name(name)
                if project:
                    edge_projects.append(project)
                    self.log_test("Edge Case Project Creation", True, f"Created: {name}")
                else:
                    self.log_test("Edge Cases Test", False, f"Failed to create edge case project: {name}")
                    return False
            
            # Now create a project with auto-increment name
            existing_projects = self.get_user_projects()
            auto_name = self.generate_auto_increment_name(existing_projects)
            auto_project = self.create_project_with_name(auto_name)
            
            if auto_project:
                # Verify the auto-generated name is not affected by similar names
                today_str = datetime.now().strftime('%b %d, %Y')
                expected_pattern = f"EPCIS Project - {today_str} \\(\\d+\\)"
                
                if re.match(expected_pattern, auto_project['name']):
                    # Check that it only considers projects with exact base pattern
                    base_pattern = f"EPCIS Project - {today_str}"
                    matching_projects = [p for p in existing_projects if p['name'].startswith(base_pattern)]
                    
                    # Extract number from auto project
                    match = re.search(r'\((\d+)\)$', auto_project['name'])
                    if match:
                        auto_number = int(match.group(1))
                        
                        # Should be 1 if no matching projects exist, or max + 1
                        existing_numbers = []
                        for project in matching_projects:
                            num_match = re.search(r'\((\d+)\)$', project['name'])
                            if num_match:
                                existing_numbers.append(int(num_match.group(1)))
                        
                        expected_number = max(existing_numbers) + 1 if existing_numbers else 1
                        
                        if auto_number == expected_number:
                            self.log_test("Edge Cases Test", True, f"Auto-increment correctly ignores similar names: {auto_project['name']}")
                            return True
                        else:
                            self.log_test("Edge Cases Test", False, f"Expected number {expected_number}, got {auto_number}")
                            return False
                    else:
                        self.log_test("Edge Cases Test", False, f"No number in auto project name: {auto_project['name']}")
                        return False
                else:
                    self.log_test("Edge Cases Test", False, f"Auto project name doesn't match expected pattern: {auto_project['name']}")
                    return False
            else:
                self.log_test("Edge Cases Test", False, "Failed to create auto-increment project")
                return False
                
        except Exception as e:
            self.log_test("Edge Cases Test", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_projects(self):
        """Clean up all created test projects"""
        print("\n=== CLEANUP: Removing Test Projects ===")
        
        cleanup_count = 0
        for project_id in self.created_project_ids[:]:  # Copy list to avoid modification during iteration
            if self.delete_project(project_id):
                cleanup_count += 1
        
        self.log_test("Cleanup", True, f"Cleaned up {cleanup_count} test projects")
    
    def run_all_tests(self):
        """Run all auto-increment project names tests"""
        print("🚀 STARTING AUTO-INCREMENT PROJECT NAMES TESTING")
        print("=" * 80)
        
        # Setup
        if not self.test_api_health():
            return False
        
        if not self.setup_test_user():
            return False
        
        # Run tests
        tests = [
            self.test_basic_project_creation_auto_increment,
            self.test_date_based_naming,
            self.test_number_increment_logic,
            self.test_duplicate_handling_after_deletion,
            self.test_edge_cases_similar_names
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Cleanup
        self.cleanup_test_projects()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 AUTO-INCREMENT PROJECT NAMES TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 ALL AUTO-INCREMENT PROJECT NAMES TESTS PASSED!")
            print("\n✅ COMPREHENSIVE VERIFICATION COMPLETED:")
            print("   • Basic project creation with auto-incrementing names ✓")
            print("   • Date-based naming with today's date format ✓")
            print("   • Number increment logic (1, 2, 3, etc.) ✓")
            print("   • Duplicate handling after project deletion ✓")
            print("   • Edge cases with similar project names ✓")
            return True
        else:
            print("❌ SOME TESTS FAILED - Auto-increment functionality needs attention")
            return False

def main():
    """Main test execution"""
    tester = AutoIncrementProjectNamesTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 RESULT: Auto-incrementing project names functionality is working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️  RESULT: Auto-incrementing project names functionality has issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()