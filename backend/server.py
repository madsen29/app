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
    items_per_case: int
    number_of_cases: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SerialConfigurationCreate(BaseModel):
    items_per_case: int
    number_of_cases: int

class SerialNumbers(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    configuration_id: str
    case_serial_numbers: List[str]
    item_serial_numbers: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SerialNumbersCreate(BaseModel):
    configuration_id: str
    case_serial_numbers: List[str]
    item_serial_numbers: List[str]

class EPCISGenerationRequest(BaseModel):
    configuration_id: str
    company_prefix: str = "1234567"
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
    
    # Validate serial numbers count
    expected_items = config["items_per_case"] * config["number_of_cases"]
    if len(input.item_serial_numbers) != expected_items:
        raise HTTPException(
            status_code=400, 
            detail=f"Expected {expected_items} item serial numbers, got {len(input.item_serial_numbers)}"
        )
    
    if len(input.case_serial_numbers) != config["number_of_cases"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Expected {config['number_of_cases']} case serial numbers, got {len(input.case_serial_numbers)}"
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
        request.company_prefix,
        request.read_point,
        request.biz_location
    )
    
    # Return as downloadable file
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=epcis_aggregation.xml"}
    )

def generate_epcis_xml(config, serial_numbers, company_prefix, read_point, biz_location):
    """Generate GS1 EPCIS XML for pharmaceutical aggregation"""
    
    # Create root element
    root = ET.Element("EPCISDocument")
    root.set("xmlns", "urn:epcglobal:epcis:xsd:2")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("schemaVersion", "2.0")
    root.set("creationDate", datetime.now(timezone.utc).isoformat())
    
    # Create EPCISBody
    epcis_body = ET.SubElement(root, "EPCISBody")
    event_list = ET.SubElement(epcis_body, "EventList")
    
    # Generate aggregation events for each case
    items_per_case = config["items_per_case"]
    case_serials = serial_numbers["case_serial_numbers"]
    item_serials = serial_numbers["item_serial_numbers"]
    
    for i, case_serial in enumerate(case_serials):
        # Create aggregation event
        aggregation_event = ET.SubElement(event_list, "AggregationEvent")
        
        # Event time
        event_time = ET.SubElement(aggregation_event, "eventTime")
        event_time.text = datetime.now(timezone.utc).isoformat()
        
        # Event timezone offset
        event_timezone = ET.SubElement(aggregation_event, "eventTimeZoneOffset")
        event_timezone.text = "+00:00"
        
        # Parent ID (Case SSCC)
        parent_id = ET.SubElement(aggregation_event, "parentID")
        parent_id.text = f"urn:epc:id:sscc:{company_prefix}.{case_serial.zfill(17)}"
        
        # Child EPCs (Item SGTINs)
        child_epcs = ET.SubElement(aggregation_event, "childEPCs")
        start_idx = i * items_per_case
        end_idx = start_idx + items_per_case
        
        for item_serial in item_serials[start_idx:end_idx]:
            epc = ET.SubElement(child_epcs, "epc")
            epc.text = f"urn:epc:id:sgtin:{company_prefix}.000000.{item_serial}"
        
        # Action
        action = ET.SubElement(aggregation_event, "action")
        action.text = "ADD"
        
        # Business Step
        biz_step = ET.SubElement(aggregation_event, "bizStep")
        biz_step.text = "urn:epcglobal:cbv:bizstep:packing"
        
        # Disposition
        disposition = ET.SubElement(aggregation_event, "disposition")
        disposition.text = "urn:epcglobal:cbv:disp:active"
        
        # Read Point
        read_point_elem = ET.SubElement(aggregation_event, "readPoint")
        read_point_id = ET.SubElement(read_point_elem, "id")
        read_point_id.text = read_point
        
        # Business Location
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