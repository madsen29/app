#!/usr/bin/env python3
"""
Detailed XML Structure Validation for ILMD Extensions
Validates that the EPCIS XML contains the exact ILMD structure requested
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime

BACKEND_URL = "https://b592395b-b7d6-4a00-b6d1-3e8882cb2379.preview.emergentagent.com/api"

def test_xml_structure():
    """Test the exact XML structure for ILMD extensions"""
    session = requests.Session()
    
    # Create configuration with test data
    config_data = {
        "items_per_case": 10,
        "cases_per_sscc": 5,
        "number_of_sscc": 1,
        "company_prefix": "1234567",
        "item_product_code": "000000",
        "case_product_code": "000001",
        "lot_number": "4JT0482",
        "expiration_date": "2026-08-31",
        "sscc_indicator_digit": "3",
        "case_indicator_digit": "2",
        "item_indicator_digit": "1"
    }
    
    config_response = session.post(f"{BACKEND_URL}/configuration", json=config_data)
    config_id = config_response.json()["id"]
    
    # Create serial numbers
    serial_data = {
        "configuration_id": config_id,
        "sscc_serial_numbers": ["SSCC001"],
        "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],
        "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(50)]
    }
    
    session.post(f"{BACKEND_URL}/serial-numbers", json=serial_data)
    
    # Generate EPCIS XML
    epcis_data = {
        "configuration_id": config_id,
        "read_point": "urn:epc:id:sgln:1234567.00000.0",
        "biz_location": "urn:epc:id:sgln:1234567.00001.0"
    }
    
    epcis_response = session.post(f"{BACKEND_URL}/generate-epcis", json=epcis_data)
    xml_content = epcis_response.text
    
    print("=" * 80)
    print("DETAILED XML STRUCTURE VALIDATION")
    print("=" * 80)
    
    # Parse XML and find ILMD extensions
    root = ET.fromstring(xml_content)
    
    # Find ObjectEvents with ILMD extensions
    object_events_with_ilmd = []
    for event in root.iter():
        if event.tag.endswith("ObjectEvent"):
            for child in event:
                if child.tag.endswith("extension"):
                    for ext_child in child:
                        if ext_child.tag.endswith("ilmd"):
                            object_events_with_ilmd.append((event, child, ext_child))
    
    print(f"Found {len(object_events_with_ilmd)} ObjectEvents with ILMD extensions")
    
    for i, (event, extension, ilmd) in enumerate(object_events_with_ilmd):
        print(f"\nObjectEvent {i+1} ILMD Extension:")
        print("=" * 40)
        
        # Print the extension XML structure
        extension_xml = ET.tostring(extension, encoding='unicode')
        print("XML Structure:")
        print(extension_xml)
        
        # Validate specific elements
        print("\nValidation:")
        
        # Check namespace
        if 'urn:epcglobal:cbv:mda' in extension_xml:
            print("✅ Correct cbvmda namespace (urn:epcglobal:cbv:mda)")
        else:
            print("❌ Missing or incorrect cbvmda namespace")
        
        # Check lot number
        lot_elem = None
        for child in ilmd:
            if child.tag.endswith("lotNumber"):
                lot_elem = child
                break
        
        if lot_elem is not None and lot_elem.text == "4JT0482":
            print("✅ Correct lot number: 4JT0482")
        else:
            print(f"❌ Incorrect lot number: {lot_elem.text if lot_elem else 'Not found'}")
        
        # Check expiration date
        exp_elem = None
        for child in ilmd:
            if child.tag.endswith("itemExpirationDate"):
                exp_elem = child
                break
        
        if exp_elem is not None and exp_elem.text == "2026-08-31":
            print("✅ Correct expiration date: 2026-08-31")
        else:
            print(f"❌ Incorrect expiration date: {exp_elem.text if exp_elem else 'Not found'}")
        
        # Check which event type this is
        epc_list = None
        for child in event:
            if child.tag.endswith("epcList"):
                epc_list = child
                break
        
        if epc_list is not None:
            epcs = [epc.text for epc in epc_list if epc.tag.endswith("epc")]
            if epcs:
                first_epc = epcs[0]
                if "sgtin" in first_epc and "1000000" in first_epc:
                    print(f"✅ Item commissioning event ({len(epcs)} items)")
                elif "sgtin" in first_epc and "2000001" in first_epc:
                    print(f"✅ Case commissioning event ({len(epcs)} cases)")
                elif "sscc" in first_epc:
                    print(f"✅ SSCC commissioning event ({len(epcs)} SSCCs)")
                else:
                    print(f"? Unknown event type: {first_epc}")
    
    print("\n" + "=" * 80)
    print("EXPECTED XML STRUCTURE VERIFICATION")
    print("=" * 80)
    
    expected_structure = '''<extension>
    <ilmd>
        <cbvmda:lotNumber>4JT0482</cbvmda:lotNumber>
        <cbvmda:itemExpirationDate>2026-08-31</cbvmda:itemExpirationDate>
    </ilmd>
</extension>'''
    
    print("Expected structure:")
    print(expected_structure)
    
    # Check if the structure matches expectations
    structure_matches = True
    for event, extension, ilmd in object_events_with_ilmd:
        # Check that extension contains ilmd
        ilmd_found = False
        for child in extension:
            if child.tag.endswith("ilmd"):
                ilmd_found = True
                
                # Check namespace attribute
                if 'cbvmda' not in ET.tostring(child, encoding='unicode'):
                    structure_matches = False
                    print("❌ Missing cbvmda namespace in ILMD")
                
                # Check lot number element
                lot_found = False
                exp_found = False
                for grandchild in child:
                    if grandchild.tag.endswith("lotNumber") and grandchild.text == "4JT0482":
                        lot_found = True
                    elif grandchild.tag.endswith("itemExpirationDate") and grandchild.text == "2026-08-31":
                        exp_found = True
                
                if not lot_found:
                    structure_matches = False
                    print("❌ Lot number element missing or incorrect")
                if not exp_found:
                    structure_matches = False
                    print("❌ Expiration date element missing or incorrect")
        
        if not ilmd_found:
            structure_matches = False
            print("❌ ILMD element not found in extension")
    
    if structure_matches:
        print("✅ XML structure matches expected format")
    else:
        print("❌ XML structure does not match expected format")
    
    return structure_matches

if __name__ == "__main__":
    success = test_xml_structure()
    print(f"\nOverall result: {'✅ PASS' if success else '❌ FAIL'}")