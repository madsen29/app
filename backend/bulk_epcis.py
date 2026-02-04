"""
Bulk EPCIS Creation Module

Handles JSON upload, hierarchy resolution, validation, and EPCIS generation
for bulk packaging data.
"""

import json
import hashlib
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pydantic import BaseModel, Field
import uuid


# ============================================================
# PYDANTIC MODELS
# ============================================================

class BulkLocation(BaseModel):
    """Location data for sender/receiver"""
    name: str
    street_address_one: str = Field(alias="streetAddressOne")
    city: str
    state: str
    postal_code: str = Field(alias="postalCode")
    country_code: str = Field(alias="countryCode")
    sgln: str
    
    class Config:
        populate_by_name = True


class BulkEPCISRequest(BaseModel):
    """Request model for bulk EPCIS creation"""
    shipping_sscc: str = Field(alias="shippingSSCC")
    sender_location: BulkLocation = Field(alias="senderLocation")
    receiver_location: BulkLocation = Field(alias="receiverLocation")
    
    class Config:
        populate_by_name = True


class BulkEPCISSummary(BaseModel):
    """Summary response for bulk EPCIS generation"""
    total_records_processed: int
    commissioning_events_created: int
    aggregation_events_created: int
    root_epcs_aggregated: int
    max_hierarchy_depth: int
    sender_sgln: str
    receiver_sgln: str
    validation_warnings_count: int
    validation_warnings: List[str]
    generation_status: str
    filename: str
    job_id: str
    # SGTIN parsing stats
    sgtins_successfully_parsed: int = 0
    sgtin_parse_failures: int = 0


class BulkJobAudit(BaseModel):
    """Audit record for bulk EPCIS creation job"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_filename: str
    input_checksum: str
    shipping_sscc: str
    sender_sgln: str
    receiver_sgln: str
    total_records: int
    commissioning_events: int
    aggregation_events: int
    warnings: List[str]
    status: str
    epcis_storage_pointer: Optional[str] = None


# ============================================================
# HIERARCHY CLASSES
# ============================================================

class SGTINParseError(Exception):
    """Exception raised when SGTIN parsing fails"""
    pass


def parse_sgtin(serial_number: str, gs1_prefix: str, product_code: str) -> str:
    """
    Parse serialNumber and construct proper EPC SGTIN.
    
    serialNumber anatomy:
        indicator_digit + gs1Prefix + productCode + check_digit + serial_number
    
    EPC SGTIN construction:
        gs1Prefix . indicator_digit + productCode . serial_number
    
    Args:
        serial_number: Raw serialNumber from JSON
        gs1_prefix: GS1 company prefix
        product_code: Product/item reference code
    
    Returns:
        Properly formatted SGTIN string (without urn:epc:id:sgtin: prefix)
    
    Raises:
        SGTINParseError: If parsing fails
    """
    if not serial_number or len(serial_number) < 2:
        raise SGTINParseError("serialNumber is empty or too short")
    
    if not gs1_prefix:
        raise SGTINParseError("gs1Prefix is required")
    
    if not product_code:
        raise SGTINParseError("productCode is required")
    
    # Extract indicator digit (first character)
    indicator_digit = serial_number[0]
    
    # Calculate expected prefix length: indicator(1) + gs1Prefix + productCode + checkDigit(1)
    prefix_length = 1 + len(gs1_prefix) + len(product_code) + 1
    
    if len(serial_number) <= prefix_length:
        raise SGTINParseError(
            f"serialNumber '{serial_number}' is too short to contain indicator + gs1Prefix + productCode + checkDigit + serial"
        )
    
    # Validate that serialNumber contains the expected gs1Prefix after indicator
    expected_prefix_start = serial_number[1:1 + len(gs1_prefix)]
    if expected_prefix_start != gs1_prefix:
        raise SGTINParseError(
            f"serialNumber does not contain expected gs1Prefix '{gs1_prefix}' at position 1 (found '{expected_prefix_start}')"
        )
    
    # Validate that serialNumber contains the expected productCode after gs1Prefix
    product_code_start = 1 + len(gs1_prefix)
    expected_product_code = serial_number[product_code_start:product_code_start + len(product_code)]
    if expected_product_code != product_code:
        raise SGTINParseError(
            f"serialNumber does not contain expected productCode '{product_code}' at position {product_code_start} (found '{expected_product_code}')"
        )
    
    # Extract serial number (everything after indicator + gs1Prefix + productCode + checkDigit)
    serial_start = prefix_length
    extracted_serial = serial_number[serial_start:]
    
    if not extracted_serial:
        raise SGTINParseError("Extracted serial_number is empty after parsing")
    
    # Construct EPC SGTIN: gs1Prefix.indicatorDigit+productCode.serialNumber
    sgtin = f"{gs1_prefix}.{indicator_digit}{product_code}.{extracted_serial}"
    
    return sgtin


class HierarchyNode:
    """Represents a node in the packaging hierarchy"""
    def __init__(self, record: Dict[str, Any]):
        self.id = record['_id']
        self.type = record.get('type', '')
        self.raw_serial_number = record['serialNumber']  # Keep raw value for reference
        self.gs1_prefix = record.get('gs1Prefix', '')
        self.product_code = record.get('productCode', '')
        self.lot = record['lot']
        self.expiration = record['expiration']
        self.parent_id = record.get('parentPackagingId')
        self.additional_trade_item_id = record.get('additionalTradeItemIdentification', '')
        self.regulated_product_name = record.get('regulatedProductName', '')
        self.manufacturer_name = record.get('manufacturerOfTradeItemPartyName', '')
        self.dosage_form = record.get('dosageFormType', '')
        self.strength = record.get('strengthDescription', '')
        self.children: List['HierarchyNode'] = []
        self.depth = 0
        
        # Parsed SGTIN (set during validation)
        self.sgtin: Optional[str] = None
        self.sgtin_parse_error: Optional[str] = None


class ValidationResult:
    """Stores validation results"""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.is_valid = True
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another ValidationResult into this one"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

def validate_json_structure(data: List[Dict[str, Any]]) -> ValidationResult:
    """Validate JSON structure and required fields"""
    result = ValidationResult()
    
    if not isinstance(data, list):
        result.add_error("JSON must be an array of records")
        return result
    
    if len(data) == 0:
        result.add_error("JSON array is empty")
        return result
    
    required_fields = ['_id', 'serialNumber', 'lot', 'expiration', 'gs1Prefix', 'productCode']
    
    for idx, record in enumerate(data):
        if not isinstance(record, dict):
            result.add_error(f"Record {idx} is not an object")
            continue
        
        for field in required_fields:
            if field not in record or not record[field]:
                result.add_error(f"Record {idx} ({record.get('_id', 'unknown')}): missing required field '{field}'")
    
    return result


def validate_and_parse_sgtins(nodes: Dict[str, 'HierarchyNode']) -> Tuple[ValidationResult, int, int]:
    """
    Validate and parse SGTINs for all nodes.
    
    Returns:
        (validation_result, success_count, failure_count)
    """
    result = ValidationResult()
    success_count = 0
    failure_count = 0
    
    for node_id, node in nodes.items():
        try:
            sgtin = parse_sgtin(
                serial_number=node.raw_serial_number,
                gs1_prefix=node.gs1_prefix,
                product_code=node.product_code
            )
            node.sgtin = sgtin
            success_count += 1
        except SGTINParseError as e:
            node.sgtin_parse_error = str(e)
            result.add_error(f"Record {node_id}: SGTIN parsing failed - {e}")
            failure_count += 1
    
    return result, success_count, failure_count


def validate_sscc_format(sscc: str) -> ValidationResult:
    """Validate SSCC format"""
    result = ValidationResult()
    
    if not sscc or not isinstance(sscc, str):
        result.add_error("SSCC is required and must be a string")
        return result
    
    # Remove any separators
    clean_sscc = sscc.replace(' ', '').replace('-', '').replace('.', '')
    
    # Should be 18 digits for a valid SSCC
    if not clean_sscc.isdigit():
        result.add_error("SSCC must contain only digits (after removing separators)")
        return result
    
    if len(clean_sscc) != 18:
        result.add_error(f"SSCC must be exactly 18 digits, got {len(clean_sscc)}")
        return result
    
    return result


def validate_location(location: BulkLocation, role: str) -> ValidationResult:
    """Validate location data"""
    result = ValidationResult()
    
    if not location.name:
        result.add_error(f"{role} location: name is required")
    if not location.sgln:
        result.add_error(f"{role} location: SGLN is required")
    if not location.city:
        result.add_error(f"{role} location: city is required")
    if not location.country_code:
        result.add_error(f"{role} location: country code is required")
    
    return result


def build_hierarchy(records: List[Dict[str, Any]]) -> Tuple[Dict[str, HierarchyNode], List[HierarchyNode], ValidationResult]:
    """
    Build hierarchy from records based on parentPackagingId
    Returns: (nodes_dict, root_nodes, validation_result)
    
    Rules:
    - If a record has no parentPackagingId, it is a root node (top-most level, e.g., CASE)
    - If a record has a parentPackagingId that doesn't exist in the uploaded data,
      it is also treated as a root node (the parent is external to this batch)
    """
    result = ValidationResult()
    nodes: Dict[str, HierarchyNode] = {}
    
    # Create all nodes first
    for record in records:
        node_id = record['_id']
        nodes[node_id] = HierarchyNode(record)
    
    # Track nodes with external parents (parent not in uploaded data)
    external_parent_count = 0
    
    # Build parent-child relationships
    for node_id, node in nodes.items():
        if node.parent_id:
            if node.parent_id not in nodes:
                # Parent is not in uploaded data - this node becomes a root
                # This is NOT an error, just informational
                external_parent_count += 1
            else:
                # Parent exists in uploaded data - establish relationship
                parent = nodes[node.parent_id]
                parent.children.append(node)
    
    # Find root nodes: no parent OR parent not in uploaded data
    root_nodes = [node for node in nodes.values() if not node.parent_id or node.parent_id not in nodes]
    
    # Add informational warning if there were external parents
    if external_parent_count > 0:
        result.add_warning(f"{external_parent_count} record(s) reference parent(s) not in uploaded data - treated as root nodes")
    
    # Check for cycles using DFS
    visited = set()
    rec_stack = set()
    
    def has_cycle(node: HierarchyNode) -> bool:
        visited.add(node.id)
        rec_stack.add(node.id)
        
        for child in node.children:
            if child.id not in visited:
                if has_cycle(child):
                    return True
            elif child.id in rec_stack:
                return True
        
        rec_stack.remove(node.id)
        return False
    
    for root in root_nodes:
        if root.id not in visited:
            if has_cycle(root):
                result.add_error(f"Circular relationship detected involving {root.id}")
    
    # Calculate depths
    def calculate_depth(node: HierarchyNode, depth: int = 0):
        node.depth = depth
        for child in node.children:
            calculate_depth(child, depth + 1)
    
    for root in root_nodes:
        calculate_depth(root)
    
    return nodes, root_nodes, result


def validate_packaging_types(nodes: Dict[str, HierarchyNode]) -> ValidationResult:
    """
    Validate packaging type reinforcement rules
    EA < IN < CA < SSCC
    """
    result = ValidationResult()
    
    type_order = {'EA': 0, 'IN': 1, 'CA': 2, 'SSCC': 3}
    
    for node_id, node in nodes.items():
        node_type = node.type.upper() if node.type else 'UNKNOWN'
        
        # Check SSCC in uploaded data
        if node_type == 'SSCC':
            result.add_warning(f"Node {node_id}: type=SSCC found in uploaded data. Will be excluded from hierarchy - use user-provided SSCC only.")
        
        # Check parent-child type relationships
        for child in node.children:
            child_type = child.type.upper() if child.type else 'UNKNOWN'
            
            if node_type in type_order and child_type in type_order:
                parent_level = type_order[node_type]
                child_level = type_order[child_type]
                
                # Invalid: CA to EA, SSCC as child
                if child_level > parent_level:
                    result.add_error(f"Invalid aggregation: {child_type} ({child.id}) cannot be child of {node_type} ({node_id})")
                # Same level warning
                elif child_level == parent_level:
                    result.add_warning(f"Same-level aggregation: {child_type} ({child.id}) → {node_type} ({node_id})")
        
        # Check root anomalies
        if not node.parent_id and len(node.children) > 0 and node_type == 'EA':
            result.add_warning(f"Node {node_id}: type=EA but has children (is a root). This may be incorrect.")
    
    return result


def filter_sscc_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Remove SSCC type records from uploaded data"""
    filtered = []
    sscc_count = 0
    
    for record in records:
        if record.get('type', '').upper() == 'SSCC':
            sscc_count += 1
        else:
            filtered.append(record)
    
    return filtered, sscc_count


def get_max_depth(root_nodes: List[HierarchyNode]) -> int:
    """Calculate maximum depth of hierarchy"""
    max_depth = 0
    
    def traverse(node: HierarchyNode):
        nonlocal max_depth
        if node.depth > max_depth:
            max_depth = node.depth
        for child in node.children:
            traverse(child)
    
    for root in root_nodes:
        traverse(root)
    
    return max_depth


def collect_all_nodes(root_nodes: List[HierarchyNode]) -> List[HierarchyNode]:
    """Collect all nodes from hierarchy trees"""
    all_nodes = []
    
    def traverse(node: HierarchyNode):
        all_nodes.append(node)
        for child in node.children:
            traverse(child)
    
    for root in root_nodes:
        traverse(root)
    
    return all_nodes


def calculate_file_checksum(content: bytes) -> str:
    """Calculate SHA256 checksum of file content"""
    return hashlib.sha256(content).hexdigest()


# ============================================================
# EPCIS GENERATION FUNCTIONS
# ============================================================

def generate_bulk_epcis_xml(
    nodes: Dict[str, HierarchyNode],
    root_nodes: List[HierarchyNode],
    shipping_sscc: str,
    sender_location: BulkLocation,
    receiver_location: BulkLocation
) -> Tuple[str, int, int]:
    """
    Generate EPCIS XML from bulk data
    Returns: (xml_content, commissioning_count, aggregation_count)
    """
    
    # Initialize timestamp management
    base_timestamp = datetime.now(timezone.utc)
    timestamp_counter = 0
    
    def get_next_timestamp():
        nonlocal timestamp_counter
        current_timestamp = base_timestamp + timedelta(seconds=timestamp_counter)
        timestamp_counter += 1
        return current_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def get_final_timestamp():
        return (base_timestamp + timedelta(seconds=timestamp_counter)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Create root element
    root = ET.Element("epcis:EPCISDocument")
    root.set("xmlns:epcis", "urn:epcglobal:epcis:xsd:1")
    root.set("xmlns:cbvmd", "urn:epcglobal:cbv:mda")
    root.set("xmlns:cbvmda", "urn:epcglobal:cbv:mda")
    root.set("xmlns:gs1ushc", "http://epcis.gs1us.org/hc/ns")
    root.set("xmlns:sbdh", "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader")
    root.set("schemaVersion", "1.2")
    root.set("creationDate", get_next_timestamp())
    
    # Create EPCISHeader
    epcis_header = ET.SubElement(root, "EPCISHeader")
    
    # Create SBDH Header
    sbdh = ET.SubElement(epcis_header, "sbdh:StandardBusinessDocumentHeader")
    
    header_version = ET.SubElement(sbdh, "sbdh:HeaderVersion")
    header_version.text = "1.0"
    
    # Sender
    sender = ET.SubElement(sbdh, "sbdh:Sender")
    sender_identifier = ET.SubElement(sender, "sbdh:Identifier")
    sender_identifier.set("Authority", "GS1")
    sender_identifier.text = sender_location.sgln.split('.')[0] if '.' in sender_location.sgln else sender_location.sgln
    
    # Receiver
    receiver = ET.SubElement(sbdh, "sbdh:Receiver")
    receiver_identifier = ET.SubElement(receiver, "sbdh:Identifier")
    receiver_identifier.set("Authority", "GS1")
    receiver_identifier.text = receiver_location.sgln.split('.')[0] if '.' in receiver_location.sgln else receiver_location.sgln
    
    # Document Identification
    doc_identification = ET.SubElement(sbdh, "sbdh:DocumentIdentification")
    standard = ET.SubElement(doc_identification, "sbdh:Standard")
    standard.text = "EPCglobal"
    type_version = ET.SubElement(doc_identification, "sbdh:TypeVersion")
    type_version.text = "1.0"
    instance_identifier = ET.SubElement(doc_identification, "sbdh:InstanceIdentifier")
    instance_identifier.text = f"BULK_EPCIS_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    type_element = ET.SubElement(doc_identification, "sbdh:Type")
    type_element.text = "Events"
    creation_date_time = ET.SubElement(doc_identification, "sbdh:CreationDateAndTime")
    
    # Add EPCISMasterData
    extension = ET.SubElement(epcis_header, "extension")
    epcis_master_data = ET.SubElement(extension, "EPCISMasterData")
    vocabulary_list = ET.SubElement(epcis_master_data, "VocabularyList")
    
    # EPCClass Vocabulary
    epcclass_vocabulary = ET.SubElement(vocabulary_list, "Vocabulary")
    epcclass_vocabulary.set("type", "urn:epcglobal:epcis:vtype:EPCClass")
    epcclass_element_list = ET.SubElement(epcclass_vocabulary, "VocabularyElementList")
    
    # Deduplicate EPCClass entries by additionalTradeItemIdentification
    seen_trade_item_ids = set()
    all_nodes = collect_all_nodes(root_nodes)
    
    for node in all_nodes:
        trade_item_id = node.additional_trade_item_id
        if trade_item_id and trade_item_id not in seen_trade_item_ids:
            seen_trade_item_ids.add(trade_item_id)
            
            vocab_element = ET.SubElement(epcclass_element_list, "VocabularyElement")
            vocab_element.set("id", f"urn:epc:idpat:sgtin:{trade_item_id}.*")
            
            # Add attributes
            if trade_item_id:
                attr = ET.SubElement(vocab_element, "attribute")
                attr.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentification")
                attr.text = trade_item_id
            
            if node.regulated_product_name:
                attr = ET.SubElement(vocab_element, "attribute")
                attr.set("id", "urn:epcglobal:cbv:mda#regulatedProductName")
                attr.text = node.regulated_product_name
            
            if node.manufacturer_name:
                attr = ET.SubElement(vocab_element, "attribute")
                attr.set("id", "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName")
                attr.text = node.manufacturer_name
            
            if node.dosage_form:
                attr = ET.SubElement(vocab_element, "attribute")
                attr.set("id", "urn:epcglobal:cbv:mda#dosageFormType")
                attr.text = node.dosage_form
            
            if node.strength:
                attr = ET.SubElement(vocab_element, "attribute")
                attr.set("id", "urn:epcglobal:cbv:mda#strengthDescription")
                attr.text = node.strength
    
    # Location Vocabulary
    location_vocabulary = ET.SubElement(vocabulary_list, "Vocabulary")
    location_vocabulary.set("type", "urn:epcglobal:epcis:vtype:Location")
    location_element_list = ET.SubElement(location_vocabulary, "VocabularyElementList")
    
    def add_location_element(loc: BulkLocation, element_list):
        loc_element = ET.SubElement(element_list, "VocabularyElement")
        loc_element.set("id", f"urn:epc:id:sgln:{loc.sgln}")
        
        if loc.name:
            attr = ET.SubElement(loc_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#name")
            attr.text = loc.name
        
        if loc.street_address_one:
            attr = ET.SubElement(loc_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#streetAddressOne")
            attr.text = loc.street_address_one
        
        if loc.city:
            attr = ET.SubElement(loc_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#city")
            attr.text = loc.city
        
        if loc.state:
            attr = ET.SubElement(loc_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#state")
            attr.text = loc.state
        
        if loc.postal_code:
            attr = ET.SubElement(loc_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#postalCode")
            attr.text = loc.postal_code
        
        if loc.country_code:
            attr = ET.SubElement(loc_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#countryCode")
            attr.text = loc.country_code
    
    add_location_element(sender_location, location_element_list)
    add_location_element(receiver_location, location_element_list)
    
    # Add gs1ushc:dscsaTransactionStatement
    dscsa_statement = ET.SubElement(epcis_header, "gs1ushc:dscsaTransactionStatement")
    affirm_statement = ET.SubElement(dscsa_statement, "gs1ushc:affirmTransactionStatement")
    affirm_statement.text = "true"
    legal_notice = ET.SubElement(dscsa_statement, "gs1ushc:legalNotice")
    legal_notice.text = "Seller has complied with each applicable subsection of FDCA Sec. 581(27)(A)-(G)."
    
    # Create EPCISBody
    epcis_body = ET.SubElement(root, "EPCISBody")
    event_list = ET.SubElement(epcis_body, "EventList")
    
    read_point = f"urn:epc:id:sgln:{sender_location.sgln}"
    biz_location = f"urn:epc:id:sgln:{sender_location.sgln}"
    
    commissioning_count = 0
    aggregation_count = 0
    
    # Helper to add ILMD extension
    def add_ilmd_extension(event_element, lot_number: str, expiration_date: str):
        if lot_number or expiration_date:
            ext = ET.SubElement(event_element, "extension")
            ilmd = ET.SubElement(ext, "ilmd")
            
            if lot_number:
                lot = ET.SubElement(ilmd, "cbvmda:lotNumber")
                lot.text = lot_number
            
            if expiration_date:
                # Format expiration date
                exp_str = expiration_date
                if 'T' in str(expiration_date):
                    exp_str = str(expiration_date).split('T')[0]
                exp = ET.SubElement(ilmd, "cbvmda:itemExpirationDate")
                exp.text = exp_str
    
    # 1. COMMISSIONING ObjectEvents - One per valid record
    for node in all_nodes:
        object_event = ET.SubElement(event_list, "ObjectEvent")
        
        event_time = ET.SubElement(object_event, "eventTime")
        event_time.text = get_next_timestamp()
        
        event_timezone = ET.SubElement(object_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        epc_list = ET.SubElement(object_event, "epcList")
        epc = ET.SubElement(epc_list, "epc")
        epc.text = f"urn:epc:id:sgtin:{node.serial_number}"
        
        action = ET.SubElement(object_event, "action")
        action.text = "ADD"
        
        biz_step = ET.SubElement(object_event, "bizStep")
        biz_step.text = "urn:epcglobal:cbv:bizstep:commissioning"
        
        disposition = ET.SubElement(object_event, "disposition")
        disposition.text = "urn:epcglobal:cbv:disp:active"
        
        read_point_elem = ET.SubElement(object_event, "readPoint")
        read_point_id = ET.SubElement(read_point_elem, "id")
        read_point_id.text = read_point
        
        biz_location_elem = ET.SubElement(object_event, "bizLocation")
        biz_location_id = ET.SubElement(biz_location_elem, "id")
        biz_location_id.text = biz_location
        
        # Add ILMD with lot and expiration
        add_ilmd_extension(object_event, node.lot, node.expiration)
        
        commissioning_count += 1
    
    # 2. AGGREGATION Events - For each parent with children
    def create_aggregation_events(node: HierarchyNode):
        nonlocal aggregation_count
        
        if node.children:
            aggregation_event = ET.SubElement(event_list, "AggregationEvent")
            
            event_time = ET.SubElement(aggregation_event, "eventTime")
            event_time.text = get_next_timestamp()
            
            event_timezone = ET.SubElement(aggregation_event, "eventTimeZoneOffset")
            event_timezone.text = "+00:00"
            
            parent_id = ET.SubElement(aggregation_event, "parentID")
            parent_id.text = f"urn:epc:id:sgtin:{node.serial_number}"
            
            child_epcs = ET.SubElement(aggregation_event, "childEPCs")
            for child in node.children:
                child_epc = ET.SubElement(child_epcs, "epc")
                child_epc.text = f"urn:epc:id:sgtin:{child.serial_number}"
            
            action = ET.SubElement(aggregation_event, "action")
            action.text = "ADD"
            
            biz_step = ET.SubElement(aggregation_event, "bizStep")
            biz_step.text = "urn:epcglobal:cbv:bizstep:packing"
            
            read_point_elem = ET.SubElement(aggregation_event, "readPoint")
            read_point_id = ET.SubElement(read_point_elem, "id")
            read_point_id.text = read_point
            
            biz_location_elem = ET.SubElement(aggregation_event, "bizLocation")
            biz_location_id = ET.SubElement(biz_location_elem, "id")
            biz_location_id.text = biz_location
            
            # Add ILMD with parent's lot and expiration
            add_ilmd_extension(aggregation_event, node.lot, node.expiration)
            
            aggregation_count += 1
        
        # Recurse for children
        for child in node.children:
            create_aggregation_events(child)
    
    for root_node in root_nodes:
        create_aggregation_events(root_node)
    
    # 3. MASS AGGREGATION - All root nodes under user-provided SSCC
    if root_nodes:
        mass_aggregation_event = ET.SubElement(event_list, "AggregationEvent")
        
        event_time = ET.SubElement(mass_aggregation_event, "eventTime")
        event_time.text = get_next_timestamp()
        
        event_timezone = ET.SubElement(mass_aggregation_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        parent_id = ET.SubElement(mass_aggregation_event, "parentID")
        # Format SSCC as URN
        clean_sscc = shipping_sscc.replace(' ', '').replace('-', '').replace('.', '')
        parent_id.text = f"urn:epc:id:sscc:{clean_sscc[0]}.{clean_sscc[1:]}"
        
        child_epcs = ET.SubElement(mass_aggregation_event, "childEPCs")
        for root_node in root_nodes:
            child_epc = ET.SubElement(child_epcs, "epc")
            child_epc.text = f"urn:epc:id:sgtin:{root_node.serial_number}"
        
        action = ET.SubElement(mass_aggregation_event, "action")
        action.text = "ADD"
        
        biz_step = ET.SubElement(mass_aggregation_event, "bizStep")
        biz_step.text = "urn:epcglobal:cbv:bizstep:packing"
        
        read_point_elem = ET.SubElement(mass_aggregation_event, "readPoint")
        read_point_id = ET.SubElement(read_point_elem, "id")
        read_point_id.text = read_point
        
        biz_location_elem = ET.SubElement(mass_aggregation_event, "bizLocation")
        biz_location_id = ET.SubElement(biz_location_elem, "id")
        biz_location_id.text = biz_location
        
        aggregation_count += 1
    
    # 4. SHIPPING ObjectEvent - Final event for the SSCC
    shipping_event = ET.SubElement(event_list, "ObjectEvent")
    
    event_time = ET.SubElement(shipping_event, "eventTime")
    event_time.text = get_next_timestamp()
    
    event_timezone = ET.SubElement(shipping_event, "eventTimeZoneOffset")
    event_timezone.text = "+00:00"
    
    epc_list = ET.SubElement(shipping_event, "epcList")
    epc = ET.SubElement(epc_list, "epc")
    clean_sscc = shipping_sscc.replace(' ', '').replace('-', '').replace('.', '')
    epc.text = f"urn:epc:id:sscc:{clean_sscc[0]}.{clean_sscc[1:]}"
    
    action = ET.SubElement(shipping_event, "action")
    action.text = "OBSERVE"
    
    biz_step = ET.SubElement(shipping_event, "bizStep")
    biz_step.text = "urn:epcglobal:cbv:bizstep:shipping"
    
    disposition = ET.SubElement(shipping_event, "disposition")
    disposition.text = "urn:epcglobal:cbv:disp:in_transit"
    
    read_point_elem = ET.SubElement(shipping_event, "readPoint")
    read_point_id = ET.SubElement(read_point_elem, "id")
    read_point_id.text = read_point
    
    biz_location_elem = ET.SubElement(shipping_event, "bizLocation")
    biz_location_id = ET.SubElement(biz_location_elem, "id")
    biz_location_id.text = biz_location
    
    # Add extension with sourceList and destinationList
    ext = ET.SubElement(shipping_event, "extension")
    
    source_list = ET.SubElement(ext, "sourceList")
    source_owning = ET.SubElement(source_list, "source")
    source_owning.set("type", "urn:epcglobal:cbv:sdt:owning_party")
    source_owning.text = f"urn:epc:id:sgln:{sender_location.sgln}"
    source_location = ET.SubElement(source_list, "source")
    source_location.set("type", "urn:epcglobal:cbv:sdt:location")
    source_location.text = f"urn:epc:id:sgln:{sender_location.sgln}"
    
    destination_list = ET.SubElement(ext, "destinationList")
    dest_owning = ET.SubElement(destination_list, "destination")
    dest_owning.set("type", "urn:epcglobal:cbv:sdt:owning_party")
    dest_owning.text = f"urn:epc:id:sgln:{receiver_location.sgln}"
    dest_location = ET.SubElement(destination_list, "destination")
    dest_location.set("type", "urn:epcglobal:cbv:sdt:location")
    dest_location.text = f"urn:epc:id:sgln:{receiver_location.sgln}"
    
    # Update SBDH CreationDateAndTime
    creation_date_time.text = get_final_timestamp()
    
    # Convert to string
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True), commissioning_count, aggregation_count


# ============================================================
# MAIN PROCESSING FUNCTION
# ============================================================

def process_bulk_epcis(
    json_data: List[Dict[str, Any]],
    shipping_sscc: str,
    sender_location: BulkLocation,
    receiver_location: BulkLocation,
    input_filename: str,
    file_content: bytes
) -> Tuple[Optional[str], BulkEPCISSummary, ValidationResult]:
    """
    Main function to process bulk EPCIS creation
    Returns: (xml_content, summary, validation_result)
    """
    job_id = str(uuid.uuid4())
    validation = ValidationResult()
    
    # Step 1: Validate JSON structure
    json_validation = validate_json_structure(json_data)
    validation.merge(json_validation)
    
    if not validation.is_valid:
        return None, BulkEPCISSummary(
            total_records_processed=0,
            commissioning_events_created=0,
            aggregation_events_created=0,
            root_epcs_aggregated=0,
            max_hierarchy_depth=0,
            sender_sgln=sender_location.sgln,
            receiver_sgln=receiver_location.sgln,
            validation_warnings_count=len(validation.warnings),
            validation_warnings=validation.warnings,
            generation_status="FAILED",
            filename="",
            job_id=job_id
        ), validation
    
    # Step 2: Validate SSCC
    sscc_validation = validate_sscc_format(shipping_sscc)
    validation.merge(sscc_validation)
    
    # Step 3: Validate locations
    sender_validation = validate_location(sender_location, "Sender")
    validation.merge(sender_validation)
    
    receiver_validation = validate_location(receiver_location, "Receiver")
    validation.merge(receiver_validation)
    
    if not validation.is_valid:
        return None, BulkEPCISSummary(
            total_records_processed=len(json_data),
            commissioning_events_created=0,
            aggregation_events_created=0,
            root_epcs_aggregated=0,
            max_hierarchy_depth=0,
            sender_sgln=sender_location.sgln,
            receiver_sgln=receiver_location.sgln,
            validation_warnings_count=len(validation.warnings),
            validation_warnings=validation.warnings,
            generation_status="FAILED",
            filename="",
            job_id=job_id
        ), validation
    
    # Step 4: Filter out SSCC records from uploaded data
    filtered_data, sscc_filtered_count = filter_sscc_records(json_data)
    
    if sscc_filtered_count > 0:
        validation.add_warning(f"Excluded {sscc_filtered_count} SSCC-type records from uploaded data. Using user-provided SSCC only.")
    
    # Step 5: Build hierarchy
    nodes, root_nodes, hierarchy_validation = build_hierarchy(filtered_data)
    validation.merge(hierarchy_validation)
    
    if not validation.is_valid:
        return None, BulkEPCISSummary(
            total_records_processed=len(json_data),
            commissioning_events_created=0,
            aggregation_events_created=0,
            root_epcs_aggregated=0,
            max_hierarchy_depth=0,
            sender_sgln=sender_location.sgln,
            receiver_sgln=receiver_location.sgln,
            validation_warnings_count=len(validation.warnings),
            validation_warnings=validation.warnings,
            generation_status="FAILED",
            filename="",
            job_id=job_id
        ), validation
    
    # Step 6: Validate packaging types (reinforcement)
    type_validation = validate_packaging_types(nodes)
    validation.merge(type_validation)
    
    if not validation.is_valid:
        return None, BulkEPCISSummary(
            total_records_processed=len(json_data),
            commissioning_events_created=0,
            aggregation_events_created=0,
            root_epcs_aggregated=len(root_nodes),
            max_hierarchy_depth=get_max_depth(root_nodes),
            sender_sgln=sender_location.sgln,
            receiver_sgln=receiver_location.sgln,
            validation_warnings_count=len(validation.warnings),
            validation_warnings=validation.warnings,
            generation_status="FAILED",
            filename="",
            job_id=job_id
        ), validation
    
    # Step 7: Generate EPCIS XML
    xml_content, commissioning_count, aggregation_count = generate_bulk_epcis_xml(
        nodes, root_nodes, shipping_sscc, sender_location, receiver_location
    )
    
    # Generate filename
    today_date = datetime.now(timezone.utc).strftime("%y%m%d")
    filename = f"bulk-epcis-{sender_location.sgln.replace('.', '-')}-{receiver_location.sgln.replace('.', '-')}-{today_date}.xml"
    
    summary = BulkEPCISSummary(
        total_records_processed=len(filtered_data),
        commissioning_events_created=commissioning_count,
        aggregation_events_created=aggregation_count,
        root_epcs_aggregated=len(root_nodes),
        max_hierarchy_depth=get_max_depth(root_nodes),
        sender_sgln=sender_location.sgln,
        receiver_sgln=receiver_location.sgln,
        validation_warnings_count=len(validation.warnings),
        validation_warnings=validation.warnings,
        generation_status="SUCCESS",
        filename=filename,
        job_id=job_id
    )
    
    return xml_content, summary, validation
