#!/usr/bin/env python3
"""
Debug Project Test - Check what happened to the product_serials field
"""

import requests
import json

# Get backend URL from environment
BACKEND_URL = "https://bulk-gs1-builder.preview.emergentagent.com/api"
PROJECT_ID = "a57661ea-634c-44b3-8d4e-08eb72f9c23a"  # From the previous test

class ProjectDebugger:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.auth_token = None
        
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
                print("✅ Successfully authenticated")
                return True
            else:
                print(f"❌ Authentication failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def debug_project(self, project_id):
        """Debug the specific project"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                project = response.json()
                
                print(f"\n📋 PROJECT DEBUG ANALYSIS:")
                print(f"   Project ID: {project.get('id')}")
                print(f"   Name: {project.get('name')}")
                print(f"   Status: {project.get('status')}")
                
                print(f"\n🔍 ALL FIELDS:")
                for key, value in project.items():
                    print(f"   {key}: {type(value)} = {value if not isinstance(value, (dict, list)) or len(str(value)) < 100 else f'{type(value)} (length: {len(value)})'}")
                
                # Check if product_serials exists at all
                has_product_serials_key = 'product_serials' in project
                product_serials_value = project.get('product_serials')
                
                print(f"\n📦 PRODUCT_SERIALS ANALYSIS:")
                print(f"   Key exists in response: {has_product_serials_key}")
                print(f"   Value: {product_serials_value}")
                print(f"   Type: {type(product_serials_value)}")
                
                # Show raw JSON
                print(f"\n📄 RAW PROJECT JSON:")
                print("=" * 60)
                try:
                    formatted_json = json.dumps(project, indent=2, ensure_ascii=False)
                    print(formatted_json)
                except Exception as e:
                    print(f"Error formatting JSON: {e}")
                    print(f"Raw data: {project}")
                print("=" * 60)
                
                return project
            else:
                print(f"❌ Failed to get project: HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error debugging project: {str(e)}")
            return None
    
    def test_update_with_product_serials(self, project_id):
        """Test updating project with product_serials directly"""
        print(f"\n🔧 TESTING DIRECT PRODUCT_SERIALS UPDATE:")
        
        # Simple test data
        test_product_serials = [
            {
                "productIndex": 0,
                "productName": "Test Product",
                "ssccSerial": "TEST_SSCC_001",
                "cases": [
                    {
                        "caseSerial": "TEST_CASE_001",
                        "items": ["TEST_ITEM_001", "TEST_ITEM_002"]
                    }
                ]
            }
        ]
        
        update_data = {
            "product_serials": test_product_serials
        }
        
        try:
            print(f"   Sending update request with product_serials...")
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Update successful")
                
                # Check if product_serials is in the response
                updated_product_serials = data.get('product_serials')
                print(f"   product_serials in response: {updated_product_serials is not None}")
                if updated_product_serials:
                    print(f"   product_serials value: {updated_product_serials}")
                
                return True
            else:
                print(f"   Update failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   Update error: {str(e)}")
            return False
    
    def run(self):
        """Run the debug analysis"""
        print("=" * 80)
        print("PROJECT DEBUG ANALYSIS")
        print("=" * 80)
        
        if not self.authenticate():
            return False
        
        # Debug the project
        project = self.debug_project(PROJECT_ID)
        if not project:
            return False
        
        # Test direct update
        self.test_update_with_product_serials(PROJECT_ID)
        
        # Check again after update
        print(f"\n🔄 CHECKING PROJECT AFTER UPDATE:")
        updated_project = self.debug_project(PROJECT_ID)
        
        return True

if __name__ == "__main__":
    debugger = ProjectDebugger()
    debugger.run()