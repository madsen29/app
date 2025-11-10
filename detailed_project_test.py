#!/usr/bin/env python3
"""
Detailed Project Analysis - Examine project structure to understand serial number storage
"""

import requests
import json
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://scandit-epcis.preview.emergentagent.com/api"

class DetailedProjectAnalyzer:
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
    
    def analyze_project(self, project_id):
        """Analyze a specific project in detail"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            
            if response.status_code == 200:
                project = response.json()
                
                print(f"\n📋 DETAILED PROJECT ANALYSIS:")
                print(f"   Project ID: {project.get('id')}")
                print(f"   Name: {project.get('name')}")
                print(f"   Status: {project.get('status')}")
                print(f"   Current Step: {project.get('current_step')}")
                
                # Analyze all fields
                print(f"\n🔍 ALL PROJECT FIELDS:")
                for key, value in project.items():
                    if key in ['id', 'name', 'status', 'current_step']:
                        continue  # Already shown above
                    
                    print(f"   {key}: {type(value)}")
                    if value is not None:
                        if isinstance(value, (list, dict)):
                            if isinstance(value, list):
                                print(f"      Length: {len(value)}")
                                if len(value) > 0:
                                    print(f"      First item type: {type(value[0])}")
                            elif isinstance(value, dict):
                                print(f"      Keys: {len(value.keys())}")
                                if len(value) <= 10:  # Show keys if not too many
                                    print(f"      Key names: {list(value.keys())}")
                
                # Focus on serial_numbers field
                serial_numbers = project.get("serial_numbers")
                if serial_numbers:
                    print(f"\n📊 SERIAL_NUMBERS FIELD ANALYSIS:")
                    print(f"   Type: {type(serial_numbers)}")
                    
                    if isinstance(serial_numbers, list):
                        print(f"   Length: {len(serial_numbers)}")
                        
                        for i, item in enumerate(serial_numbers):
                            print(f"\n   Item {i + 1}:")
                            print(f"      Type: {type(item)}")
                            
                            if isinstance(item, dict):
                                print(f"      Keys: {list(item.keys())}")
                                for key, value in item.items():
                                    if isinstance(value, str):
                                        print(f"         {key}: '{value}'")
                                    else:
                                        print(f"         {key}: {value} ({type(value)})")
                            else:
                                print(f"      Value: {item}")
                
                # Focus on product_serials field (even if None)
                product_serials = project.get("product_serials")
                print(f"\n📦 PRODUCT_SERIALS FIELD:")
                print(f"   Exists: {'Yes' if 'product_serials' in project else 'No'}")
                print(f"   Value: {product_serials}")
                print(f"   Type: {type(product_serials)}")
                
                # Show raw JSON for key fields
                print(f"\n📄 RAW SERIAL_NUMBERS JSON:")
                print("=" * 60)
                if serial_numbers:
                    try:
                        formatted_json = json.dumps(serial_numbers, indent=2, ensure_ascii=False)
                        print(formatted_json)
                    except Exception as e:
                        print(f"Error formatting JSON: {e}")
                        print(f"Raw data: {serial_numbers}")
                else:
                    print("serial_numbers field is None/missing")
                print("=" * 60)
                
                return project
            else:
                print(f"❌ Failed to get project: HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error analyzing project: {str(e)}")
            return None
    
    def run(self):
        """Run the detailed project analysis"""
        print("=" * 80)
        print("DETAILED PROJECT ANALYSIS")
        print("=" * 80)
        
        if not self.authenticate():
            return False
        
        # Analyze a few completed projects
        completed_project_ids = [
            "4caa6c4a-6726-45b0-8f8c-6fb508220d37",  # EPCIS Fix Test Project 20250719_195045
            "819a8535-065d-4bca-a642-e0f6e946cb27",  # Updated Baseline Test Project
            "0f4de023-1bd2-47d5-a5aa-f2f38591c4e6"   # Baseline Test Project
        ]
        
        for project_id in completed_project_ids:
            print(f"\n{'='*80}")
            print(f"ANALYZING PROJECT: {project_id}")
            print(f"{'='*80}")
            
            project = self.analyze_project(project_id)
            if not project:
                continue
        
        return True

if __name__ == "__main__":
    analyzer = DetailedProjectAnalyzer()
    analyzer.run()