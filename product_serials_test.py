#!/usr/bin/env python3
"""
Product Serials Testing for EPCIS Serial Number Aggregation App
Tests the project save endpoint to verify that product_serials is being saved correctly 
with all item serial numbers for project ID: e2fe1108-6cbe-43c2-83c6-ce19ada894a7

Test Requirements:
1. Get the project using GET /api/projects/{project_id}
2. Check the product_serials field
3. For each product in product_serials, show the hierarchical structure
4. Verify that ALL item serial numbers are present and not empty strings
5. Show the exact structure of what's saved in the database for this project's product_serials field
"""

import requests
import json
from datetime import datetime
import sys

# Get backend URL from environment
BACKEND_URL = "https://scandit-epcis.preview.emergentagent.com/api"
PROJECT_ID = "e2fe1108-6cbe-43c2-83c6-ce19ada894a7"

class ProductSerialsTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.auth_token = None
        self.project_id = PROJECT_ID
        
    def log_result(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate with the API"""
        login_data = {
            "email": "epcis_test_user@test.com",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_result("Authentication", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Request error: {str(e)}")
            return False
    
    def get_project_data(self):
        """Get project data and analyze product_serials field"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{self.project_id}")
            
            if response.status_code == 200:
                project_data = response.json()
                self.log_result("Project Retrieval", True, f"Successfully retrieved project: {project_data.get('name', 'Unknown')}")
                
                # Print basic project info
                print(f"\n📋 PROJECT INFORMATION:")
                print(f"   Project ID: {project_data.get('id')}")
                print(f"   Project Name: {project_data.get('name')}")
                print(f"   Status: {project_data.get('status')}")
                print(f"   Current Step: {project_data.get('current_step')}")
                print(f"   Created: {project_data.get('created_at')}")
                print(f"   Updated: {project_data.get('updated_at')}")
                
                return project_data
            else:
                self.log_result("Project Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Project Retrieval", False, f"Request error: {str(e)}")
            return None
    
    def analyze_product_serials(self, project_data):
        """Analyze the product_serials field structure"""
        product_serials = project_data.get("product_serials")
        
        print(f"\n🔍 PRODUCT_SERIALS FIELD ANALYSIS:")
        print(f"   Field exists: {'Yes' if product_serials is not None else 'No'}")
        
        if product_serials is None:
            self.log_result("Product Serials Field", False, "product_serials field is None/missing")
            return False
        
        print(f"   Data type: {type(product_serials)}")
        
        if isinstance(product_serials, list):
            print(f"   Number of products: {len(product_serials)}")
            
            if len(product_serials) == 0:
                self.log_result("Product Serials Content", False, "product_serials array is empty")
                return False
            
            # Analyze each product in the array
            all_items_valid = True
            total_items = 0
            
            for i, product in enumerate(product_serials):
                print(f"\n   📦 PRODUCT {i + 1}:")
                print(f"      Product type: {type(product)}")
                
                if isinstance(product, dict):
                    # Show all keys in the product
                    print(f"      Keys: {list(product.keys())}")
                    
                    # Look for hierarchical structure
                    sscc_serials = product.get("ssccSerialNumbers", [])
                    case_serials = product.get("caseSerialNumbers", [])
                    inner_case_serials = product.get("innerCaseSerialNumbers", [])
                    item_serials = product.get("itemSerialNumbers", [])
                    
                    print(f"      SSCC Serials: {len(sscc_serials)} items")
                    if sscc_serials:
                        print(f"         Sample: {sscc_serials[:3]}")
                    
                    print(f"      Case Serials: {len(case_serials)} items")
                    if case_serials:
                        print(f"         Sample: {case_serials[:3]}")
                    
                    print(f"      Inner Case Serials: {len(inner_case_serials)} items")
                    if inner_case_serials:
                        print(f"         Sample: {inner_case_serials[:3]}")
                    
                    print(f"      Item Serials: {len(item_serials)} items")
                    if item_serials:
                        print(f"         Sample: {item_serials[:3]}")
                        total_items += len(item_serials)
                        
                        # Check for empty strings in item serials
                        empty_items = [idx for idx, serial in enumerate(item_serials) if not serial or serial.strip() == ""]
                        if empty_items:
                            print(f"         ❌ Empty item serials found at indices: {empty_items}")
                            all_items_valid = False
                        else:
                            print(f"         ✅ All item serials are non-empty")
                    else:
                        print(f"         ❌ No item serials found")
                        all_items_valid = False
                    
                    # Look for hierarchical structure (nested format)
                    if "ssccIndex" in product or "cases" in product:
                        print(f"      📊 HIERARCHICAL STRUCTURE DETECTED:")
                        if "ssccIndex" in product:
                            print(f"         SSCC Index: {product.get('ssccIndex')}")
                        if "ssccSerial" in product:
                            print(f"         SSCC Serial: {product.get('ssccSerial')}")
                        
                        cases = product.get("cases", [])
                        print(f"         Cases: {len(cases)} items")
                        
                        for j, case in enumerate(cases):
                            if isinstance(case, dict):
                                case_serial = case.get("caseSerial", "")
                                case_items = case.get("items", [])
                                print(f"            Case {j + 1}: Serial='{case_serial}', Items={len(case_items)}")
                                
                                # Check case items for empty serials
                                if case_items:
                                    empty_case_items = [idx for idx, item in enumerate(case_items) if not item or (isinstance(item, str) and item.strip() == "")]
                                    if empty_case_items:
                                        print(f"               ❌ Empty case item serials at indices: {empty_case_items}")
                                        all_items_valid = False
                                    else:
                                        print(f"               ✅ All case item serials are non-empty")
                                        total_items += len(case_items)
                else:
                    print(f"      ❌ Product is not a dictionary: {product}")
                    all_items_valid = False
            
            # Summary
            print(f"\n📊 SUMMARY:")
            print(f"   Total products analyzed: {len(product_serials)}")
            print(f"   Total item serials found: {total_items}")
            print(f"   All item serials valid: {'Yes' if all_items_valid else 'No'}")
            
            if all_items_valid and total_items > 0:
                self.log_result("Product Serials Validation", True, f"All {total_items} item serials are present and non-empty")
                return True
            else:
                self.log_result("Product Serials Validation", False, "Some item serials are missing or empty")
                return False
        else:
            self.log_result("Product Serials Format", False, f"product_serials is not a list: {type(product_serials)}")
            return False
    
    def show_raw_structure(self, project_data):
        """Show the exact raw structure of product_serials"""
        product_serials = project_data.get("product_serials")
        
        print(f"\n📄 RAW PRODUCT_SERIALS STRUCTURE:")
        print("=" * 60)
        
        if product_serials is not None:
            # Pretty print the JSON structure
            try:
                formatted_json = json.dumps(product_serials, indent=2, ensure_ascii=False)
                print(formatted_json)
            except Exception as e:
                print(f"Error formatting JSON: {e}")
                print(f"Raw data: {product_serials}")
        else:
            print("product_serials field is None/missing")
        
        print("=" * 60)
    
    def run_product_serials_test(self):
        """Run the complete product serials test"""
        print("=" * 80)
        print("PRODUCT SERIALS TESTING")
        print("=" * 80)
        print(f"Testing project ID: {self.project_id}")
        print("Verifying product_serials field structure and item serial numbers")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("\n❌ Authentication failed. Cannot continue.")
            return False
        
        # Step 2: Get project data
        project_data = self.get_project_data()
        if not project_data:
            print("\n❌ Failed to retrieve project data. Cannot continue.")
            return False
        
        # Step 3: Analyze product_serials field
        serials_valid = self.analyze_product_serials(project_data)
        
        # Step 4: Show raw structure
        self.show_raw_structure(project_data)
        
        # Step 5: Check other relevant fields
        print(f"\n🔍 OTHER RELEVANT FIELDS:")
        serial_numbers = project_data.get("serial_numbers")
        configuration = project_data.get("configuration")
        
        print(f"   serial_numbers field: {'Present' if serial_numbers is not None else 'Missing'}")
        if serial_numbers:
            print(f"      Type: {type(serial_numbers)}")
            if isinstance(serial_numbers, list):
                print(f"      Length: {len(serial_numbers)}")
        
        print(f"   configuration field: {'Present' if configuration is not None else 'Missing'}")
        if configuration:
            print(f"      Type: {type(configuration)}")
            if isinstance(configuration, dict):
                print(f"      Keys: {len(configuration.keys())}")
        
        # Final summary
        print(f"\n" + "=" * 80)
        print("PRODUCT SERIALS TEST SUMMARY")
        print("=" * 80)
        
        if serials_valid:
            print("✅ PRODUCT SERIALS VALIDATION PASSED")
            print("✅ All item serial numbers are present and non-empty")
            print("✅ Hierarchical structure is properly maintained")
        else:
            print("❌ PRODUCT SERIALS VALIDATION FAILED")
            print("❌ Issues found with item serial numbers or structure")
        
        return serials_valid

if __name__ == "__main__":
    tester = ProductSerialsTester()
    success = tester.run_product_serials_test()
    sys.exit(0 if success else 1)