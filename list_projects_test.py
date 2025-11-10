#!/usr/bin/env python3
"""
List Projects Test - Find available projects for the test user
"""

import requests
import json
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://scandit-epcis.preview.emergentagent.com/api"

class ProjectLister:
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
    
    def list_projects(self):
        """List all projects for the authenticated user"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            
            if response.status_code == 200:
                projects = response.json()
                print(f"\n📋 FOUND {len(projects)} PROJECTS:")
                print("=" * 80)
                
                for i, project in enumerate(projects):
                    print(f"\n{i + 1}. PROJECT:")
                    print(f"   ID: {project.get('id')}")
                    print(f"   Name: {project.get('name')}")
                    print(f"   Status: {project.get('status')}")
                    print(f"   Current Step: {project.get('current_step')}")
                    print(f"   Created: {project.get('created_at')}")
                    print(f"   Updated: {project.get('updated_at')}")
                    
                    # Check for product_serials field
                    product_serials = project.get("product_serials")
                    serial_numbers = project.get("serial_numbers")
                    configuration = project.get("configuration")
                    
                    print(f"   Has product_serials: {'Yes' if product_serials is not None else 'No'}")
                    if product_serials:
                        print(f"      Type: {type(product_serials)}")
                        if isinstance(product_serials, list):
                            print(f"      Length: {len(product_serials)}")
                    
                    print(f"   Has serial_numbers: {'Yes' if serial_numbers is not None else 'No'}")
                    if serial_numbers:
                        print(f"      Type: {type(serial_numbers)}")
                        if isinstance(serial_numbers, list):
                            print(f"      Length: {len(serial_numbers)}")
                    
                    print(f"   Has configuration: {'Yes' if configuration is not None else 'No'}")
                
                # Look for projects with product_serials
                projects_with_product_serials = [p for p in projects if p.get("product_serials") is not None]
                
                print(f"\n🎯 PROJECTS WITH PRODUCT_SERIALS: {len(projects_with_product_serials)}")
                if projects_with_product_serials:
                    for project in projects_with_product_serials:
                        print(f"   - {project.get('name')} (ID: {project.get('id')})")
                
                return projects
            else:
                print(f"❌ Failed to list projects: HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error listing projects: {str(e)}")
            return None
    
    def run(self):
        """Run the project listing"""
        print("=" * 80)
        print("PROJECT LISTING TEST")
        print("=" * 80)
        
        if not self.authenticate():
            return False
        
        projects = self.list_projects()
        return projects is not None

if __name__ == "__main__":
    lister = ProjectLister()
    lister.run()