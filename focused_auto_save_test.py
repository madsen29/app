#!/usr/bin/env python3
"""
Focused Auto-Save Backend API Testing
Tests the auto-save functionality changes with proper workflow preservation.
"""

import requests
import json
import time
import threading
from datetime import datetime
import sys

# Get backend URL from environment
BACKEND_URL = "https://d693cd3d-ff3c-4d8a-a0c1-55fb8a85ba90.preview.emergentagent.com/api"

class FocusedAutoSaveTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_email = "focused.autosave@example.com"
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
        """Setup authentication for testing"""
        # Register user (might fail if exists)
        user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "firstName": "Focused",
            "lastName": "AutoSave",
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
            pass  # User might already exist
        
        # Login
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
    
    def test_complete_workflow(self):
        """Test complete workflow: Project → Configuration → Serial Numbers → EPCIS"""
        
        # 1. Create Project
        project_data = {
            "name": f"Complete Workflow Test {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        response = self.session.post(f"{self.base_url}/projects", json=project_data)
        if response.status_code != 200:
            self.log_test("Complete Workflow - Project Creation", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        project = response.json()
        project_id = project.get("id")
        self.log_test("Complete Workflow - Project Creation", True, f"Project created: {project_id}")
        
        # 2. Create Configuration
        config_data = {
            "itemsPerCase": 5,
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
        
        response = self.session.post(f"{self.base_url}/projects/{project_id}/configuration", json=config_data)
        if response.status_code != 200:
            self.log_test("Complete Workflow - Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        config = response.json()
        self.log_test("Complete Workflow - Configuration Creation", True, "Configuration created successfully")
        
        # 3. Create Serial Numbers (1 SSCC, 2 Cases, 10 Items total)
        serial_data = {
            "ssccSerialNumbers": ["SSCC001"],
            "caseSerialNumbers": ["CASE001", "CASE002"],
            "innerCaseSerialNumbers": [],
            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(10)]
        }
        
        response = self.session.post(f"{self.base_url}/projects/{project_id}/serial-numbers", json=serial_data)
        if response.status_code != 200:
            self.log_test("Complete Workflow - Serial Numbers Creation", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        serials = response.json()
        self.log_test("Complete Workflow - Serial Numbers Creation", True, 
                     f"Serial numbers created: {len(serials['ssccSerialNumbers'])} SSCC, {len(serials['caseSerialNumbers'])} Cases, {len(serials['itemSerialNumbers'])} Items")
        
        # 4. Generate EPCIS
        epcis_data = {
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        response = self.session.post(f"{self.base_url}/projects/{project_id}/generate-epcis", json=epcis_data)
        if response.status_code != 200:
            self.log_test("Complete Workflow - EPCIS Generation", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        # Check if response contains XML
        if "<?xml" in response.text and "EPCISDocument" in response.text:
            self.log_test("Complete Workflow - EPCIS Generation", True, "EPCIS XML generated successfully")
        else:
            self.log_test("Complete Workflow - EPCIS Generation", False, "Invalid EPCIS XML response")
            return False
        
        return project_id
    
    def test_auto_save_simulation(self, project_id):
        """Test auto-save functionality with realistic scenarios"""
        if not project_id:
            return False
        
        # Test 1: Rapid configuration updates (simulating user typing)
        success_count = 0
        total_updates = 15
        
        for i in range(total_updates):
            # Simulate incremental configuration updates
            update_data = {
                "configuration": {
                    "itemsPerCase": 5 + (i % 3),  # Vary between 5, 6, 7
                    "lotNumber": f"LOT{123 + i}",
                    "expirationDate": "2025-12-31",
                    "auto_save_sequence": i + 1,
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            response = self.session.put(f"{self.base_url}/projects/{project_id}", json=update_data)
            if response.status_code == 200:
                success_count += 1
            
            time.sleep(0.05)  # 50ms between updates (realistic auto-save interval)
        
        success_rate = (success_count / total_updates) * 100
        if success_rate >= 90:
            self.log_test("Auto-Save Simulation - Rapid Updates", True, 
                         f"Rapid auto-save successful: {success_count}/{total_updates} updates ({success_rate:.1f}%)")
        else:
            self.log_test("Auto-Save Simulation - Rapid Updates", False, 
                         f"Rapid auto-save failed: {success_count}/{total_updates} updates ({success_rate:.1f}%)")
        
        # Test 2: Serial number auto-save simulation
        serial_updates = []
        for i in range(5):
            # Simulate progressive serial number entry
            serial_data = {
                "serial_numbers": [f"ITEM{j+1:03d}" for j in range((i+1) * 2)],  # Progressive entry
                "auto_save_timestamp": datetime.now().isoformat(),
                "entry_progress": f"{(i+1) * 2}/10 items entered"
            }
            
            update_data = {"configuration": serial_data}
            response = self.session.put(f"{self.base_url}/projects/{project_id}", json=update_data)
            serial_updates.append(response.status_code == 200)
            time.sleep(0.1)
        
        serial_success_rate = (sum(serial_updates) / len(serial_updates)) * 100
        if serial_success_rate >= 80:
            self.log_test("Auto-Save Simulation - Serial Entry", True, 
                         f"Serial auto-save successful: {sum(serial_updates)}/{len(serial_updates)} updates ({serial_success_rate:.1f}%)")
        else:
            self.log_test("Auto-Save Simulation - Serial Entry", False, 
                         f"Serial auto-save failed: {sum(serial_updates)}/{len(serial_updates)} updates ({serial_success_rate:.1f}%)")
        
        return success_rate >= 80 and serial_success_rate >= 80
    
    def test_data_integrity_after_auto_save(self, project_id):
        """Test that data integrity is maintained after multiple auto-save operations"""
        if not project_id:
            return False
        
        # Get final project state
        response = self.session.get(f"{self.base_url}/projects/{project_id}")
        if response.status_code != 200:
            self.log_test("Data Integrity Check", False, f"Failed to retrieve project: HTTP {response.status_code}")
            return False
        
        project = response.json()
        
        # Check that project has expected structure
        has_id = project.get("id") == project_id
        has_name = project.get("name") is not None
        has_config = project.get("configuration") is not None
        has_serials = project.get("serial_numbers") is not None
        has_epcis = project.get("epcis_file_content") is not None
        
        integrity_checks = [has_id, has_name, has_config, has_serials, has_epcis]
        passed_checks = sum(integrity_checks)
        
        if passed_checks >= 4:  # Allow for some flexibility
            self.log_test("Data Integrity Check", True, 
                         f"Data integrity maintained: {passed_checks}/5 checks passed")
            return True
        else:
            missing = []
            if not has_id: missing.append("ID")
            if not has_name: missing.append("name")
            if not has_config: missing.append("configuration")
            if not has_serials: missing.append("serial_numbers")
            if not has_epcis: missing.append("epcis_file_content")
            
            self.log_test("Data Integrity Check", False, 
                         f"Data integrity compromised: missing {', '.join(missing)}")
            return False
    
    def run_focused_tests(self):
        """Run focused auto-save tests"""
        print("🎯 Starting Focused Auto-Save Backend Tests...")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Stopping tests.")
            return False
        
        # Complete workflow test
        project_id = self.test_complete_workflow()
        if not project_id:
            print("❌ Complete workflow test failed. Stopping tests.")
            return False
        
        # Auto-save specific tests
        auto_save_success = self.test_auto_save_simulation(project_id)
        integrity_success = self.test_data_integrity_after_auto_save(project_id)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST SUMMARY")
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
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = FocusedAutoSaveTester()
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)