#!/usr/bin/env python3
"""
Final comprehensive test with the exact configuration from the review request:
- Company Prefix: 1234567
- Product Code: 000000
- Case Product Code: 000000
- Inner Case Product Code: 000001
- Package NDC: 45802-046-85
- Item Indicator: 1
- Case Indicator: 2
- Inner Case Indicator: 4
- Test with 1 SSCC, 2 Cases, 3 Inner Cases per Case, 8 Items per Inner Case (48 total items)
"""

import requests
import json
import xml.etree.ElementTree as ET

BACKEND_URL = "https://443af6fc-0d8a-42dd-a86d-aab66f8c129f.preview.emergentagent.com/api"

def test_review_request_configuration():
    """Test with exact configuration from review request"""
    
    # Exact configuration from review request
    config = {
        "items_per_case": 8,  # This becomes items_per_inner_case when inner cases are used
        "cases_per_sscc": 2,
        "number_of_sscc": 1,
        "use_inner_cases": True,
        "inner_cases_per_case": 3,
        "items_per_inner_case": 8,
        "company_prefix": "1234567",
        "item_product_code": "000000",
        "case_product_code": "000000",
        "inner_case_product_code": "000001",
        "package_ndc": "45802-046-85",
        "sscc_indicator_digit": "3",
        "case_indicator_digit": "2",
        "inner_case_indicator_digit": "4",
        "item_indicator_digit": "1"
    }
    
    print("=" * 80)
    print("REVIEW REQUEST CONFIGURATION TEST")
    print("=" * 80)
    print("Configuration:")
    print(f"  Company Prefix: {config['company_prefix']}")
    print(f"  Package NDC: {config['package_ndc']}")
    print(f"  Hierarchy: 1 SSCC → 2 Cases → 3 Inner Cases per Case → 8 Items per Inner Case")
    print(f"  Total Items: {1 * 2 * 3 * 8} = 48 items")
    print(f"  Indicator Digits: SSCC={config['sscc_indicator_digit']}, Case={config['case_indicator_digit']}, Inner Case={config['inner_case_indicator_digit']}, Item={config['item_indicator_digit']}")
    print("=" * 80)
    
    try:
        # 1. Create configuration
        print("1. Creating configuration...")
        config_response = requests.post(f"{BACKEND_URL}/configuration", json=config)
        if config_response.status_code != 200:
            print(f"❌ Configuration creation failed: {config_response.status_code} - {config_response.text}")
            return False
        
        config_data = config_response.json()
        config_id = config_data["id"]
        print(f"✅ Configuration created with ID: {config_id}")
        
        # Verify package_ndc field
        if config_data.get("package_ndc") == "45802-046-85":
            print(f"✅ Package NDC field stored correctly: {config_data['package_ndc']}")
        else:
            print(f"❌ Package NDC field incorrect: expected '45802-046-85', got '{config_data.get('package_ndc')}'")
            return False
        
        # 2. Create serial numbers
        print("\n2. Creating serial numbers...")
        serials = {
            "configuration_id": config_id,
            "sscc_serial_numbers": ["SSCC001"],
            "case_serial_numbers": ["CASE001", "CASE002"],  # 2 cases
            "inner_case_serial_numbers": [f"INNER{i:03d}" for i in range(1, 7)],  # 6 inner cases (3 per case × 2 cases)
            "item_serial_numbers": [f"ITEM{i:03d}" for i in range(1, 49)]  # 48 items (8 per inner case × 6 inner cases)
        }
        
        serial_response = requests.post(f"{BACKEND_URL}/serial-numbers", json=serials)
        if serial_response.status_code != 200:
            print(f"❌ Serial numbers creation failed: {serial_response.status_code} - {serial_response.text}")
            return False
        
        print(f"✅ Serial numbers created: 1 SSCC, 2 Cases, 6 Inner Cases, 48 Items")
        
        # 3. Generate EPCIS XML
        print("\n3. Generating EPCIS XML...")
        epcis_request = {"configuration_id": config_id}
        epcis_response = requests.post(f"{BACKEND_URL}/generate-epcis", json=epcis_request)
        
        if epcis_response.status_code != 200:
            print(f"❌ EPCIS generation failed: {epcis_response.status_code} - {epcis_response.text}")
            return False
        
        xml_content = epcis_response.text
        print(f"✅ EPCIS XML generated ({len(xml_content)} characters)")
        
        # 4. Validate XML structure
        print("\n4. Validating XML structure...")
        root = ET.fromstring(xml_content)
        
        # Check EPCISMasterData is in extension
        epcis_header = None
        for child in root:
            if child.tag.endswith("EPCISHeader"):
                epcis_header = child
                break
        
        extension_found = False
        epcis_master_data = None
        
        if epcis_header:
            for child in epcis_header:
                if child.tag.endswith("extension"):
                    extension_found = True
                    for grandchild in child:
                        if grandchild.tag.endswith("EPCISMasterData"):
                            epcis_master_data = grandchild
                            break
                    break
        
        if extension_found and epcis_master_data is not None:
            print("✅ EPCISMasterData is wrapped inside <extension> element")
        else:
            print("❌ EPCISMasterData is NOT wrapped inside <extension> element")
            return False
        
        # 5. Check EPCClass vocabulary elements
        print("\n5. Validating EPCClass vocabulary elements...")
        
        vocabulary_elements = []
        for elem in root.iter():
            if elem.tag.endswith("VocabularyElement"):
                vocabulary_elements.append(elem)
        
        if len(vocabulary_elements) == 3:
            print(f"✅ Found 3 EPCClass vocabulary elements (expected for 4-level hierarchy)")
        else:
            print(f"❌ Expected 3 EPCClass vocabulary elements, found {len(vocabulary_elements)}")
            return False
        
        # Check each EPCClass has correct indicator digit and package_ndc
        expected_patterns = [
            ("Item", f"urn:epc:idpat:sgtin:1234567.1000000.*"),
            ("Case", f"urn:epc:idpat:sgtin:1234567.2000000.*"),
            ("Inner Case", f"urn:epc:idpat:sgtin:1234567.4000001.*")
        ]
        
        found_patterns = []
        package_ndc_usage = []
        
        for elem in vocabulary_elements:
            elem_id = elem.get("id")
            found_patterns.append(elem_id)
            
            # Check for package_ndc in additionalTradeItemIdentification
            for attr in elem:
                if (attr.tag.endswith("attribute") and 
                    attr.get("id") == "urn:epcglobal:cbv:mda#additionalTradeItemIdentification" and
                    attr.text == "45802-046-85"):
                    package_ndc_usage.append(elem_id)
                    break
        
        print("   EPCClass patterns found:")
        for pattern in found_patterns:
            print(f"     {pattern}")
        
        # Verify expected patterns
        for level, expected_pattern in expected_patterns:
            if expected_pattern in found_patterns:
                print(f"   ✅ {level} EPCClass with correct indicator digit found")
            else:
                print(f"   ❌ {level} EPCClass with pattern {expected_pattern} NOT found")
                return False
        
        # Verify package_ndc usage
        if len(package_ndc_usage) == 3:
            print(f"✅ package_ndc (45802-046-85) used for additionalTradeItemIdentification in all 3 EPCClasses")
        else:
            print(f"❌ package_ndc found in {len(package_ndc_usage)} EPCClasses, expected 3")
            return False
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - REVIEW REQUEST REQUIREMENTS VERIFIED")
        print("=" * 80)
        print("Verified:")
        print("✓ Package NDC field properly stored and retrieved")
        print("✓ EPCISMasterData wrapped inside <extension> element")
        print("✓ 3 EPCClass vocabulary elements for 4-level hierarchy")
        print("✓ Each EPCClass uses correct indicator digit")
        print("✓ package_ndc used for additionalTradeItemIdentification in all EPCClasses")
        print("✓ Configuration: 1 SSCC → 2 Cases → 6 Inner Cases → 48 Items")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_review_request_configuration()
    exit(0 if success else 1)