#!/usr/bin/env python3
"""
Debug Configuration Data - Check what's actually stored in the configuration
"""

import requests
import json

# Get backend URL from environment
BACKEND_URL = "https://443af6fc-0d8a-42dd-a86d-aab66f8c129f.preview.emergentagent.com/api"

def debug_configuration():
    session = requests.Session()
    
    # Create test configuration
    test_data = {
        "items_per_case": 3,
        "cases_per_sscc": 2,
        "number_of_sscc": 1,
        "use_inner_cases": False,
        "company_prefix": "1234567",
        "item_product_code": "000000",
        "case_product_code": "000001",
        "lot_number": "LOT123",
        "expiration_date": "2025-12-31",
        "sscc_indicator_digit": "3",
        "case_indicator_digit": "2",
        "item_indicator_digit": "1",
        "sender_company_prefix": "0345802",
        "sender_gln": "0345802000014",
        "sender_sgln": "0345802000014.001",
        "receiver_company_prefix": "0567890",
        "receiver_gln": "0567890000021",
        "receiver_sgln": "0567890000021.001",
        "shipper_company_prefix": "0999888",
        "shipper_gln": "0999888000028",
        "shipper_sgln": "0999888000028.001",
        "shipper_same_as_sender": False,
        "package_ndc": "45802-046-85",
        "regulated_product_name": "Test Product",
        "manufacturer_name": "Test Manufacturer"
    }
    
    print("SENDING CONFIGURATION DATA:")
    print("=" * 40)
    print(json.dumps(test_data, indent=2))
    
    # Create configuration
    response = session.post(f"{BACKEND_URL}/configuration", json=test_data, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        config_data = response.json()
        print("\nRECEIVED CONFIGURATION DATA:")
        print("=" * 40)
        print(json.dumps(config_data, indent=2))
        
        # Check specific GLN/SGLN fields
        print("\nGLN/SGLN FIELDS CHECK:")
        print("=" * 40)
        gln_sgln_fields = [
            "sender_gln", "sender_sgln",
            "receiver_gln", "receiver_sgln", 
            "shipper_gln", "shipper_sgln"
        ]
        
        for field in gln_sgln_fields:
            value = config_data.get(field, "NOT_FOUND")
            print(f"{field}: '{value}' (empty: {value == ''})")
        
        return config_data["id"]
    else:
        print(f"Configuration creation failed: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    debug_configuration()