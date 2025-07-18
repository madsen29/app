#!/usr/bin/env python3
"""
Final Verification Test for EPCIS Critical Issues

This test verifies that all three critical issues have been resolved using the exact
configuration specified in the review request.
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys

# Get backend URL from environment
BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

class FinalVerificationTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.auth_token = None
        
    def setup_test_user(self):
        """Create a test user and get authentication token"""
        user_data = {
            "email": "final_test@example.com",
            "password": "testpass123",
            "firstName": "Final",
            "lastName": "Tester",
            "companyName": "Test Company",
            "streetAddress": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "postalCode": "12345",
            "countryCode": "US"
        }
        
        try:
            # Try to register (might fail if user exists)
            self.session.post(f"{self.base_url}/auth/register", json=user_data)
            
            # Login to get token
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                return True
            return False
        except:
            return False
    
    def run_final_verification(self):
        """Run final verification with exact review request configuration"""
        print("=" * 80)
        print("FINAL VERIFICATION - EPCIS CRITICAL ISSUES RESOLUTION")
        print("=" * 80)
        print("Testing with EXACT configuration from review request:")
        print("- company_prefix: '1234567'")
        print("- product_code: '000000'")
        print("- sscc_extension_digit: '3'")
        print("- item_indicator_digit: '1'")
        print("- case_indicator_digit: '2'")
        print("- inner_case_indicator_digit: '4'")
        print("- use_inner_cases: true")
        print("- 4-level hierarchy: 1 SSCC → 2 cases → 3 inner cases → 4 items")
        print("=" * 80)
        
        # Setup authentication
        if not self.setup_test_user():
            print("❌ Authentication failed")
            return False
        
        # Create project
        project_response = self.session.post(f"{self.base_url}/projects", 
                                           json={"name": "Final Verification Test"})
        if project_response.status_code != 200:
            print("❌ Project creation failed")
            return False
        
        project_id = project_response.json()["id"]
        print(f"✅ Created test project: {project_id}")
        
        # Create configuration with exact review request parameters
        config_data = {
            "itemsPerCase": 0,
            "casesPerSscc": 2,
            "numberOfSscc": 1,
            "useInnerCases": True,
            "innerCasesPerCase": 3,
            "itemsPerInnerCase": 4,
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000000",
            "innerCaseProductCode": "000000",
            "lotNumber": "LOT123456",
            "expirationDate": "2026-12-31",
            "ssccExtensionDigit": "3",
            "caseIndicatorDigit": "2",
            "innerCaseIndicatorDigit": "4",
            "itemIndicatorDigit": "1",
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001",
            "shipperSameAsSender": False,
            "packageNdc": "45802-046-85",
            "regulatedProductName": "Test Pharmaceutical Product",
            "manufacturerName": "Test Pharma Inc"
        }
        
        config_response = self.session.post(f"{self.base_url}/projects/{project_id}/configuration", 
                                          json=config_data)
        if config_response.status_code != 200:
            print("❌ Configuration creation failed")
            return False
        
        print("✅ Created configuration with review request parameters")
        
        # Create serial numbers (1 SSCC, 2 cases, 6 inner cases, 24 items)
        serial_data = {
            "ssccSerialNumbers": ["TEST001"],
            "caseSerialNumbers": ["CASE001", "CASE002"],
            "innerCaseSerialNumbers": [f"INNER{i+1:03d}" for i in range(6)],
            "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(24)]
        }
        
        serial_response = self.session.post(f"{self.base_url}/projects/{project_id}/serial-numbers", 
                                          json=serial_data)
        if serial_response.status_code != 200:
            print("❌ Serial numbers creation failed")
            return False
        
        print("✅ Created serial numbers for 4-level hierarchy")
        
        # Generate EPCIS XML
        epcis_response = self.session.post(f"{self.base_url}/projects/{project_id}/generate-epcis", 
                                         json={"readPoint": "urn:epc:id:sgln:1234567.00000.0",
                                              "bizLocation": "urn:epc:id:sgln:1234567.00001.0"})
        if epcis_response.status_code != 200:
            print("❌ EPCIS generation failed")
            return False
        
        xml_content = epcis_response.text
        print("✅ Generated EPCIS XML successfully")
        
        # Verify all three critical issues are resolved
        print("\n" + "=" * 50)
        print("CRITICAL ISSUES VERIFICATION")
        print("=" * 50)
        
        # Issue 1: Inner case EPCClass vocabulary
        root = ET.fromstring(xml_content)
        vocabulary_elements = []
        for elem in root.iter():
            if elem.tag.endswith("VocabularyElement"):
                vocab_id = elem.get("id")
                if vocab_id and "sgtin" in vocab_id:
                    vocabulary_elements.append(vocab_id)
        
        inner_case_pattern = "urn:epc:idpat:sgtin:1234567.4000000.*"
        issue1_resolved = inner_case_pattern in vocabulary_elements
        print(f"Issue 1 - Inner Case EPCClass: {'✅ RESOLVED' if issue1_resolved else '❌ FAILED'}")
        if issue1_resolved:
            print(f"  Found: {inner_case_pattern}")
        
        # Issue 2: Product code in SGTINs
        correct_patterns = [
            "sgtin:1234567.1000000.",  # Item
            "sgtin:1234567.2000000.",  # Case
            "sgtin:1234567.4000000."   # Inner Case
        ]
        issue2_resolved = all(pattern in xml_content for pattern in correct_patterns)
        none_found = "None" in xml_content and "sgtin" in xml_content
        issue2_resolved = issue2_resolved and not none_found
        print(f"Issue 2 - Product Code Values: {'✅ RESOLVED' if issue2_resolved else '❌ FAILED'}")
        if issue2_resolved:
            print("  All SGTINs contain correct product code '000000'")
        
        # Issue 3: SSCC extension digit
        correct_sscc = "sscc:0999888.3TEST001" in xml_content
        none_sscc = "sscc:0999888.None" in xml_content
        issue3_resolved = correct_sscc and not none_sscc
        print(f"Issue 3 - SSCC Extension Digit: {'✅ RESOLVED' if issue3_resolved else '❌ FAILED'}")
        if issue3_resolved:
            print("  SSCC contains correct extension digit '3'")
        
        # Overall result
        all_resolved = issue1_resolved and issue2_resolved and issue3_resolved
        print("\n" + "=" * 50)
        print(f"OVERALL RESULT: {'✅ ALL ISSUES RESOLVED' if all_resolved else '❌ SOME ISSUES REMAIN'}")
        print("=" * 50)
        
        if all_resolved:
            print("🎉 SUCCESS: All three critical issues have been successfully resolved!")
            print("\nExpected results achieved:")
            print("✅ Inner case EPCClass appears in vocabulary with pattern: urn:epc:idpat:sgtin:1234567.4000000.*")
            print("✅ All SGTINs show product code '000000' instead of 'None'")
            print("✅ SSCC shows extension digit '3' instead of 'None'")
        else:
            print("❌ FAILURE: Some critical issues are still present")
        
        return all_resolved

if __name__ == "__main__":
    tester = FinalVerificationTester()
    success = tester.run_final_verification()
    sys.exit(0 if success else 1)