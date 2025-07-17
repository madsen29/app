#!/usr/bin/env python3
"""
Debug EPCIS XML Generation to understand the structure
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

BACKEND_URL = "https://c8e3fe45-251a-4359-a250-c028fb05fe98.preview.emergentagent.com/api"

def debug_epcis_xml():
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
    
    # Create configuration
    config_response = session.post(
        f"{BACKEND_URL}/configuration",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if config_response.status_code != 200:
        print(f"Failed to create configuration: {config_response.status_code}")
        return
    
    config_id = config_response.json()["id"]
    print(f"Created configuration: {config_id}")
    
    # Create serial numbers
    serial_data = {
        "configuration_id": config_id,
        "sscc_serial_numbers": ["1001"],
        "case_serial_numbers": ["C001", "C002"],
        "inner_case_serial_numbers": [],
        "item_serial_numbers": ["I001", "I002", "I003", "I004", "I005", "I006"]
    }
    
    serial_response = session.post(
        f"{BACKEND_URL}/serial-numbers",
        json=serial_data,
        headers={"Content-Type": "application/json"}
    )
    
    if serial_response.status_code != 200:
        print(f"Failed to create serial numbers: {serial_response.status_code}")
        return
    
    print("Created serial numbers successfully")
    
    # Generate EPCIS XML
    epcis_data = {
        "configuration_id": config_id,
        "read_point": "urn:epc:id:sgln:1234567.00000.0",
        "biz_location": "urn:epc:id:sgln:1234567.00001.0"
    }
    
    epcis_response = session.post(
        f"{BACKEND_URL}/generate-epcis",
        json=epcis_data,
        headers={"Content-Type": "application/json"}
    )
    
    if epcis_response.status_code != 200:
        print(f"Failed to generate EPCIS: {epcis_response.status_code}")
        return
    
    xml_content = epcis_response.text
    print("\n" + "="*80)
    print("GENERATED EPCIS XML:")
    print("="*80)
    print(xml_content)
    
    # Parse and analyze structure
    try:
        root = ET.fromstring(xml_content)
        
        print("\n" + "="*80)
        print("XML STRUCTURE ANALYSIS:")
        print("="*80)
        
        # Find EventList
        event_list = None
        for elem in root.iter():
            if elem.tag.endswith("EventList"):
                event_list = elem
                break
        
        if event_list is not None:
            events = list(event_list)
            print(f"Total events: {len(events)}")
            
            for i, event in enumerate(events):
                event_type = event.tag.split('}')[-1] if '}' in event.tag else event.tag
                print(f"Event {i+1}: {event_type}")
                
                # Check for bizStep
                for child in event:
                    if child.tag.endswith("bizStep"):
                        print(f"  bizStep: {child.text}")
                        break
        
        # Check for business entity identifiers
        print(f"\nBusiness Entity Identifiers in XML:")
        business_identifiers = [
            "0345802000014", "0345802000014.001",
            "0567890000021", "0567890000021.001", 
            "0999888000028", "0999888000028.001"
        ]
        
        for identifier in business_identifiers:
            if identifier in xml_content:
                print(f"  ✓ Found: {identifier}")
            else:
                print(f"  ✗ Missing: {identifier}")
                
    except ET.ParseError as e:
        print(f"XML parsing error: {str(e)}")

if __name__ == "__main__":
    debug_epcis_xml()