"""
Bulk EPCIS Creation Module

Handles JSON upload, hierarchy resolution, validation, and EPCIS generation
for bulk packaging data.
"""

import json
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict


class HierarchyNode:
    """Represents a node in the packaging hierarchy"""
    def __init__(self, record: Dict[str, Any]):
        self.id = record['_id']
        self.type = record.get('type', '')
        self.serial_number = record['serialNumber']
        self.lot = record['lot']
        self.expiration = record['expiration']
        self.parent_id = record.get('parentPackagingId')
        self.additional_trade_item_id = record.get('additionalTradeItemIdentification')
        self.regulated_product_name = record.get('regulatedProductName')
        self.manufacturer_name = record.get('manufacturerOfTradeItemPartyName')
        self.dosage_form = record.get('dosageFormType')
        self.strength = record.get('strengthDescription')
        self.children: List['HierarchyNode'] = []
        self.depth = 0


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


def validate_json_structure(data: List[Dict[str, Any]]) -> ValidationResult:
    """Validate JSON structure and required fields"""
    result = ValidationResult()
    
    if not isinstance(data, list):
        result.add_error("JSON must be an array of records")
        return result
    
    if len(data) == 0:
        result.add_error("JSON array is empty")
        return result
    
    required_fields = ['_id', 'serialNumber', 'lot', 'expiration']
    
    for idx, record in enumerate(data):
        if not isinstance(record, dict):
            result.add_error(f"Record {idx} is not an object")
            continue
        
        for field in required_fields:
            if field not in record or not record[field]:
                result.add_error(f"Record {idx} ({record.get('_id', 'unknown')}): missing required field '{field}'")
    
    return result


def build_hierarchy(records: List[Dict[str, Any]]) -> Tuple[Dict[str, HierarchyNode], List[HierarchyNode], ValidationResult]:
    """
    Build hierarchy from records based on parentPackagingId
    Returns: (nodes_dict, root_nodes, validation_result)
    """
    result = ValidationResult()
    nodes: Dict[str, HierarchyNode] = {}
    
    # Create all nodes first
    for record in records:
        node_id = record['_id']
        nodes[node_id] = HierarchyNode(record)
    
    # Build parent-child relationships
    for node_id, node in nodes.items():
        if node.parent_id:
            if node.parent_id not in nodes:
                result.add_error(f"Node {node_id} references missing parent {node.parent_id}")
            else:
                parent = nodes[node.parent_id]
                parent.children.append(node)
    
    # Find root nodes (no parent)
    root_nodes = [node for node in nodes.values() if not node.parent_id]
    
    # Check for cycles
    visited = set()
    
    def has_cycle(node: HierarchyNode, path: Set[str]) -> bool:
        if node.id in path:
            return True
        if node.id in visited:
            return False
        
        visited.add(node.id)
        path.add(node.id)
        
        for child in node.children:
            if has_cycle(child, path):
                return True
        
        path.remove(node.id)
        return False
    
    for root in root_nodes:
        if has_cycle(root, set()):
            result.add_error(f"Circular relationship detected starting from {root.id}")
    
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
            result.add_warning(f"Node {node_id}: type=SSCC found in uploaded data. SSCC should be user-provided only.")
        
        # Check parent-child type relationships
        for child in node.children:
            child_type = child.type.upper() if child.type else 'UNKNOWN'
            
            if node_type in type_order and child_type in type_order:
                parent_level = type_order[node_type]
                child_level = type_order[child_type]
                
                if child_level >= parent_level:
                    # Same level warning
                    if child_level == parent_level:
                        result.add_warning(f"Same-level aggregation: {child_type} ({child.id}) → {node_type} ({node_id})")
                    # Invalid direction
                    else:
                        result.add_error(f"Invalid aggregation: {child_type} ({child.id}) → {node_type} ({node_id}). Child cannot be higher level than parent.")
        
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


def validate_sscc_format(sscc: str) -> bool:
    """Validate SSCC format (simple validation)"""
    # Basic validation: should be numeric string
    if not sscc or not isinstance(sscc, str):
        return False
    
    # Remove any separators
    clean_sscc = sscc.replace(' ', '').replace('-', '')
    
    # Should be 18 digits
    if not clean_sscc.isdigit():
        return False
    
    if len(clean_sscc) != 18:
        return False
    
    return True
