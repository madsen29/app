#!/usr/bin/env python3
"""
Multi-Product Serial Numbers Testing for EPCIS Serial Number Aggregation App
Creates a project with product_serials field and tests the hierarchical structure
to verify that ALL item serial numbers are present and not empty strings.

This test creates the scenario requested in the review:
1. Create a project and configuration
2. Add product_serials with hierarchical structure
3. Verify the product_serials field structure
4. Check that all item serial numbers are present and non-empty
"""

import requests
import json
from datetime import datetime
import sys

# Get backend URL from environment
BACKEND_URL = "https://scandit-epcis.preview.emergentagent.com/api"

class MultiProductTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.auth_token = None
        self.test_project_id = None
        
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
    
    def create_test_project(self):
        """Create a test project"""
        project_data = {
            "name": f"Multi-Product Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_project_id = data["id"]
                self.log_result("Project Creation", True, f"Created project: {data['name']}", f"ID: {self.test_project_id}")
                return True
            else:
                self.log_result("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Project Creation", False, f"Request error: {str(e)}")
            return False
    
    def create_configuration(self):
        """Create configuration for the project"""
        config_data = {
            "itemsPerCase": 3,
            "casesPerSscc": 2,
            "numberOfSscc": 1,
            "useInnerCases": False,
            "companyPrefix": "1234567",
            "itemProductCode": "000000",
            "caseProductCode": "000001",
            "lotNumber": "LOT123456",
            "expirationDate": "2026-12-31",
            "ssccExtensionDigit": "3",
            "caseIndicatorDigit": "2",
            "itemIndicatorDigit": "1",
            # Business document information
            "senderCompanyPrefix": "0345802",
            "senderGln": "0345802000014",
            "senderSgln": "0345802000014.001",
            "receiverCompanyPrefix": "0567890",
            "receiverGln": "0567890000021",
            "receiverSgln": "0567890000021.001",
            "shipperCompanyPrefix": "0999888",
            "shipperGln": "0999888000028",
            "shipperSgln": "0999888000028.001"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/configuration",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.log_result("Configuration Creation", True, "Configuration created successfully")
                return True
            else:
                self.log_result("Configuration Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Configuration Creation", False, f"Request error: {str(e)}")
            return False
    
    def add_product_serials(self):
        """Add product_serials to the project using hierarchical structure"""
        # Create a hierarchical structure with multiple products
        product_serials = [
            {
                "productIndex": 0,
                "productName": "Product A - Metformin 500mg",
                "ssccIndex": 0,
                "ssccSerial": "SSCC_PROD_A_001",
                "cases": [
                    {
                        "caseIndex": 0,
                        "caseSerial": "CASE_PROD_A_001",
                        "items": [
                            "ITEM_PROD_A_001",
                            "ITEM_PROD_A_002",
                            "ITEM_PROD_A_003"
                        ]
                    },
                    {
                        "caseIndex": 1,
                        "caseSerial": "CASE_PROD_A_002",
                        "items": [
                            "ITEM_PROD_A_004",
                            "ITEM_PROD_A_005",
                            "ITEM_PROD_A_006"
                        ]
                    }
                ]
            },
            {
                "productIndex": 1,
                "productName": "Product B - Lisinopril 10mg",
                "ssccIndex": 0,
                "ssccSerial": "SSCC_PROD_B_001",
                "cases": [
                    {
                        "caseIndex": 0,
                        "caseSerial": "CASE_PROD_B_001",
                        "items": [
                            "ITEM_PROD_B_001",
                            "ITEM_PROD_B_002",
                            "ITEM_PROD_B_003"
                        ]
                    },
                    {
                        "caseIndex": 1,
                        "caseSerial": "CASE_PROD_B_002",
                        "items": [
                            "ITEM_PROD_B_004",
                            "ITEM_PROD_B_005",
                            "ITEM_PROD_B_006"
                        ]
                    }
                ]
            }
        ]
        
        # Also create flat format for compatibility
        sscc_serials = ["SSCC_PROD_A_001", "SSCC_PROD_B_001"]
        case_serials = ["CASE_PROD_A_001", "CASE_PROD_A_002", "CASE_PROD_B_001", "CASE_PROD_B_002"]
        item_serials = [
            "ITEM_PROD_A_001", "ITEM_PROD_A_002", "ITEM_PROD_A_003",
            "ITEM_PROD_A_004", "ITEM_PROD_A_005", "ITEM_PROD_A_006",
            "ITEM_PROD_B_001", "ITEM_PROD_B_002", "ITEM_PROD_B_003",
            "ITEM_PROD_B_004", "ITEM_PROD_B_005", "ITEM_PROD_B_006"
        ]
        
        update_data = {
            "product_serials": product_serials,
            "serial_numbers": [
                {"type": "sscc", "serial": s} for s in sscc_serials
            ] + [
                {"type": "case", "serial": s} for s in case_serials
            ] + [
                {"type": "item", "serial": s} for s in item_serials
            ]
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/projects/{self.test_project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.log_result("Product Serials Addition", True, f"Added {len(product_serials)} products with hierarchical structure")
                return True
            else:
                self.log_result("Product Serials Addition", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Product Serials Addition", False, f"Request error: {str(e)}")
            return False
    
    def verify_product_serials(self):
        """Verify the product_serials field structure and content"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{self.test_project_id}")
            
            if response.status_code == 200:
                project_data = response.json()
                
                print(f"\n📋 PROJECT VERIFICATION:")
                print(f"   Project ID: {project_data.get('id')}")
                print(f"   Project Name: {project_data.get('name')}")
                print(f"   Status: {project_data.get('status')}")
                
                # Check product_serials field
                product_serials = project_data.get("product_serials")
                
                print(f"\n🔍 PRODUCT_SERIALS FIELD ANALYSIS:")
                print(f"   Field exists: {'Yes' if product_serials is not None else 'No'}")
                
                if product_serials is None:
                    self.log_result("Product Serials Verification", False, "product_serials field is None/missing")
                    return False
                
                print(f"   Data type: {type(product_serials)}")
                print(f"   Number of products: {len(product_serials) if isinstance(product_serials, list) else 'N/A'}")
                
                if not isinstance(product_serials, list):
                    self.log_result("Product Serials Verification", False, f"product_serials is not a list: {type(product_serials)}")
                    return False
                
                if len(product_serials) == 0:
                    self.log_result("Product Serials Verification", False, "product_serials array is empty")
                    return False
                
                # Analyze each product
                all_items_valid = True
                total_items = 0
                
                for i, product in enumerate(product_serials):
                    print(f"\n   📦 PRODUCT {i + 1}:")
                    print(f"      Product Name: {product.get('productName', 'N/A')}")
                    print(f"      SSCC Serial: {product.get('ssccSerial', 'N/A')}")
                    
                    cases = product.get("cases", [])
                    print(f"      Cases: {len(cases)}")
                    
                    product_items = 0
                    for j, case in enumerate(cases):
                        case_serial = case.get("caseSerial", "")
                        case_items = case.get("items", [])
                        print(f"         Case {j + 1}: Serial='{case_serial}', Items={len(case_items)}")
                        
                        # Check for empty item serials
                        if case_items:
                            empty_items = [idx for idx, item in enumerate(case_items) if not item or (isinstance(item, str) and item.strip() == "")]
                            if empty_items:
                                print(f"            ❌ Empty item serials at indices: {empty_items}")
                                all_items_valid = False
                            else:
                                print(f"            ✅ All {len(case_items)} item serials are non-empty")
                                print(f"            Sample items: {case_items[:2]}")
                                product_items += len(case_items)
                        else:
                            print(f"            ❌ No items found in case")
                            all_items_valid = False
                    
                    total_items += product_items
                    print(f"      Total items in product: {product_items}")
                
                # Summary
                print(f"\n📊 VERIFICATION SUMMARY:")
                print(f"   Total products: {len(product_serials)}")
                print(f"   Total item serials: {total_items}")
                print(f"   All item serials valid: {'Yes' if all_items_valid else 'No'}")
                
                # Show raw structure
                print(f"\n📄 RAW PRODUCT_SERIALS STRUCTURE:")
                print("=" * 60)
                try:
                    formatted_json = json.dumps(product_serials, indent=2, ensure_ascii=False)
                    print(formatted_json)
                except Exception as e:
                    print(f"Error formatting JSON: {e}")
                    print(f"Raw data: {product_serials}")
                print("=" * 60)
                
                if all_items_valid and total_items > 0:
                    self.log_result("Product Serials Verification", True, f"All {total_items} item serials are present and non-empty across {len(product_serials)} products")
                    return True
                else:
                    self.log_result("Product Serials Verification", False, "Some item serials are missing or empty")
                    return False
                    
            else:
                self.log_result("Product Serials Verification", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Product Serials Verification", False, f"Request error: {str(e)}")
            return False
    
    def test_epcis_generation(self):
        """Test EPCIS generation with multi-product data"""
        epcis_request = {
            "readPoint": "urn:epc:id:sgln:1234567.00000.0",
            "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/projects/{self.test_project_id}/generate-epcis",
                json=epcis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                xml_content = response.text
                
                # Check for multi-product serials in XML
                product_a_items = ["ITEM_PROD_A_001", "ITEM_PROD_A_002", "ITEM_PROD_A_003"]
                product_b_items = ["ITEM_PROD_B_001", "ITEM_PROD_B_002", "ITEM_PROD_B_003"]
                
                items_found = 0
                for item in product_a_items + product_b_items:
                    if item in xml_content:
                        items_found += 1
                
                if items_found >= 6:  # At least some items from both products
                    self.log_result("EPCIS Generation", True, f"EPCIS XML generated with multi-product data ({items_found} items found)")
                    return True
                else:
                    self.log_result("EPCIS Generation", False, f"Only {items_found} items found in EPCIS XML")
                    return False
            else:
                self.log_result("EPCIS Generation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("EPCIS Generation", False, f"Request error: {str(e)}")
            return False
    
    def run_multi_product_test(self):
        """Run the complete multi-product test"""
        print("=" * 80)
        print("MULTI-PRODUCT SERIAL NUMBERS TESTING")
        print("=" * 80)
        print("Creating and testing project with product_serials field")
        print("Verifying hierarchical structure and item serial numbers")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("\n❌ Authentication failed. Cannot continue.")
            return False
        
        # Step 2: Create test project
        if not self.create_test_project():
            print("\n❌ Project creation failed. Cannot continue.")
            return False
        
        # Step 3: Create configuration
        if not self.create_configuration():
            print("\n❌ Configuration creation failed. Cannot continue.")
            return False
        
        # Step 4: Add product_serials
        if not self.add_product_serials():
            print("\n❌ Product serials addition failed. Cannot continue.")
            return False
        
        # Step 5: Verify product_serials structure
        serials_valid = self.verify_product_serials()
        
        # Step 6: Test EPCIS generation
        epcis_valid = self.test_epcis_generation()
        
        # Final summary
        print(f"\n" + "=" * 80)
        print("MULTI-PRODUCT TEST SUMMARY")
        print("=" * 80)
        
        if serials_valid and epcis_valid:
            print("✅ MULTI-PRODUCT FUNCTIONALITY WORKING")
            print("✅ Product_serials field properly saves hierarchical structure")
            print("✅ All item serial numbers are present and non-empty")
            print("✅ EPCIS generation works with multi-product data")
            print(f"✅ Test project ID: {self.test_project_id}")
        else:
            print("❌ MULTI-PRODUCT FUNCTIONALITY ISSUES DETECTED")
            if not serials_valid:
                print("❌ Product_serials structure or content issues")
            if not epcis_valid:
                print("❌ EPCIS generation issues with multi-product data")
        
        return serials_valid and epcis_valid

if __name__ == "__main__":
    tester = MultiProductTester()
    success = tester.run_multi_product_test()
    sys.exit(0 if success else 1)