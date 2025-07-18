#!/usr/bin/env python3
"""
Debug EPCIS Generation Test
Focused test to understand the EPCIS XML structure issue
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com/api"

def debug_epcis_generation():
    """Debug the EPCIS generation to understand the XML structure"""
    
    # First create a simple configuration
    config_data = {
        "items_per_case": 10,
        "cases_per_sscc": 5,
        "number_of_sscc": 1,  # Simplified to 1 SSCC for easier debugging
        "company_prefix": "1234567",
        "item_product_code": "000000",
        "case_product_code": "111111",
        "sscc_indicator_digit": "0",
        "case_indicator_digit": "0",
        "item_indicator_digit": "0"
    }
    
    print("Creating configuration...")
    response = requests.post(f"{BACKEND_URL}/configuration", json=config_data)
    if response.status_code != 200:
        print(f"Failed to create configuration: {response.status_code} - {response.text}")
        return
    
    config = response.json()
    config_id = config["id"]
    print(f"Configuration created with ID: {config_id}")
    
    # Create serial numbers for 1 SSCC, 5 cases, 50 items
    serial_data = {
        "configuration_id": config_id,
        "sscc_serial_numbers": ["SSCC001"],
        "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],
        "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(50)]
    }
    
    print("Creating serial numbers...")
    response = requests.post(f"{BACKEND_URL}/serial-numbers", json=serial_data)
    if response.status_code != 200:
        print(f"Failed to create serial numbers: {response.status_code} - {response.text}")
        return
    
    print("Serial numbers created successfully")
    
    # Generate EPCIS XML
    epcis_data = {
        "configuration_id": config_id,
        "read_point": "urn:epc:id:sgln:1234567.00000.0",
        "biz_location": "urn:epc:id:sgln:1234567.00001.0"
    }
    
    print("Generating EPCIS XML...")
    response = requests.post(f"{BACKEND_URL}/generate-epcis", json=epcis_data)
    if response.status_code != 200:
        print(f"Failed to generate EPCIS: {response.status_code} - {response.text}")
        return
    
    xml_content = response.text
    print(f"EPCIS XML generated successfully ({len(xml_content)} characters)")
    
    # Parse and analyze the XML
    try:
        root = ET.fromstring(xml_content)
        print(f"\nRoot element: {root.tag}")
        print(f"Schema version: {root.get('schemaVersion')}")
        
        # Find EventList
        event_list = None
        for elem in root.iter():
            if elem.tag.endswith("EventList"):
                event_list = elem
                break
        
        if event_list is None:
            print("No EventList found!")
            return
        
        # Count events
        object_events = []
        aggregation_events = []
        
        for child in event_list:
            if child.tag.endswith("ObjectEvent"):
                object_events.append(child)
            elif child.tag.endswith("AggregationEvent"):
                aggregation_events.append(child)
        
        print(f"\nEvent Analysis:")
        print(f"ObjectEvents (commissioning): {len(object_events)}")
        print(f"AggregationEvents: {len(aggregation_events)}")
        
        # Analyze ObjectEvents
        print(f"\nObjectEvent Details:")
        for i, event in enumerate(object_events):
            epc_list = None
            bizstep = None
            action = None
            
            for child in event:
                if child.tag.endswith("epcList"):
                    epc_list = child
                elif child.tag.endswith("bizStep"):
                    bizstep = child
                elif child.tag.endswith("action"):
                    action = child
            
            epc_count = len(list(epc_list)) if epc_list is not None else 0
            bizstep_text = bizstep.text if bizstep is not None else "Unknown"
            action_text = action.text if action is not None else "Unknown"
            
            print(f"  Event {i+1}: {epc_count} EPCs, Action: {action_text}, BizStep: {bizstep_text}")
            
            # Show first few EPCs to understand the pattern
            if epc_list is not None and epc_count > 0:
                epcs = [epc.text for epc in epc_list if epc.tag.endswith("epc")]
                print(f"    Sample EPCs: {epcs[:3]}{'...' if len(epcs) > 3 else ''}")
        
        # Analyze AggregationEvents
        print(f"\nAggregationEvent Details:")
        for i, event in enumerate(aggregation_events):
            parent_id = None
            child_epcs = None
            action = None
            
            for child in event:
                if child.tag.endswith("parentID"):
                    parent_id = child
                elif child.tag.endswith("childEPCs"):
                    child_epcs = child
                elif child.tag.endswith("action"):
                    action = child
            
            parent_text = parent_id.text if parent_id is not None else "Unknown"
            child_count = len(list(child_epcs)) if child_epcs is not None else 0
            action_text = action.text if action is not None else "Unknown"
            
            print(f"  Event {i+1}: Parent: {parent_text[:50]}{'...' if len(parent_text) > 50 else ''}")
            print(f"           {child_count} children, Action: {action_text}")
        
        # Save XML for inspection
        with open("/app/debug_epcis.xml", "w") as f:
            f.write(xml_content)
        print(f"\nXML saved to /app/debug_epcis.xml for inspection")
        
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        print("First 1000 characters of XML:")
        print(xml_content[:1000])

if __name__ == "__main__":
    debug_epcis_generation()