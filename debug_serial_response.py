#!/usr/bin/env python3
"""
Debug test to investigate the serial number response format issue
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

def debug_serial_number_response():
    session = requests.Session()
    
    # Create test user
    user_data = {
        "email": f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "testpassword123",
        "firstName": "Debug",
        "lastName": "User",
        "companyName": "Debug Company",
        "streetAddress": "123 Debug St",
        "city": "Debug City",
        "state": "DS",
        "postalCode": "12345",
        "countryCode": "US"
    }
    
    # Register and login
    register_response = session.post(f"{BACKEND_URL}/auth/register", json=user_data)
    if register_response.status_code != 200:
        print(f"Registration failed: {register_response.status_code}")
        return
    
    login_response = session.post(f"{BACKEND_URL}/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Create project
    project_response = session.post(f"{BACKEND_URL}/projects", json={"name": "Debug Project"})
    if project_response.status_code != 200:
        print(f"Project creation failed: {project_response.status_code}")
        return
    
    project_id = project_response.json()["id"]
    print(f"Created project: {project_id}")
    
    # Create configuration
    config = {
        "numberOfSscc": 1,
        "casesPerSscc": 2,
        "useInnerCases": True,
        "innerCasesPerCase": 3,
        "itemsPerInnerCase": 4,
        "companyPrefix": "1234567",
        "itemProductCode": "000000",
        "caseProductCode": "000001",
        "innerCaseProductCode": "000002",
        "ssccIndicatorDigit": "3",
        "caseIndicatorDigit": "2",
        "innerCaseIndicatorDigit": "4",
        "itemIndicatorDigit": "1"
    }
    
    config_response = session.post(f"{BACKEND_URL}/projects/{project_id}/configuration", json=config)
    if config_response.status_code != 200:
        print(f"Configuration creation failed: {config_response.status_code}")
        print(f"Response: {config_response.text}")
        return
    
    print("Configuration created successfully")
    
    # Create serial numbers
    serial_data = {
        "ssccSerialNumbers": ["SSCC001"],
        "caseSerialNumbers": ["CASE001", "CASE002"],
        "innerCaseSerialNumbers": ["INNER001", "INNER002", "INNER003", "INNER004", "INNER005", "INNER006"],
        "itemSerialNumbers": [f"ITEM{i+1:03d}" for i in range(24)]
    }
    
    print(f"Sending serial numbers:")
    print(f"  SSCCs: {len(serial_data['ssccSerialNumbers'])}")
    print(f"  Cases: {len(serial_data['caseSerialNumbers'])}")
    print(f"  Inner Cases: {len(serial_data['innerCaseSerialNumbers'])}")
    print(f"  Items: {len(serial_data['itemSerialNumbers'])}")
    
    serial_response = session.post(f"{BACKEND_URL}/projects/{project_id}/serial-numbers", json=serial_data)
    
    print(f"\nSerial numbers response status: {serial_response.status_code}")
    print(f"Response headers: {dict(serial_response.headers)}")
    
    if serial_response.status_code == 200:
        response_data = serial_response.json()
        print(f"\nResponse data keys: {list(response_data.keys())}")
        print(f"Response data: {json.dumps(response_data, indent=2)}")
        
        # Check actual counts in response
        sscc_count = len(response_data.get("sscc_serial_numbers", []))
        case_count = len(response_data.get("case_serial_numbers", []))
        inner_case_count = len(response_data.get("inner_case_serial_numbers", []))
        item_count = len(response_data.get("item_serial_numbers", []))
        
        print(f"\nActual counts in response:")
        print(f"  SSCCs: {sscc_count}")
        print(f"  Cases: {case_count}")
        print(f"  Inner Cases: {inner_case_count}")
        print(f"  Items: {item_count}")
        
    else:
        print(f"Error response: {serial_response.text}")

if __name__ == "__main__":
    debug_serial_number_response()