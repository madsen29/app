#!/usr/bin/env python3
"""
XML Structure Verification Test for Case Commissioning Event ILMD Extension
Verifies the exact XML structure matches the expected format from the review request.
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys

# Get backend URL from environment
BACKEND_URL = "https://443af6fc-0d8a-42dd-a86d-aab66f8c129f.preview.emergentagent.com/api"

def create_test_data_and_generate_xml():
    """Create test configuration and generate EPCIS XML"""
    session = requests.Session()
    
    # Step 1: Create configuration
    config_data = {
        "items_per_case": 10,
        "cases_per_sscc": 5,
        "number_of_sscc": 1,
        "company_prefix": "1234567",
        "item_product_code": "000000",
        "case_product_code": "000000",
        "lot_number": "4JT0482",
        "expiration_date": "2026-08-31",
        "sscc_indicator_digit": "3",
        "case_indicator_digit": "2",
        "item_indicator_digit": "1"
    }
    
    config_response = session.post(f"{BACKEND_URL}/configuration", json=config_data)
    if config_response.status_code != 200:
        print(f"❌ Configuration creation failed: {config_response.status_code}")
        return None
    
    config_id = config_response.json()["id"]
    print(f"✅ Configuration created: {config_id}")
    
    # Step 2: Create serial numbers
    serial_data = {
        "configuration_id": config_id,
        "sscc_serial_numbers": ["SSCC001"],
        "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],
        "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(50)]
    }
    
    serial_response = session.post(f"{BACKEND_URL}/serial-numbers", json=serial_data)
    if serial_response.status_code != 200:
        print(f"❌ Serial numbers creation failed: {serial_response.status_code}")
        return None
    
    print("✅ Serial numbers created")
    
    # Step 3: Generate EPCIS XML
    epcis_data = {
        "configuration_id": config_id,
        "read_point": "urn:epc:id:sgln:1234567.00000.0",
        "biz_location": "urn:epc:id:sgln:1234567.00001.0"
    }
    
    epcis_response = session.post(f"{BACKEND_URL}/generate-epcis", json=epcis_data)
    if epcis_response.status_code != 200:
        print(f"❌ EPCIS generation failed: {epcis_response.status_code}")
        return None
    
    print("✅ EPCIS XML generated")
    return epcis_response.text

def extract_case_commissioning_event_xml(xml_content):
    """Extract the Case commissioning event from the XML"""
    try:
        root = ET.fromstring(xml_content)
        
        # Find Case commissioning event
        for event in root.iter():
            if event.tag.endswith("ObjectEvent"):
                # Check if this event contains case EPCs
                epc_list = None
                for child in event:
                    if child.tag.endswith("epcList"):
                        epc_list = child
                        break
                
                if epc_list is not None:
                    for epc_elem in epc_list:
                        if epc_elem.tag.endswith("epc"):
                            epc = epc_elem.text
                            # Case EPCs have format: urn:epc:id:sgtin:1234567.2000000.CASExxx
                            if epc and "urn:epc:id:sgtin:1234567.2000000." in epc and "CASE" in epc:
                                return event
        return None
    except Exception as e:
        print(f"❌ Error extracting Case commissioning event: {str(e)}")
        return None

def verify_xml_structure(case_event):
    """Verify the XML structure matches the expected format"""
    if case_event is None:
        print("❌ No Case commissioning event found")
        return False
    
    print("\n" + "="*60)
    print("CASE COMMISSIONING EVENT XML STRUCTURE VERIFICATION")
    print("="*60)
    
    # Check basic structure
    required_elements = {
        "eventTime": None,
        "eventTimeZoneOffset": None,
        "epcList": None,
        "action": "ADD",
        "bizStep": "urn:epcglobal:cbv:bizstep:commissioning",
        "disposition": "urn:epcglobal:cbv:disp:active",
        "readPoint": None,
        "bizLocation": None,
        "extension": None
    }
    
    found_elements = {}
    
    for child in case_event:
        tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag_name in required_elements:
            found_elements[tag_name] = child
            
            if required_elements[tag_name] is not None:
                if child.text != required_elements[tag_name]:
                    print(f"❌ {tag_name}: Expected '{required_elements[tag_name]}', got '{child.text}'")
                    return False
                else:
                    print(f"✅ {tag_name}: {child.text}")
            else:
                print(f"✅ {tag_name}: Present")
    
    # Check missing elements
    missing = [elem for elem in required_elements if elem not in found_elements]
    if missing:
        print(f"❌ Missing elements: {', '.join(missing)}")
        return False
    
    # Verify bizLocation structure
    biz_location = found_elements.get("bizLocation")
    if biz_location is not None:
        id_elem = None
        for child in biz_location:
            if child.tag.endswith("id"):
                id_elem = child
                break
        
        if id_elem is None:
            print("❌ bizLocation missing id element")
            return False
        
        if id_elem.text != "urn:epc:id:sgln:1234567.00001.0":
            print(f"❌ bizLocation/id: Expected 'urn:epc:id:sgln:1234567.00001.0', got '{id_elem.text}'")
            return False
        
        print(f"✅ bizLocation/id: {id_elem.text}")
    
    # Verify ILMD extension structure
    extension = found_elements.get("extension")
    if extension is not None:
        ilmd = None
        for child in extension:
            if child.tag.endswith("ilmd"):
                ilmd = child
                break
        
        if ilmd is None:
            print("❌ extension missing ilmd element")
            return False
        
        print("✅ extension/ilmd: Present")
        
        # Check ILMD contents
        lot_number = None
        expiration_date = None
        
        for child in ilmd:
            if child.tag.endswith("lotNumber"):
                lot_number = child
            elif child.tag.endswith("itemExpirationDate"):
                expiration_date = child
        
        if lot_number is None:
            print("❌ ilmd missing lotNumber element")
            return False
        
        if expiration_date is None:
            print("❌ ilmd missing itemExpirationDate element")
            return False
        
        if lot_number.text != "4JT0482":
            print(f"❌ lotNumber: Expected '4JT0482', got '{lot_number.text}'")
            return False
        
        if expiration_date.text != "2026-08-31":
            print(f"❌ itemExpirationDate: Expected '2026-08-31', got '{expiration_date.text}'")
            return False
        
        print(f"✅ cbvmda:lotNumber: {lot_number.text}")
        print(f"✅ cbvmda:itemExpirationDate: {expiration_date.text}")
    
    return True

def print_formatted_xml(case_event):
    """Print the formatted XML structure"""
    if case_event is None:
        return
    
    print("\n" + "="*60)
    print("ACTUAL CASE COMMISSIONING EVENT XML STRUCTURE")
    print("="*60)
    
    # Create a clean representation
    ET.indent(case_event, space="    ")
    xml_str = ET.tostring(case_event, encoding="unicode")
    
    # Clean up namespace prefixes for readability
    xml_str = xml_str.replace('{urn:epcglobal:epcis:xsd:1}', '')
    xml_str = xml_str.replace('{urn:epcglobal:cbv:mda}', 'cbvmda:')
    
    print(xml_str)

def main():
    print("XML STRUCTURE VERIFICATION FOR CASE COMMISSIONING EVENT ILMD EXTENSION")
    print("="*80)
    
    # Generate test XML
    xml_content = create_test_data_and_generate_xml()
    if not xml_content:
        print("❌ Failed to generate test XML")
        return False
    
    # Extract Case commissioning event
    case_event = extract_case_commissioning_event_xml(xml_content)
    
    # Verify structure
    structure_valid = verify_xml_structure(case_event)
    
    # Print formatted XML
    print_formatted_xml(case_event)
    
    print("\n" + "="*60)
    print("VERIFICATION RESULT")
    print("="*60)
    
    if structure_valid:
        print("🎉 CASE COMMISSIONING EVENT XML STRUCTURE IS CORRECT!")
        print("✅ Contains proper ILMD extension with lot number and expiration date")
        print("✅ Matches expected XML format from review request")
        return True
    else:
        print("❌ CASE COMMISSIONING EVENT XML STRUCTURE HAS ISSUES!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)