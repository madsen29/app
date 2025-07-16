#!/usr/bin/env python3
"""
Comprehensive EPCClass XML Structure Validation Test
Validates that the EPCISMasterData structure matches the GS1 standard
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime

BACKEND_URL = "https://443af6fc-0d8a-42dd-a86d-aab66f8c129f.preview.emergentagent.com/api"

def test_epcclass_xml_structure():
    """Test EPCClass XML structure against GS1 standard"""
    
    # Create configuration with EPCClass data
    config_data = {
        "items_per_case": 10,
        "cases_per_sscc": 5,
        "number_of_sscc": 1,
        "company_prefix": "1234567",
        "item_product_code": "000000",
        "case_product_code": "000001",
        "sscc_indicator_digit": "3",
        "case_indicator_digit": "2",
        "item_indicator_digit": "1",
        "product_ndc": "45802-046-85",
        "regulated_product_name": "RX ECONAZOLE NITRATE 1% CRM 85G",
        "manufacturer_name": "Padagis LLC",
        "dosage_form_type": "CREAM",
        "strength_description": "10 mg/g",
        "net_content_description": "85GM     Wgt"
    }
    
    session = requests.Session()
    
    # Create configuration
    config_response = session.post(f"{BACKEND_URL}/configuration", json=config_data)
    if config_response.status_code != 200:
        print(f"❌ Failed to create configuration: {config_response.status_code}")
        return False
    
    config_id = config_response.json()["id"]
    
    # Create serial numbers
    serial_data = {
        "configuration_id": config_id,
        "sscc_serial_numbers": ["SSCC001"],
        "case_serial_numbers": [f"CASE{i+1:03d}" for i in range(5)],
        "item_serial_numbers": [f"ITEM{i+1:03d}" for i in range(50)]
    }
    
    serial_response = session.post(f"{BACKEND_URL}/serial-numbers", json=serial_data)
    if serial_response.status_code != 200:
        print(f"❌ Failed to create serial numbers: {serial_response.status_code}")
        return False
    
    # Generate EPCIS XML
    epcis_data = {
        "configuration_id": config_id,
        "read_point": "urn:epc:id:sgln:1234567.00000.0",
        "biz_location": "urn:epc:id:sgln:1234567.00001.0"
    }
    
    epcis_response = session.post(f"{BACKEND_URL}/generate-epcis", json=epcis_data)
    if epcis_response.status_code != 200:
        print(f"❌ Failed to generate EPCIS XML: {epcis_response.status_code}")
        return False
    
    xml_content = epcis_response.text
    
    # Parse and validate XML structure
    try:
        root = ET.fromstring(xml_content)
        
        print("🔍 Validating EPCClass XML Structure against GS1 Standard...")
        print("=" * 70)
        
        # 1. Validate root element
        if not root.tag.endswith("EPCISDocument"):
            print(f"❌ Invalid root element: {root.tag}")
            return False
        print("✅ Root element: EPCISDocument")
        
        # 2. Validate EPCIS namespace
        if not root.tag.startswith("{urn:epcglobal:epcis:xsd:1}"):
            print(f"❌ Invalid EPCIS namespace: {root.tag}")
            return False
        print("✅ EPCIS namespace: urn:epcglobal:epcis:xsd:1")
        
        # 3. Validate schema version
        schema_version = root.get("schemaVersion")
        if schema_version != "1.2":
            print(f"❌ Invalid schema version: {schema_version}")
            return False
        print(f"✅ Schema version: {schema_version}")
        
        # 4. Find EPCISHeader
        epcis_header = None
        for child in root:
            if child.tag.endswith("EPCISHeader"):
                epcis_header = child
                break
        
        if epcis_header is None:
            print("❌ Missing EPCISHeader")
            return False
        print("✅ EPCISHeader found")
        
        # 5. Find EPCISMasterData
        epcis_master_data = None
        for child in epcis_header:
            if child.tag.endswith("EPCISMasterData"):
                epcis_master_data = child
                break
        
        if epcis_master_data is None:
            print("❌ Missing EPCISMasterData")
            return False
        print("✅ EPCISMasterData found")
        
        # 6. Find VocabularyList
        vocabulary_list = None
        for child in epcis_master_data:
            if child.tag.endswith("VocabularyList"):
                vocabulary_list = child
                break
        
        if vocabulary_list is None:
            print("❌ Missing VocabularyList")
            return False
        print("✅ VocabularyList found")
        
        # 7. Find EPCClass Vocabulary
        epcclass_vocabulary = None
        for child in vocabulary_list:
            if child.tag.endswith("Vocabulary"):
                vocab_type = child.get("type")
                if vocab_type == "urn:epcglobal:epcis:vtype:EPCClass":
                    epcclass_vocabulary = child
                    break
        
        if epcclass_vocabulary is None:
            print("❌ Missing EPCClass Vocabulary")
            return False
        print("✅ EPCClass Vocabulary found")
        print(f"   Type: {epcclass_vocabulary.get('type')}")
        
        # 8. Find VocabularyElementList
        vocabulary_element_list = None
        for child in epcclass_vocabulary:
            if child.tag.endswith("VocabularyElementList"):
                vocabulary_element_list = child
                break
        
        if vocabulary_element_list is None:
            print("❌ Missing VocabularyElementList")
            return False
        print("✅ VocabularyElementList found")
        
        # 9. Find VocabularyElement
        vocabulary_element = None
        for child in vocabulary_element_list:
            if child.tag.endswith("VocabularyElement"):
                vocabulary_element = child
                break
        
        if vocabulary_element is None:
            print("❌ Missing VocabularyElement")
            return False
        
        element_id = vocabulary_element.get("id")
        print(f"✅ VocabularyElement found")
        print(f"   ID: {element_id}")
        
        # 10. Validate EPCClass attributes
        expected_attributes = {
            "urn:epcglobal:cbv:mda#additionalTradeItemIdentification": "45802-046-85",
            "urn:epcglobal:cbv:mda#additionalTradeItemIdentificationTypeCode": "FDA_NDC_11",
            "urn:epcglobal:cbv:mda#regulatedProductName": "RX ECONAZOLE NITRATE 1% CRM 85G",
            "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName": "Padagis LLC",
            "urn:epcglobal:cbv:mda#dosageFormType": "CREAM",
            "urn:epcglobal:cbv:mda#strengthDescription": "10 mg/g",
            "urn:epcglobal:cbv:mda#netContentDescription": "85GM     Wgt"
        }
        
        found_attributes = {}
        for child in vocabulary_element:
            if child.tag.endswith("attribute"):
                attr_id = child.get("id")
                attr_value = child.text
                found_attributes[attr_id] = attr_value
        
        print(f"✅ Found {len(found_attributes)} EPCClass attributes:")
        
        all_attributes_valid = True
        for expected_id, expected_value in expected_attributes.items():
            if expected_id in found_attributes:
                if found_attributes[expected_id] == expected_value:
                    print(f"   ✅ {expected_id.split('#')[1]}: {expected_value}")
                else:
                    print(f"   ❌ {expected_id.split('#')[1]}: expected '{expected_value}', got '{found_attributes[expected_id]}'")
                    all_attributes_valid = False
            else:
                print(f"   ❌ Missing attribute: {expected_id.split('#')[1]}")
                all_attributes_valid = False
        
        if not all_attributes_valid:
            return False
        
        # 11. Validate EPCISBody exists
        epcis_body = None
        for child in root:
            if child.tag.endswith("EPCISBody"):
                epcis_body = child
                break
        
        if epcis_body is None:
            print("❌ Missing EPCISBody")
            return False
        print("✅ EPCISBody found")
        
        # 12. Validate EventList exists
        event_list = None
        for child in epcis_body:
            if child.tag.endswith("EventList"):
                event_list = child
                break
        
        if event_list is None:
            print("❌ Missing EventList")
            return False
        
        event_count = len(list(event_list))
        print(f"✅ EventList found with {event_count} events")
        
        print("=" * 70)
        print("🎉 EPCClass XML Structure Validation: PASSED")
        print("✅ All GS1 standard requirements met:")
        print("   • Proper EPCIS 1.2 document structure")
        print("   • EPCISMasterData with VocabularyList")
        print("   • EPCClass vocabulary with correct type")
        print("   • All required EPCClass attributes present")
        print("   • Event data properly included")
        
        return True
        
    except ET.ParseError as e:
        print(f"❌ XML parsing error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_epcclass_xml_structure()
    if success:
        print("\n🎯 CONCLUSION: EPCClass integration is working correctly!")
        print("   The EPCIS XML matches GS1 standard requirements.")
    else:
        print("\n❌ CONCLUSION: EPCClass integration has issues.")