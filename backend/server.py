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
    sscc_indicator_digit: str
    case_indicator_digit: str
    inner_case_indicator_digit: str = Field(default="")
    item_indicator_digit: str
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
    sscc_indicator_digit: str
    case_indicator_digit: str
    inner_case_indicator_digit: str = Field(default="")
    item_indicator_digit: str

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
    total_cases = config["cases_per_sscc"] * config["number_of_sscc"]
    
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
    
    if config["use_inner_cases"]:
        if len(input.inner_case_serial_numbers) != total_inner_cases:
            raise HTTPException(
                status_code=400, 
                detail=f"Expected {total_inner_cases} inner case serial numbers, got {len(input.inner_case_serial_numbers)}"
            )
    else:
        if len(input.inner_case_serial_numbers) > 0:
            raise HTTPException(
                status_code=400, 
                detail="Inner case serial numbers provided but inner cases are not enabled in configuration"
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

def generate_epcis_xml(config, serial_numbers, read_point, biz_location):
    """Generate GS1 EPCIS 1.2 XML for pharmaceutical aggregation with commissioning events"""
    
    # Create root element with EPCIS 1.2 namespace
    root = ET.Element("EPCISDocument")
    root.set("xmlns", "urn:epcglobal:epcis:xsd:1")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("schemaVersion", "1.2")
    root.set("creationDate", datetime.now(timezone.utc).isoformat())
    
    # Create EPCISBody
    epcis_body = ET.SubElement(root, "EPCISBody")
    event_list = ET.SubElement(epcis_body, "EventList")
    
    # Get configuration parameters
    company_prefix = config["company_prefix"]
    item_product_code = config["item_product_code"]
    case_product_code = config["case_product_code"]
    sscc_indicator_digit = config["sscc_indicator_digit"]
    case_indicator_digit = config["case_indicator_digit"]
    item_indicator_digit = config["item_indicator_digit"]
    
    items_per_case = config["items_per_case"]
    cases_per_sscc = config["cases_per_sscc"]
    number_of_sscc = config["number_of_sscc"]
    
    # Get serial numbers
    sscc_serials = serial_numbers["sscc_serial_numbers"]
    case_serials = serial_numbers["case_serial_numbers"]
    item_serials = serial_numbers["item_serial_numbers"]
    
    # Generate proper EPC identifiers
    sscc_epcs = []
    case_epcs = []
    item_epcs = []
    
    for sscc_serial in sscc_serials:
        sscc_epc = f"urn:epc:id:sscc:{company_prefix}.{sscc_indicator_digit}{sscc_serial}"
        sscc_epcs.append(sscc_epc)
    
    for case_serial in case_serials:
        case_epc = f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}.{case_serial}"
        case_epcs.append(case_epc)
    
    for item_serial in item_serials:
        item_epc = f"urn:epc:id:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}.{item_serial}"
        item_epcs.append(item_epc)
    
    # 1. Commissioning Events for Items
    for item_epc in item_epcs:
        object_event = ET.SubElement(event_list, "ObjectEvent")
        
        event_time = ET.SubElement(object_event, "eventTime")
        event_time.text = datetime.now(timezone.utc).isoformat()
        
        event_timezone = ET.SubElement(object_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        epc_list = ET.SubElement(object_event, "epcList")
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
    
    # 2. Commissioning Events for Cases
    for case_epc in case_epcs:
        object_event = ET.SubElement(event_list, "ObjectEvent")
        
        event_time = ET.SubElement(object_event, "eventTime")
        event_time.text = datetime.now(timezone.utc).isoformat()
        
        event_timezone = ET.SubElement(object_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        epc_list = ET.SubElement(object_event, "epcList")
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
    
    # 3. Commissioning Events for SSCCs
    for sscc_epc in sscc_epcs:
        object_event = ET.SubElement(event_list, "ObjectEvent")
        
        event_time = ET.SubElement(object_event, "eventTime")
        event_time.text = datetime.now(timezone.utc).isoformat()
        
        event_timezone = ET.SubElement(object_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        epc_list = ET.SubElement(object_event, "epcList")
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
    
    # 4. Aggregation Events - Items into Cases
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
    
    # 5. Aggregation Events - Cases into SSCCs
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