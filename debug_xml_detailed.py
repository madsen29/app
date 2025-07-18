#!/usr/bin/env python3
"""
Debug XML Generation Step by Step
"""

import requests
import json
import xml.etree.ElementTree as ET

# Get backend URL from environment
BACKEND_URL = "https://c8e3fe45-251a-4359-a250-c028fb05fe98.preview.emergentagent.com/api"

def debug_xml_step_by_step():
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
    response = session.post(f"{BACKEND_URL}/configuration", json=test_data, headers={"Content-Type": "application/json"})
    config_id = response.json()["id"]
    
    # Create serial numbers
    serial_data = {
        "configuration_id": config_id,
        "sscc_serial_numbers": ["SSCC001"],
        "case_serial_numbers": ["CASE001", "CASE002"],
        "inner_case_serial_numbers": [],
        "item_serial_numbers": ["ITEM001", "ITEM002", "ITEM003", "ITEM004", "ITEM005", "ITEM006"]
    }
    
    session.post(f"{BACKEND_URL}/serial-numbers", json=serial_data, headers={"Content-Type": "application/json"})
    
    # Generate EPCIS XML
    epcis_data = {
        "configuration_id": config_id,
        "read_point": "urn:epc:id:sgln:1234567.00000.0",
        "biz_location": "urn:epc:id:sgln:1234567.00001.0"
    }
    
    response = session.post(f"{BACKEND_URL}/generate-epcis", json=epcis_data, headers={"Content-Type": "application/json"})
    xml_content = response.text
    
    # Parse XML and analyze structure
    try:
        root = ET.fromstring(xml_content)
        
        print("DETAILED XML STRUCTURE ANALYSIS:")
        print("=" * 50)
        
        # Check EPCISHeader structure
        for elem in root.iter():
            if elem.tag.endswith("EPCISHeader"):
                print("✓ EPCISHeader found")
                for child in elem:
                    if child.tag.endswith("extension"):
                        print("  ✓ extension found")
                        for grandchild in child:
                            if grandchild.tag.endswith("EPCISMasterData"):
                                print("    ✓ EPCISMasterData found")
                                for ggchild in grandchild:
                                    if ggchild.tag.endswith("VocabularyList"):
                                        print("      ✓ VocabularyList found")
                                        vocab_count = 0
                                        for vocab in ggchild:
                                            if vocab.tag.endswith("Vocabulary"):
                                                vocab_count += 1
                                                vocab_type = vocab.get("type")
                                                print(f"        ✓ Vocabulary {vocab_count}: {vocab_type}")
                                                
                                                # Count elements in each vocabulary
                                                for vocab_child in vocab:
                                                    if vocab_child.tag.endswith("VocabularyElementList"):
                                                        element_count = 0
                                                        for elem_child in vocab_child:
                                                            if elem_child.tag.endswith("VocabularyElement"):
                                                                element_count += 1
                                                                elem_id = elem_child.get("id")
                                                                print(f"          - Element {element_count}: {elem_id}")
                                                        print(f"          Total elements: {element_count}")
                                        print(f"      Total vocabularies: {vocab_count}")
        
        # Check EventList structure
        for elem in root.iter():
            if elem.tag.endswith("EventList"):
                print("\n✓ EventList found")
                events = list(elem)
                print(f"  Total events: {len(events)}")
                
                for i, event in enumerate(events):
                    event_type = event.tag.split('}')[-1] if '}' in event.tag else event.tag
                    print(f"  Event {i+1}: {event_type}")
                    
                    # For ObjectEvents, check bizStep
                    if event.tag.endswith("ObjectEvent"):
                        for child in event:
                            if child.tag.endswith("bizStep"):
                                print(f"    bizStep: {child.text}")
                            elif child.tag.endswith("action"):
                                print(f"    action: {child.text}")
                            elif child.tag.endswith("disposition"):
                                print(f"    disposition: {child.text}")
                            elif child.tag.endswith("epcList"):
                                epc_count = len(list(child))
                                print(f"    epcList: {epc_count} EPCs")
                
                # Check last event specifically
                if events:
                    last_event = events[-1]
                    last_event_type = last_event.tag.split('}')[-1] if '}' in last_event.tag else last_event.tag
                    print(f"\n  LAST EVENT: {last_event_type}")
                    
                    if last_event.tag.endswith("ObjectEvent"):
                        for child in last_event:
                            if child.tag.endswith("bizStep"):
                                print(f"    Last event bizStep: {child.text}")
                                if "shipping" in child.text:
                                    print("    ✓ SHIPPING EVENT FOUND!")
                                else:
                                    print("    ❌ NOT A SHIPPING EVENT")
                    else:
                        print("    ❌ LAST EVENT IS NOT AN OBJECTEVENT")
        
        # Check for specific patterns in raw XML
        print(f"\nRAW XML PATTERN CHECKS:")
        print("=" * 30)
        print(f"Contains 'Location' vocabulary: {'urn:epcglobal:epcis:vtype:Location' in xml_content}")
        print(f"Contains shipping bizStep: {'urn:epcglobal:cbv:bizstep:shipping' in xml_content}")
        print(f"Contains sender GLN: {'0345802000014' in xml_content}")
        print(f"Contains receiver GLN: {'0567890000021' in xml_content}")
        print(f"Contains shipper GLN: {'0999888000028' in xml_content}")
        
    except ET.ParseError as e:
        print(f"XML parsing error: {str(e)}")

if __name__ == "__main__":
    debug_xml_step_by_step()