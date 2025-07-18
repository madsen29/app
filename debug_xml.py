#!/usr/bin/env python3
"""
Debug XML generation to check for duplicate attribute issue
"""

import requests
import json

BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

def debug_xml_generation():
    # Use the configuration ID from the previous test
    config_id = "1c2d05e6-c124-4412-97c8-f79cd494cf01"  # From first test scenario
    
    test_data = {
        "configurationId": config_id,
        "readPoint": "urn:epc:id:sgln:1234567.00000.0",
        "bizLocation": "urn:epc:id:sgln:1234567.00001.0"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-epcis",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
        
        if response.status_code == 200:
            xml_content = response.text
            
            # Show first few lines to identify duplicate attribute
            lines = xml_content.split('\n')
            print("\nFirst 5 lines of XML:")
            for i, line in enumerate(lines[:5], 1):
                print(f"Line {i}: {line}")
                
            # Check line 2 specifically (where error occurs)
            if len(lines) > 1:
                line2 = lines[1]
                print(f"\nLine 2 (column 330 area): {line2}")
                print(f"Line 2 length: {len(line2)}")
                if len(line2) > 320:
                    print(f"Around column 330: '{line2[320:340]}'")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Request error: {str(e)}")

if __name__ == "__main__":
    debug_xml_generation()