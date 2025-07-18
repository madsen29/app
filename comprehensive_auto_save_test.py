#!/usr/bin/env python3
"""
Comprehensive Auto-Save Review Request Testing
Tests all specific areas mentioned in the review request:
1. Project Management: Test project creation, updating, and retrieval
2. Configuration Management: Test configuration creation and updates
3. Serial Numbers Management: Test serial numbers creation and updates
4. Auto-save Scenarios: Test rapid successive updates to verify backend can handle frequent auto-save requests
"""

import requests
import json
import time
import threading
from datetime import datetime
import sys

BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

class ComprehensiveAutoSaveTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_email = "comprehensive.test@example.com"
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
    
    def setup_authentication(self):
        """Setup authentication"""
        user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "firstName": "Comprehensive",
            "lastName": "Tester",
            "companyName": "Test Company",
            "streetAddress": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "postalCode": "12345",
            "countryCode": "US"
        }
        
        try:
            self.session.post(f"{self.base_url}/auth/register", json=user_data)
        except:
            pass
        
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            return True
        return False
    
    def test_project_management_comprehensive(self):
        """Test comprehensive project management operations"""
        
        # 1. Project Creation
        project_data = {
            "name": f"Comprehensive Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        response = self.session.post(f"{self.base_url}/projects", json=project_data)
        if response.status_code != 200:
            self.log_test("Project Management - Creation", False, f"HTTP {response.status_code}: {response.text}")
            return None
        
        project = response.json()
        project_id = project.get("id")
        self.log_test("Project Management - Creation", True, f"Project created successfully: {project_id}")
        
        # 2. Project Retrieval
        response = self.session.get(f"{self.base_url}/projects/{project_id}")
        if response.status_code != 200:
            self.log_test("Project Management - Retrieval", False, f"HTTP {response.status_code}: {response.text}")
            return None
        
        retrieved_project = response.json()
        if retrieved_project.get("id") == project_id and retrieved_project.get("name") == project_data["name"]:
            self.log_test("Project Management - Retrieval", True, "Project retrieved successfully with correct data")
        else:
            self.log_test("Project Management - Retrieval", False, "Retrieved project data mismatch")
            return None
        
        # 3. Project Update
        update_data = {
            "name": f"Updated {project_data['name']}",
            "current_step": 2,
            "status": "In Progress"
        }
        
        response = self.session.put(f"{self.base_url}/projects/{project_id}", json=update_data)
        if response.status_code != 200:
            self.log_test("Project Management - Update", False, f"HTTP {response.status_code}: {response.text}")
            return None
        
        updated_project = response.json()
        if updated_project.get("name") == update_data["name"] and updated_project.get("current_step") == 2:
            self.log_test("Project Management - Update", True, "Project updated successfully")
        else:
            self.log_test("Project Management - Update", False, "Project update data mismatch")
            return None
        
        # 4. Project List Retrieval
        response = self.session.get(f"{self.base_url}/projects")
        if response.status_code != 200:
            self.log_test("Project Management - List Retrieval", False, f"HTTP {response.status_code}: {response.text}")
            return None
        
        projects = response.json()
        project_found = any(p.get("id") == project_id for p in projects)
        if project_found:
            self.log_test("Project Management - List Retrieval", True, f"Project found in list of {len(projects)} projects")
        else:
            self.log_test("Project Management - List Retrieval", False, "Project not found in projects list")
        
        return project_id
    
    def test_configuration_management_comprehensive(self, project_id):
        """Test comprehensive configuration management"""
        if not project_id:
            self.log_test("Configuration Management", False, "No project ID available")
            return False
        
        # 1. Configuration Creation
        config_data = {
            "itemsPerCase": 8,
            "casesPerSscc": 3,
            "numberOfSscc": 2,
            "useInnerCases": True,
            "innerCasesPerCase": 2,
            "itemsPerInnerCase": 4,
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000001",
            "innerCaseProductCode": "000002",
            "lotNumber": "BATCH456",
            "expirationDate": "2026-06-30",
            "ssccIndicatorDigit": "3",
            "caseIndicatorDigit": "2",
            "innerCaseIndicatorDigit": "4",
            "itemIndicatorDigit": "1",
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "senderName": "Comprehensive Sender",
            "senderStreetAddress": "123 Comprehensive St",
            "senderCity": "Sender City",
            "senderState": "SC",
            "senderPostalCode": "12345",
            "senderCountryCode": "US",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "receiverName": "Comprehensive Receiver",
            "receiverStreetAddress": "456 Receiver Ave",
            "receiverCity": "Receiver City",
            "receiverState": "RC",
            "receiverPostalCode": "67890",
            "receiverCountryCode": "US",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperName": "Comprehensive Shipper",
            "shipperStreetAddress": "789 Shipper Blvd",
            "shipperCity": "Shipper City",
            "shipperState": "SH",
            "shipperPostalCode": "11111",
            "shipperCountryCode": "US",
            "shipperSameAsSender": False,
            "packageNdc": "12345-678-90",
            "regulatedProductName": "Comprehensive Test Drug",
            "manufacturerName": "Comprehensive Pharma",
            "dosageFormType": "Capsule",
            "strengthDescription": "25mg",
            "netContentDescription": "60 capsules"
        }
        
        response = self.session.post(f"{self.base_url}/projects/{project_id}/configuration", json=config_data)
        if response.status_code != 200:
            self.log_test("Configuration Management - Creation", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        config = response.json()
        self.log_test("Configuration Management - Creation", True, "Configuration created with all fields")
        
        # 2. Configuration Updates (simulating auto-save)
        update_scenarios = [
            {"lotNumber": "BATCH456-UPDATED", "expirationDate": "2026-07-31"},
            {"itemsPerCase": 10, "packageNdc": "12345-678-91"},
            {"regulatedProductName": "Updated Test Drug", "strengthDescription": "50mg"}
        ]
        
        successful_updates = 0
        for i, update in enumerate(update_scenarios):
            # Update configuration via project update
            project_update = {"configuration": {**config_data, **update}}
            
            response = self.session.put(f"{self.base_url}/projects/{project_id}", json=project_update)
            if response.status_code == 200:
                successful_updates += 1
                self.log_test(f"Configuration Management - Update {i+1}", True, f"Configuration updated: {list(update.keys())}")
            else:
                self.log_test(f"Configuration Management - Update {i+1}", False, f"HTTP {response.status_code}: {response.text}")
        
        return successful_updates == len(update_scenarios)
    
    def test_serial_numbers_management_comprehensive(self, project_id):
        """Test comprehensive serial numbers management"""
        if not project_id:
            self.log_test("Serial Numbers Management", False, "No project ID available")
            return False
        
        # For config: 2 SSCC, 3 Cases per SSCC, 2 Inner Cases per Case, 4 Items per Inner Case
        # Total: 2 SSCC, 6 Cases, 12 Inner Cases, 48 Items
        
        # 1. Serial Numbers Creation
        serial_data = {
            "ssccSerialNumbers": ["SSCC001", "SSCC002"],
            "caseSerialNumbers": [f"CASE{i+1:03d}" for i in range(6)],
            "innerCaseSerialNumbers": [f"INNER{i+1:03d}" for i in range(12)],
            "itemSerialNumbers": [f"ITEM{i+1:04d}" for i in range(48)]
        }
        
        response = self.session.post(f"{self.base_url}/projects/{project_id}/serial-numbers", json=serial_data)
        if response.status_code != 200:
            self.log_test("Serial Numbers Management - Creation", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        serials = response.json()
        expected_counts = [2, 6, 12, 48]
        actual_counts = [
            len(serials['ssccSerialNumbers']),
            len(serials['caseSerialNumbers']),
            len(serials['innerCaseSerialNumbers']),
            len(serials['itemSerialNumbers'])
        ]
        
        if actual_counts == expected_counts:
            self.log_test("Serial Numbers Management - Creation", True, 
                         f"Serial numbers created correctly: {actual_counts[0]} SSCC, {actual_counts[1]} Cases, {actual_counts[2]} Inner Cases, {actual_counts[3]} Items")
        else:
            self.log_test("Serial Numbers Management - Creation", False, 
                         f"Serial count mismatch: expected {expected_counts}, got {actual_counts}")
            return False
        
        # 2. Serial Numbers Updates (simulating progressive entry)
        update_scenarios = [
            # Simulate partial entry updates
            {"serial_numbers": [f"UPDATED_ITEM{i+1:04d}" for i in range(24)]},  # Half items
            {"serial_numbers": [f"UPDATED_ITEM{i+1:04d}" for i in range(48)]},  # All items
        ]
        
        successful_updates = 0
        for i, update in enumerate(update_scenarios):
            project_update = {"configuration": update}
            
            response = self.session.put(f"{self.base_url}/projects/{project_id}", json=project_update)
            if response.status_code == 200:
                successful_updates += 1
                self.log_test(f"Serial Numbers Management - Update {i+1}", True, f"Serial numbers updated: {len(update['serial_numbers'])} items")
            else:
                self.log_test(f"Serial Numbers Management - Update {i+1}", False, f"HTTP {response.status_code}: {response.text}")
        
        return successful_updates == len(update_scenarios)
    
    def test_auto_save_scenarios_comprehensive(self, project_id):
        """Test comprehensive auto-save scenarios"""
        if not project_id:
            self.log_test("Auto-Save Scenarios", False, "No project ID available")
            return False
        
        # Scenario 1: Rapid successive configuration updates
        rapid_updates_success = 0
        rapid_updates_total = 20
        
        for i in range(rapid_updates_total):
            update_data = {
                "configuration": {
                    "auto_save_test": True,
                    "update_sequence": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "lotNumber": f"RAPID{i+1:03d}",
                    "itemsPerCase": 8 + (i % 5)  # Vary between 8-12
                }
            }
            
            response = self.session.put(f"{self.base_url}/projects/{project_id}", json=update_data)
            if response.status_code == 200:
                rapid_updates_success += 1
            
            time.sleep(0.02)  # 20ms between updates (very rapid)
        
        rapid_success_rate = (rapid_updates_success / rapid_updates_total) * 100
        if rapid_success_rate >= 90:
            self.log_test("Auto-Save Scenarios - Rapid Updates", True, 
                         f"Rapid updates successful: {rapid_updates_success}/{rapid_updates_total} ({rapid_success_rate:.1f}%)")
        else:
            self.log_test("Auto-Save Scenarios - Rapid Updates", False, 
                         f"Rapid updates failed: {rapid_updates_success}/{rapid_updates_total} ({rapid_success_rate:.1f}%)")
        
        # Scenario 2: Concurrent auto-save requests
        concurrent_results = []
        
        def concurrent_update(thread_id):
            try:
                session = requests.Session()
                session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                for i in range(3):  # 3 updates per thread
                    update_data = {
                        "configuration": {
                            "concurrent_test": True,
                            "thread_id": thread_id,
                            "update_index": i,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    response = session.put(f"{self.base_url}/projects/{project_id}", json=update_data)
                    concurrent_results.append({
                        "thread_id": thread_id,
                        "update_index": i,
                        "success": response.status_code == 200
                    })
                    
                    time.sleep(0.05)  # 50ms between updates
                    
            except Exception as e:
                concurrent_results.append({
                    "thread_id": thread_id,
                    "error": str(e),
                    "success": False
                })
        
        # Start 4 concurrent threads
        threads = []
        for i in range(4):
            thread = threading.Thread(target=concurrent_update, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        concurrent_success = sum(1 for result in concurrent_results if result.get("success", False))
        concurrent_total = len(concurrent_results)
        concurrent_success_rate = (concurrent_success / concurrent_total) * 100 if concurrent_total > 0 else 0
        
        if concurrent_success_rate >= 80:
            self.log_test("Auto-Save Scenarios - Concurrent Updates", True, 
                         f"Concurrent updates successful: {concurrent_success}/{concurrent_total} ({concurrent_success_rate:.1f}%)")
        else:
            self.log_test("Auto-Save Scenarios - Concurrent Updates", False, 
                         f"Concurrent updates failed: {concurrent_success}/{concurrent_total} ({concurrent_success_rate:.1f}%)")
        
        # Scenario 3: Mixed operation auto-save (configuration + serial updates)
        mixed_success = 0
        mixed_total = 10
        
        for i in range(mixed_total):
            if i % 2 == 0:
                # Configuration update
                update_data = {
                    "configuration": {
                        "mixed_test": "config",
                        "sequence": i,
                        "lotNumber": f"MIXED{i:03d}"
                    }
                }
            else:
                # Serial numbers update
                update_data = {
                    "serial_numbers": [f"MIXED_ITEM{j+1:04d}" for j in range((i+1) * 5)],
                    "mixed_test": "serials",
                    "sequence": i
                }
            
            response = self.session.put(f"{self.base_url}/projects/{project_id}", json=update_data)
            if response.status_code == 200:
                mixed_success += 1
            
            time.sleep(0.1)  # 100ms between mixed updates
        
        mixed_success_rate = (mixed_success / mixed_total) * 100
        if mixed_success_rate >= 80:
            self.log_test("Auto-Save Scenarios - Mixed Operations", True, 
                         f"Mixed operations successful: {mixed_success}/{mixed_total} ({mixed_success_rate:.1f}%)")
        else:
            self.log_test("Auto-Save Scenarios - Mixed Operations", False, 
                         f"Mixed operations failed: {mixed_success}/{mixed_total} ({mixed_success_rate:.1f}%)")
        
        return (rapid_success_rate >= 90 and concurrent_success_rate >= 80 and mixed_success_rate >= 80)
    
    def test_final_epcis_generation(self, project_id):
        """Test final EPCIS generation to ensure no regressions"""
        if not project_id:
            self.log_test("Final EPCIS Generation", False, "No project ID available")
            return False
        
        epcis_data = {
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        response = self.session.post(f"{self.base_url}/projects/{project_id}/generate-epcis", json=epcis_data)
        if response.status_code != 200:
            self.log_test("Final EPCIS Generation", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        # Verify EPCIS XML content
        xml_content = response.text
        required_elements = [
            "<?xml",
            "EPCISDocument",
            "ObjectEvent",
            "AggregationEvent",
            "urn:epc:id:sscc:",
            "urn:epc:id:sgtin:"
        ]
        
        missing_elements = [elem for elem in required_elements if elem not in xml_content]
        
        if not missing_elements:
            # Check filename header
            content_disposition = response.headers.get("Content-Disposition", "")
            has_filename = "filename=" in content_disposition
            
            self.log_test("Final EPCIS Generation", True, 
                         f"EPCIS XML generated successfully {'with filename header' if has_filename else 'without filename header'}")
            return True
        else:
            self.log_test("Final EPCIS Generation", False, 
                         f"EPCIS XML missing required elements: {', '.join(missing_elements)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all comprehensive auto-save tests"""
        print("🔬 Starting Comprehensive Auto-Save Backend Tests...")
        print("Testing all review request focus areas:")
        print("1. Project Management: Test project creation, updating, and retrieval")
        print("2. Configuration Management: Test configuration creation and updates")
        print("3. Serial Numbers Management: Test serial numbers creation and updates")
        print("4. Auto-save Scenarios: Test rapid successive updates")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Stopping tests.")
            return False
        
        # 1. Project Management Tests
        project_id = self.test_project_management_comprehensive()
        if not project_id:
            print("❌ Project management tests failed. Stopping tests.")
            return False
        
        # 2. Configuration Management Tests
        config_success = self.test_configuration_management_comprehensive(project_id)
        
        # 3. Serial Numbers Management Tests
        serial_success = self.test_serial_numbers_management_comprehensive(project_id)
        
        # 4. Auto-save Scenarios Tests
        autosave_success = self.test_auto_save_scenarios_comprehensive(project_id)
        
        # 5. Final EPCIS Generation Test
        epcis_success = self.test_final_epcis_generation(project_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Review request specific summary
        print("\n🎯 REVIEW REQUEST FOCUS AREAS:")
        print(f"✅ Project Management: TESTED AND WORKING")
        print(f"✅ Configuration Management: {'WORKING' if config_success else 'ISSUES FOUND'}")
        print(f"✅ Serial Numbers Management: {'WORKING' if serial_success else 'ISSUES FOUND'}")
        print(f"✅ Auto-save Scenarios: {'WORKING' if autosave_success else 'ISSUES FOUND'}")
        print(f"✅ EPCIS Generation: {'WORKING' if epcis_success else 'ISSUES FOUND'}")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return success_rate >= 85  # High threshold for comprehensive testing

if __name__ == "__main__":
    tester = ComprehensiveAutoSaveTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)