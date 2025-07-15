from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class SerialConfiguration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items_per_case: int = Field(default=0)  # Used when no inner cases
    cases_per_sscc: int
    number_of_sscc: int
    use_inner_cases: bool = Field(default=False)
    inner_cases_per_case: int = Field(default=0)  # Used when inner cases enabled
    items_per_inner_case: int = Field(default=0)  # Used when inner cases enabled
    company_prefix: str
    item_product_code: str
    case_product_code: str
    inner_case_product_code: str = Field(default="")
    lot_number: str = Field(default="")
    expiration_date: str = Field(default="")
    sscc_indicator_digit: str
    case_indicator_digit: str
    inner_case_indicator_digit: str = Field(default="")
    item_indicator_digit: str
    # EPCClass data
    product_ndc: str = Field(default="")
    package_ndc: str = Field(default="")
    regulated_product_name: str = Field(default="")
    manufacturer_name: str = Field(default="")
    dosage_form_type: str = Field(default="")
    strength_description: str = Field(default="")
    net_content_description: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SerialConfigurationCreate(BaseModel):
    items_per_case: int = Field(default=0)
    cases_per_sscc: int
    number_of_sscc: int
    use_inner_cases: bool = Field(default=False)
    inner_cases_per_case: int = Field(default=0)
    items_per_inner_case: int = Field(default=0)
    company_prefix: str
    item_product_code: str
    case_product_code: str
    inner_case_product_code: str = Field(default="")
    lot_number: str = Field(default="")
    expiration_date: str = Field(default="")
    sscc_indicator_digit: str
    case_indicator_digit: str
    inner_case_indicator_digit: str = Field(default="")
    item_indicator_digit: str
    # EPCClass data
    product_ndc: str = Field(default="")
    package_ndc: str = Field(default="")
    regulated_product_name: str = Field(default="")
    manufacturer_name: str = Field(default="")
    dosage_form_type: str = Field(default="")
    strength_description: str = Field(default="")
    net_content_description: str = Field(default="")

class SerialNumbers(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    configuration_id: str
    sscc_serial_numbers: List[str]
    case_serial_numbers: List[str]
    inner_case_serial_numbers: List[str] = Field(default_factory=list)
    item_serial_numbers: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SerialNumbersCreate(BaseModel):
    configuration_id: str
    sscc_serial_numbers: List[str]
    case_serial_numbers: List[str]
    inner_case_serial_numbers: List[str] = Field(default_factory=list)
    item_serial_numbers: List[str]

class EPCISGenerationRequest(BaseModel):
    configuration_id: str
    read_point: str = "urn:epc:id:sgln:1234567.00000.0"
    biz_location: str = "urn:epc:id:sgln:1234567.00001.0"

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "EPCIS Serial Number Aggregation API"}

@api_router.post("/configuration", response_model=SerialConfiguration)
async def create_configuration(input: SerialConfigurationCreate):
    config_dict = input.dict()
    config_obj = SerialConfiguration(**config_dict)
    await db.configurations.insert_one(config_obj.dict())
    return config_obj

@api_router.get("/configuration", response_model=List[SerialConfiguration])
async def get_configurations():
    configurations = await db.configurations.find().to_list(1000)
    return [SerialConfiguration(**config) for config in configurations]

@api_router.post("/serial-numbers", response_model=SerialNumbers)
async def create_serial_numbers(input: SerialNumbersCreate):
    # Validate configuration exists
    config = await db.configurations.find_one({"id": input.configuration_id})
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Calculate expected quantities based on configuration
    cases_per_sscc = config["cases_per_sscc"]
    
    # If no cases, items go directly in SSCC
    if cases_per_sscc == 0:
        total_cases = 0
        total_inner_cases = 0
        total_items = config["items_per_case"] * config["number_of_sscc"]
    else:
        total_cases = cases_per_sscc * config["number_of_sscc"]
        
        if config["use_inner_cases"]:
            total_inner_cases = config["inner_cases_per_case"] * total_cases
            total_items = config["items_per_inner_case"] * total_inner_cases
        else:
            total_inner_cases = 0
            total_items = config["items_per_case"] * total_cases
    
    # Validate serial numbers count
    if len(input.sscc_serial_numbers) != config["number_of_sscc"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Expected {config['number_of_sscc']} SSCC serial numbers, got {len(input.sscc_serial_numbers)}"
        )
    
    if len(input.case_serial_numbers) != total_cases:
        raise HTTPException(
            status_code=400, 
            detail=f"Expected {total_cases} case serial numbers, got {len(input.case_serial_numbers)}"
        )
    
    if config["use_inner_cases"] and cases_per_sscc > 0:
        if len(input.inner_case_serial_numbers) != total_inner_cases:
            raise HTTPException(
                status_code=400, 
                detail=f"Expected {total_inner_cases} inner case serial numbers, got {len(input.inner_case_serial_numbers)}"
            )
    else:
        if len(input.inner_case_serial_numbers) > 0:
            raise HTTPException(
                status_code=400, 
                detail="Inner case serial numbers provided but not expected for this configuration"
            )
    
    if len(input.item_serial_numbers) != total_items:
        raise HTTPException(
            status_code=400, 
            detail=f"Expected {total_items} item serial numbers, got {len(input.item_serial_numbers)}"
        )
    
    serial_dict = input.dict()
    serial_obj = SerialNumbers(**serial_dict)
    await db.serial_numbers.insert_one(serial_obj.dict())
    return serial_obj

@api_router.get("/serial-numbers/{configuration_id}", response_model=SerialNumbers)
async def get_serial_numbers(configuration_id: str):
    serial_numbers = await db.serial_numbers.find_one({"configuration_id": configuration_id})
    if not serial_numbers:
        raise HTTPException(status_code=404, detail="Serial numbers not found")
    return SerialNumbers(**serial_numbers)

@api_router.post("/generate-epcis")
async def generate_epcis(request: EPCISGenerationRequest):
    # Get configuration and serial numbers
    config = await db.configurations.find_one({"id": request.configuration_id})
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    serial_numbers = await db.serial_numbers.find_one({"configuration_id": request.configuration_id})
    if not serial_numbers:
        raise HTTPException(status_code=404, detail="Serial numbers not found")
    
    # Generate EPCIS XML
    xml_content = generate_epcis_xml(
        config, 
        serial_numbers, 
        request.read_point,
        request.biz_location
    )
    
    # Return as downloadable file
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=epcis_aggregation.xml"}
    )

def add_ilmd_extension(event_element, lot_number, expiration_date):
    """Add ILMD extension with lot number and expiration date to an event"""
    if lot_number or expiration_date:
        extension = ET.SubElement(event_element, "extension")
        ilmd = ET.SubElement(extension, "ilmd")
        
        # Register the cbvmda namespace
        ET.register_namespace("cbvmda", "urn:epcglobal:cbv:mda")
        
        if lot_number:
            lot_elem = ET.SubElement(ilmd, "{urn:epcglobal:cbv:mda}lotNumber")
            lot_elem.text = lot_number
        
        if expiration_date:
            exp_elem = ET.SubElement(ilmd, "{urn:epcglobal:cbv:mda}itemExpirationDate")
            exp_elem.text = expiration_date

def generate_epcis_xml(config, serial_numbers, read_point, biz_location):
    """Generate GS1 EPCIS 1.2 XML for pharmaceutical aggregation with optional inner cases"""
    
    # Create root element with EPCIS 1.2 namespace
    root = ET.Element("EPCISDocument")
    root.set("xmlns", "urn:epcglobal:epcis:xsd:1")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("schemaVersion", "1.2")
    root.set("creationDate", datetime.now(timezone.utc).isoformat())
    
    # Create EPCISHeader and EPCISMasterData
    epcis_header = ET.SubElement(root, "EPCISHeader")
    
    # Add EPCISMasterData with EPCClass vocabulary
    epcis_master_data = ET.SubElement(epcis_header, "EPCISMasterData")
    vocabulary_list = ET.SubElement(epcis_master_data, "VocabularyList")
    
    # Add EPCClass vocabulary
    vocabulary = ET.SubElement(vocabulary_list, "Vocabulary")
    vocabulary.set("type", "urn:epcglobal:epcis:vtype:EPCClass")
    
    vocabulary_element_list = ET.SubElement(vocabulary, "VocabularyElementList")
    
    # Create EPCClass vocabulary element
    company_prefix = config["company_prefix"]
    item_product_code = config["item_product_code"]
    item_indicator_digit = config["item_indicator_digit"]
    
    # Generate the EPC pattern for items
    epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}.*"
    
    vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
    vocabulary_element.set("id", epc_pattern)
    
    # Add EPCClass attributes
    if config.get("product_ndc"):
        attr = ET.SubElement(vocabulary_element, "attribute")
        attr.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentification")
        attr.text = config["product_ndc"]
        
        attr_type = ET.SubElement(vocabulary_element, "attribute")
        attr_type.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentificationTypeCode")
        attr_type.text = "FDA_NDC_11"
    
    if config.get("regulated_product_name"):
        attr = ET.SubElement(vocabulary_element, "attribute")
        attr.set("id", "urn:epcglobal:cbv:mda#regulatedProductName")
        attr.text = config["regulated_product_name"]
    
    if config.get("manufacturer_name"):
        attr = ET.SubElement(vocabulary_element, "attribute")
        attr.set("id", "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName")
        attr.text = config["manufacturer_name"]
    
    if config.get("dosage_form_type"):
        attr = ET.SubElement(vocabulary_element, "attribute")
        attr.set("id", "urn:epcglobal:cbv:mda#dosageFormType")
        attr.text = config["dosage_form_type"]
    
    if config.get("strength_description"):
        attr = ET.SubElement(vocabulary_element, "attribute")
        attr.set("id", "urn:epcglobal:cbv:mda#strengthDescription")
        attr.text = config["strength_description"]
    
    if config.get("net_content_description"):
        attr = ET.SubElement(vocabulary_element, "attribute")
        attr.set("id", "urn:epcglobal:cbv:mda#netContentDescription")
        attr.text = config["net_content_description"]
    
    # Create EPCISBody
    epcis_body = ET.SubElement(root, "EPCISBody")
    event_list = ET.SubElement(epcis_body, "EventList")
    
    # Get configuration parameters
    case_product_code = config["case_product_code"]
    inner_case_product_code = config.get("inner_case_product_code", "")
    lot_number = config.get("lot_number", "")
    expiration_date = config.get("expiration_date", "")
    sscc_indicator_digit = config["sscc_indicator_digit"]
    case_indicator_digit = config["case_indicator_digit"]
    inner_case_indicator_digit = config.get("inner_case_indicator_digit", "")
    item_indicator_digit = config["item_indicator_digit"]
    
    use_inner_cases = config["use_inner_cases"]
    cases_per_sscc = config["cases_per_sscc"]
    number_of_sscc = config["number_of_sscc"]
    
    # Check if we have direct SSCC → Items aggregation
    direct_sscc_items = cases_per_sscc == 0
    
    if direct_sscc_items:
        items_per_sscc = config["items_per_case"]  # In this case, items_per_case means items_per_sscc
    elif use_inner_cases:
        inner_cases_per_case = config["inner_cases_per_case"]
        items_per_inner_case = config["items_per_inner_case"]
    else:
        items_per_case = config["items_per_case"]
    
    # Get serial numbers
    sscc_serials = serial_numbers["sscc_serial_numbers"]
    case_serials = serial_numbers["case_serial_numbers"]
    inner_case_serials = serial_numbers.get("inner_case_serial_numbers", [])
    item_serials = serial_numbers["item_serial_numbers"]
    
    # Generate proper EPC identifiers
    sscc_epcs = []
    case_epcs = []
    inner_case_epcs = []
    item_epcs = []
    
    # Generate SSCC EPCs
    for sscc_serial in sscc_serials:
        sscc_epc = f"urn:epc:id:sscc:{company_prefix}.{sscc_indicator_digit}{sscc_serial}"
        sscc_epcs.append(sscc_epc)
    
    # Generate Case EPCs (only if cases exist)
    if not direct_sscc_items:
        for case_serial in case_serials:
            case_epc = f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}.{case_serial}"
            case_epcs.append(case_epc)
    
    # Generate Inner Case EPCs if used
    if use_inner_cases and not direct_sscc_items:
        for inner_case_serial in inner_case_serials:
            inner_case_epc = f"urn:epc:id:sgtin:{company_prefix}.{inner_case_indicator_digit}{inner_case_product_code}.{inner_case_serial}"
            inner_case_epcs.append(inner_case_epc)
    
    # Generate Item EPCs
    for item_serial in item_serials:
        item_epc = f"urn:epc:id:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}.{item_serial}"
        item_epcs.append(item_epc)
    
    # 1. Single Commissioning Event for All Items
    if item_epcs:
        object_event = ET.SubElement(event_list, "ObjectEvent")
        
        event_time = ET.SubElement(object_event, "eventTime")
        event_time.text = datetime.now(timezone.utc).isoformat()
        
        event_timezone = ET.SubElement(object_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        epc_list = ET.SubElement(object_event, "epcList")
        for item_epc in item_epcs:
            epc = ET.SubElement(epc_list, "epc")
            epc.text = item_epc
        
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
        
        # Add ILMD extension for inner cases
        add_ilmd_extension(object_event, lot_number, expiration_date)
    
    # 2. Single Commissioning Event for All Inner Cases (if used)
    if use_inner_cases and inner_case_epcs and not direct_sscc_items:
        object_event = ET.SubElement(event_list, "ObjectEvent")
        
        event_time = ET.SubElement(object_event, "eventTime")
        event_time.text = datetime.now(timezone.utc).isoformat()
        
        event_timezone = ET.SubElement(object_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        epc_list = ET.SubElement(object_event, "epcList")
        for inner_case_epc in inner_case_epcs:
            epc = ET.SubElement(epc_list, "epc")
            epc.text = inner_case_epc
        
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
        
        # Add ILMD extension for cases
        add_ilmd_extension(object_event, lot_number, expiration_date)
    
    # 3. Single Commissioning Event for All Cases (if they exist)
    if case_epcs and not direct_sscc_items:
        object_event = ET.SubElement(event_list, "ObjectEvent")
        
        event_time = ET.SubElement(object_event, "eventTime")
        event_time.text = datetime.now(timezone.utc).isoformat()
        
        event_timezone = ET.SubElement(object_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        epc_list = ET.SubElement(object_event, "epcList")
        for case_epc in case_epcs:
            epc = ET.SubElement(epc_list, "epc")
            epc.text = case_epc
        
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
        
        # Add ILMD extension for cases
        add_ilmd_extension(object_event, lot_number, expiration_date)
    
    # 4. Single Commissioning Event for All SSCCs
    if sscc_epcs:
        object_event = ET.SubElement(event_list, "ObjectEvent")
        
        event_time = ET.SubElement(object_event, "eventTime")
        event_time.text = datetime.now(timezone.utc).isoformat()
        
        event_timezone = ET.SubElement(object_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        epc_list = ET.SubElement(object_event, "epcList")
        for sscc_epc in sscc_epcs:
            epc = ET.SubElement(epc_list, "epc")
            epc.text = sscc_epc
        
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
    
    # 5. Aggregation Events
    if direct_sscc_items:
        # Direct SSCC → Items aggregation
        for sscc_index, sscc_epc in enumerate(sscc_epcs):
            aggregation_event = ET.SubElement(event_list, "AggregationEvent")
            
            event_time = ET.SubElement(aggregation_event, "eventTime")
            event_time.text = datetime.now(timezone.utc).isoformat()
            
            event_timezone = ET.SubElement(aggregation_event, "eventTimeZoneOffset")
            event_timezone.text = "+00:00"
            
            parent_id = ET.SubElement(aggregation_event, "parentID")
            parent_id.text = sscc_epc
            
            child_epcs = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = sscc_index * items_per_sscc
            end_idx = start_idx + items_per_sscc
            
            for item_epc in item_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs, "epc")
                child_epc.text = item_epc
            
            action = ET.SubElement(aggregation_event, "action")
            action.text = "ADD"
            
            biz_step = ET.SubElement(aggregation_event, "bizStep")
            biz_step.text = "urn:epcglobal:cbv:bizstep:packing"
            
            disposition = ET.SubElement(aggregation_event, "disposition")
            disposition.text = "urn:epcglobal:cbv:disp:active"
            
            read_point_elem = ET.SubElement(aggregation_event, "readPoint")
            read_point_id = ET.SubElement(read_point_elem, "id")
            read_point_id.text = read_point
            
            biz_location_elem = ET.SubElement(aggregation_event, "bizLocation")
            biz_location_id = ET.SubElement(biz_location_elem, "id")
            biz_location_id.text = biz_location
    
    elif use_inner_cases:
        # Items into Inner Cases
        for inner_case_index, inner_case_epc in enumerate(inner_case_epcs):
            aggregation_event = ET.SubElement(event_list, "AggregationEvent")
            
            event_time = ET.SubElement(aggregation_event, "eventTime")
            event_time.text = datetime.now(timezone.utc).isoformat()
            
            event_timezone = ET.SubElement(aggregation_event, "eventTimeZoneOffset")
            event_timezone.text = "+00:00"
            
            parent_id = ET.SubElement(aggregation_event, "parentID")
            parent_id.text = inner_case_epc
            
            child_epcs = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = inner_case_index * items_per_inner_case
            end_idx = start_idx + items_per_inner_case
            
            for item_epc in item_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs, "epc")
                child_epc.text = item_epc
            
            action = ET.SubElement(aggregation_event, "action")
            action.text = "ADD"
            
            biz_step = ET.SubElement(aggregation_event, "bizStep")
            biz_step.text = "urn:epcglobal:cbv:bizstep:packing"
            
            disposition = ET.SubElement(aggregation_event, "disposition")
            disposition.text = "urn:epcglobal:cbv:disp:active"
            
            read_point_elem = ET.SubElement(aggregation_event, "readPoint")
            read_point_id = ET.SubElement(read_point_elem, "id")
            read_point_id.text = read_point
            
            biz_location_elem = ET.SubElement(aggregation_event, "bizLocation")
            biz_location_id = ET.SubElement(biz_location_elem, "id")
            biz_location_id.text = biz_location
        
        # Inner Cases into Cases
        for case_index, case_epc in enumerate(case_epcs):
            aggregation_event = ET.SubElement(event_list, "AggregationEvent")
            
            event_time = ET.SubElement(aggregation_event, "eventTime")
            event_time.text = datetime.now(timezone.utc).isoformat()
            
            event_timezone = ET.SubElement(aggregation_event, "eventTimeZoneOffset")
            event_timezone.text = "+00:00"
            
            parent_id = ET.SubElement(aggregation_event, "parentID")
            parent_id.text = case_epc
            
            child_epcs = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = case_index * inner_cases_per_case
            end_idx = start_idx + inner_cases_per_case
            
            for inner_case_epc in inner_case_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs, "epc")
                child_epc.text = inner_case_epc
            
            action = ET.SubElement(aggregation_event, "action")
            action.text = "ADD"
            
            biz_step = ET.SubElement(aggregation_event, "bizStep")
            biz_step.text = "urn:epcglobal:cbv:bizstep:packing"
            
            disposition = ET.SubElement(aggregation_event, "disposition")
            disposition.text = "urn:epcglobal:cbv:disp:active"
            
            read_point_elem = ET.SubElement(aggregation_event, "readPoint")
            read_point_id = ET.SubElement(read_point_elem, "id")
            read_point_id.text = read_point
            
            biz_location_elem = ET.SubElement(aggregation_event, "bizLocation")
            biz_location_id = ET.SubElement(biz_location_elem, "id")
            biz_location_id.text = biz_location
    
    else:
        # Direct: Items into Cases (no inner cases)
        for case_index, case_epc in enumerate(case_epcs):
            aggregation_event = ET.SubElement(event_list, "AggregationEvent")
            
            event_time = ET.SubElement(aggregation_event, "eventTime")
            event_time.text = datetime.now(timezone.utc).isoformat()
            
            event_timezone = ET.SubElement(aggregation_event, "eventTimeZoneOffset")
            event_timezone.text = "+00:00"
            
            parent_id = ET.SubElement(aggregation_event, "parentID")
            parent_id.text = case_epc
            
            child_epcs = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = case_index * items_per_case
            end_idx = start_idx + items_per_case
            
            for item_epc in item_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs, "epc")
                child_epc.text = item_epc
            
            action = ET.SubElement(aggregation_event, "action")
            action.text = "ADD"
            
            biz_step = ET.SubElement(aggregation_event, "bizStep")
            biz_step.text = "urn:epcglobal:cbv:bizstep:packing"
            
            disposition = ET.SubElement(aggregation_event, "disposition")
            disposition.text = "urn:epcglobal:cbv:disp:active"
            
            read_point_elem = ET.SubElement(aggregation_event, "readPoint")
            read_point_id = ET.SubElement(read_point_elem, "id")
            read_point_id.text = read_point
            
            biz_location_elem = ET.SubElement(aggregation_event, "bizLocation")
            biz_location_id = ET.SubElement(biz_location_elem, "id")
            biz_location_id.text = biz_location
    
    # 6. Cases into SSCCs (only if cases exist)
    if not direct_sscc_items:
        for sscc_index, sscc_epc in enumerate(sscc_epcs):
            aggregation_event = ET.SubElement(event_list, "AggregationEvent")
            
            event_time = ET.SubElement(aggregation_event, "eventTime")
            event_time.text = datetime.now(timezone.utc).isoformat()
            
            event_timezone = ET.SubElement(aggregation_event, "eventTimeZoneOffset")
            event_timezone.text = "+00:00"
            
            parent_id = ET.SubElement(aggregation_event, "parentID")
            parent_id.text = sscc_epc
            
            child_epcs = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = sscc_index * cases_per_sscc
            end_idx = start_idx + cases_per_sscc
            
            for case_epc in case_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs, "epc")
                child_epc.text = case_epc
            
            action = ET.SubElement(aggregation_event, "action")
            action.text = "ADD"
            
            biz_step = ET.SubElement(aggregation_event, "bizStep")
            biz_step.text = "urn:epcglobal:cbv:bizstep:packing"
            
            disposition = ET.SubElement(aggregation_event, "disposition")
            disposition.text = "urn:epcglobal:cbv:disp:active"
            
            read_point_elem = ET.SubElement(aggregation_event, "readPoint")
            read_point_id = ET.SubElement(read_point_elem, "id")
            read_point_id.text = read_point
            
            biz_location_elem = ET.SubElement(aggregation_event, "bizLocation")
            biz_location_id = ET.SubElement(biz_location_elem, "id")
            biz_location_id.text = biz_location
    
    # Convert to string
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()