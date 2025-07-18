from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET

# Authentication imports
from auth import (
    UserCreate, UserLogin, User, Token, TokenData,
    authenticate_user, create_user, create_access_token, verify_token,
    get_user_by_email, ACCESS_TOKEN_EXPIRE_MINUTES
)

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
    model_config = {"populate_by_name": True}
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items_per_case: int = Field(default=0, alias="itemsPerCase")  # Used when no inner cases
    cases_per_sscc: int = Field(alias="casesPerSscc")
    number_of_sscc: int = Field(alias="numberOfSscc")
    use_inner_cases: bool = Field(default=False, alias="useInnerCases")
    inner_cases_per_case: int = Field(default=0, alias="innerCasesPerCase")  # Used when inner cases enabled
    items_per_inner_case: int = Field(default=0, alias="itemsPerInnerCase")  # Used when inner cases enabled
    company_prefix: str = Field(alias="companyPrefix")
    item_product_code: str = Field(alias="itemProductCode")
    case_product_code: str = Field(alias="caseProductCode")
    inner_case_product_code: str = Field(default="", alias="innerCaseProductCode")
    lot_number: str = Field(default="", alias="lotNumber")
    expiration_date: str = Field(default="", alias="expirationDate")
    sscc_indicator_digit: str = Field(alias="ssccIndicatorDigit")
    case_indicator_digit: str = Field(alias="caseIndicatorDigit")
    inner_case_indicator_digit: str = Field(default="", alias="innerCaseIndicatorDigit")
    item_indicator_digit: str = Field(alias="itemIndicatorDigit")
    # Business Document Information
    sender_company_prefix: str = Field(default="", alias="senderCompanyPrefix")
    sender_gln: str = Field(default="", alias="senderGln")
    sender_sgln: str = Field(default="", alias="senderSgln")
    sender_name: str = Field(default="", alias="senderName")
    sender_street_address: str = Field(default="", alias="senderStreetAddress")
    sender_city: str = Field(default="", alias="senderCity")
    sender_state: str = Field(default="", alias="senderState")
    sender_postal_code: str = Field(default="", alias="senderPostalCode")
    sender_country_code: str = Field(default="", alias="senderCountryCode")
    sender_despatch_advice_number: str = Field(default="", alias="senderDespatchAdviceNumber")
    receiver_company_prefix: str = Field(default="", alias="receiverCompanyPrefix")
    receiver_gln: str = Field(default="", alias="receiverGln")
    receiver_sgln: str = Field(default="", alias="receiverSgln")
    receiver_name: str = Field(default="", alias="receiverName")
    receiver_street_address: str = Field(default="", alias="receiverStreetAddress")
    receiver_city: str = Field(default="", alias="receiverCity")
    receiver_state: str = Field(default="", alias="receiverState")
    receiver_postal_code: str = Field(default="", alias="receiverPostalCode")
    receiver_country_code: str = Field(default="", alias="receiverCountryCode")
    receiver_po_number: str = Field(default="", alias="receiverPoNumber")
    shipper_company_prefix: str = Field(default="", alias="shipperCompanyPrefix")
    shipper_gln: str = Field(default="", alias="shipperGln")
    shipper_sgln: str = Field(default="", alias="shipperSgln")
    shipper_name: str = Field(default="", alias="shipperName")
    shipper_street_address: str = Field(default="", alias="shipperStreetAddress")
    shipper_city: str = Field(default="", alias="shipperCity")
    shipper_state: str = Field(default="", alias="shipperState")
    shipper_postal_code: str = Field(default="", alias="shipperPostalCode")
    shipper_country_code: str = Field(default="", alias="shipperCountryCode")
    shipper_same_as_sender: bool = Field(default=False, alias="shipperSameAsSender")
    # EPCClass data
    product_ndc: str = Field(default="", alias="productNdc")
    package_ndc: str = Field(default="", alias="packageNdc")
    regulated_product_name: str = Field(default="", alias="regulatedProductName")
    manufacturer_name: str = Field(default="", alias="manufacturerName")
    dosage_form_type: str = Field(default="", alias="dosageFormType")
    strength_description: str = Field(default="", alias="strengthDescription")
    net_content_description: str = Field(default="", alias="netContentDescription")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SerialConfigurationCreate(BaseModel):
    model_config = {"populate_by_name": True}
    
    items_per_case: int = Field(default=0, alias="itemsPerCase")
    cases_per_sscc: int = Field(alias="casesPerSscc")
    number_of_sscc: int = Field(alias="numberOfSscc")
    use_inner_cases: bool = Field(default=False, alias="useInnerCases")
    inner_cases_per_case: int = Field(default=0, alias="innerCasesPerCase")
    items_per_inner_case: int = Field(default=0, alias="itemsPerInnerCase")
    company_prefix: str = Field(alias="companyPrefix")
    item_product_code: str = Field(alias="itemProductCode")
    case_product_code: str = Field(alias="caseProductCode")
    inner_case_product_code: str = Field(default="", alias="innerCaseProductCode")
    lot_number: str = Field(default="", alias="lotNumber")
    expiration_date: str = Field(default="", alias="expirationDate")
    sscc_indicator_digit: str = Field(alias="ssccIndicatorDigit")
    case_indicator_digit: str = Field(alias="caseIndicatorDigit")
    inner_case_indicator_digit: str = Field(default="", alias="innerCaseIndicatorDigit")
    item_indicator_digit: str = Field(alias="itemIndicatorDigit")
    # Business Document Information
    sender_company_prefix: str = Field(default="", alias="senderCompanyPrefix")
    sender_gln: str = Field(default="", alias="senderGln")
    sender_sgln: str = Field(default="", alias="senderSgln")
    sender_name: str = Field(default="", alias="senderName")
    sender_street_address: str = Field(default="", alias="senderStreetAddress")
    sender_city: str = Field(default="", alias="senderCity")
    sender_state: str = Field(default="", alias="senderState")
    sender_postal_code: str = Field(default="", alias="senderPostalCode")
    sender_country_code: str = Field(default="", alias="senderCountryCode")
    sender_despatch_advice_number: str = Field(default="", alias="senderDespatchAdviceNumber")
    receiver_company_prefix: str = Field(default="", alias="receiverCompanyPrefix")
    receiver_gln: str = Field(default="", alias="receiverGln")
    receiver_sgln: str = Field(default="", alias="receiverSgln")
    receiver_name: str = Field(default="", alias="receiverName")
    receiver_street_address: str = Field(default="", alias="receiverStreetAddress")
    receiver_city: str = Field(default="", alias="receiverCity")
    receiver_state: str = Field(default="", alias="receiverState")
    receiver_postal_code: str = Field(default="", alias="receiverPostalCode")
    receiver_country_code: str = Field(default="", alias="receiverCountryCode")
    receiver_po_number: str = Field(default="", alias="receiverPoNumber")
    shipper_company_prefix: str = Field(default="", alias="shipperCompanyPrefix")
    shipper_gln: str = Field(default="", alias="shipperGln")
    shipper_sgln: str = Field(default="", alias="shipperSgln")
    shipper_name: str = Field(default="", alias="shipperName")
    shipper_street_address: str = Field(default="", alias="shipperStreetAddress")
    shipper_city: str = Field(default="", alias="shipperCity")
    shipper_state: str = Field(default="", alias="shipperState")
    shipper_postal_code: str = Field(default="", alias="shipperPostalCode")
    shipper_country_code: str = Field(default="", alias="shipperCountryCode")
    shipper_same_as_sender: bool = Field(default=False, alias="shipperSameAsSender")
    # EPCClass data
    product_ndc: str = Field(default="", alias="productNdc")
    package_ndc: str = Field(default="", alias="packageNdc")
    regulated_product_name: str = Field(default="", alias="regulatedProductName")
    manufacturer_name: str = Field(default="", alias="manufacturerName")
    dosage_form_type: str = Field(default="", alias="dosageFormType")
    strength_description: str = Field(default="", alias="strengthDescription")
    net_content_description: str = Field(default="", alias="netContentDescription")

class SerialNumbers(BaseModel):
    model_config = {"populate_by_name": True}
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    configuration_id: str = Field(alias="configurationId")
    sscc_serial_numbers: List[str] = Field(alias="ssccSerialNumbers")
    case_serial_numbers: List[str] = Field(alias="caseSerialNumbers")
    inner_case_serial_numbers: List[str] = Field(default_factory=list, alias="innerCaseSerialNumbers")
    item_serial_numbers: List[str] = Field(alias="itemSerialNumbers")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SerialNumbersCreate(BaseModel):
    model_config = {"populate_by_name": True}
    
    configuration_id: str = Field(alias="configurationId")
    sscc_serial_numbers: List[str] = Field(alias="ssccSerialNumbers")
    case_serial_numbers: List[str] = Field(alias="caseSerialNumbers")
    inner_case_serial_numbers: List[str] = Field(default_factory=list, alias="innerCaseSerialNumbers")
    item_serial_numbers: List[str] = Field(alias="itemSerialNumbers")

class EPCISGenerationRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    configuration_id: str = Field(alias="configurationId")
    read_point: str = Field(default="urn:epc:id:sgln:1234567.00000.0", alias="readPoint")
    biz_location: str = Field(default="urn:epc:id:sgln:1234567.00001.0", alias="bizLocation")

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "EPCIS Serial Number Aggregation API"}

# Authentication middleware
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    token_data = verify_token(token)
    user = await get_user_by_email(token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Authentication endpoints
@api_router.post("/auth/register", response_model=User)
async def register(user: UserCreate):
    """Register a new user"""
    return await create_user(user)

@api_router.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    """Login user"""
    authenticated_user = await authenticate_user(user.email, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@api_router.post("/auth/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}

@api_router.post("/configuration", response_model=SerialConfiguration)
async def create_configuration(input: SerialConfigurationCreate):
    config_dict = input.model_dump(by_alias=False)  # This gives us snake_case
    config_obj = SerialConfiguration(**config_dict)
    await db.configurations.insert_one(config_obj.model_dump(by_alias=False))
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
    
    serial_dict = input.model_dump(by_alias=False)
    serial_obj = SerialNumbers(**serial_dict)
    await db.serial_numbers.insert_one(serial_obj.model_dump(by_alias=False))
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
    
    # Generate filename based on new naming convention
    sender_gln = config.get("sender_gln", config.get("senderGln", ""))
    receiver_gln = config.get("receiver_gln", config.get("receiverGln", ""))
    today_date = datetime.now(timezone.utc).strftime("%y%m%d")
    
    # Create filename: "epcis"-{senderGLN}-{receiverGLN}-{YYMMDD}
    # If GLN values are empty, use default fallback
    if not sender_gln or not receiver_gln:
        filename = f"epcis-{today_date}.xml"
    else:
        filename = f"epcis-{sender_gln}-{receiver_gln}-{today_date}.xml"
    
    # Return as downloadable file
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
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
    """Generate GS1 EPCIS 1.2 XML with SBDH for pharmaceutical aggregation"""
    
    # Initialize base timestamp and counter for incremental timestamps
    base_timestamp = datetime.now(timezone.utc)
    timestamp_counter = 0
    
    # Helper function to get next incremental timestamp
    def get_next_timestamp():
        nonlocal timestamp_counter
        current_timestamp = base_timestamp + timedelta(seconds=timestamp_counter)
        timestamp_counter += 1
        return current_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Helper function to get final timestamp for SBDH (after all events)
    def get_final_timestamp():
        final_timestamp = base_timestamp + timedelta(seconds=timestamp_counter)
        return final_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Helper function to format datetime in XML Schema format with Z suffix
    def format_xml_datetime():
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Create root element as EPCISDocument (not StandardBusinessDocument)
    root = ET.Element("epcis:EPCISDocument")
    root.set("xmlns", "urn:epcglobal:epcis:xsd:1")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xmlns:gs1ushc", "http://epcis.gs1us.org/hc/ns")
    root.set("schemaVersion", "1.2")
    root.set("creationDate", get_next_timestamp())
    
    # Create EPCISHeader
    epcis_header = ET.SubElement(root, "EPCISHeader")
    
    # Add SBDH namespaces to the root element
    root.set("xmlns:sbdh", "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader")
    root.set("xmlns:cbvmda", "urn:epcglobal:cbv:mda")
    
    # Create SBDH Header directly under EPCISHeader (no StandardBusinessDocument wrapper)
    sbdh = ET.SubElement(epcis_header, "sbdh:StandardBusinessDocumentHeader")
    
    # Header Version
    header_version = ET.SubElement(sbdh, "sbdh:HeaderVersion")
    header_version.text = "1.0"
    
    # Sender
    sender = ET.SubElement(sbdh, "sbdh:Sender")
    sender_identifier = ET.SubElement(sender, "sbdh:Identifier")
    sender_identifier.set("Authority", "GS1")
    sender_identifier.text = config.get("sender_gln", "")
    
    # Receiver
    receiver = ET.SubElement(sbdh, "sbdh:Receiver")
    receiver_identifier = ET.SubElement(receiver, "sbdh:Identifier")
    receiver_identifier.set("Authority", "GS1")
    receiver_identifier.text = config.get("receiver_gln", "")
    
    # Document Identification
    doc_identification = ET.SubElement(sbdh, "sbdh:DocumentIdentification")
    standard = ET.SubElement(doc_identification, "sbdh:Standard")
    standard.text = "EPCglobal"
    type_version = ET.SubElement(doc_identification, "sbdh:TypeVersion")
    type_version.text = "1.0"
    instance_identifier = ET.SubElement(doc_identification, "sbdh:InstanceIdentifier")
    instance_identifier.text = f"EPCIS_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    type_element = ET.SubElement(doc_identification, "sbdh:Type")
    type_element.text = "Events"
    creation_date_time = ET.SubElement(doc_identification, "sbdh:CreationDateAndTime")
    # Will be set to final timestamp at the end of function
    
    # Add extension element containing EPCISMasterData directly under EPCISHeader
    extension = ET.SubElement(epcis_header, "extension")
    epcis_master_data = ET.SubElement(extension, "EPCISMasterData")
    vocabulary_list = ET.SubElement(epcis_master_data, "VocabularyList")
    
    # Add EPCClass vocabulary
    vocabulary = ET.SubElement(vocabulary_list, "Vocabulary")
    vocabulary.set("type", "urn:epcglobal:epcis:vtype:EPCClass")
    
    vocabulary_element_list = ET.SubElement(vocabulary, "VocabularyElementList")
    
    # Get configuration parameters
    company_prefix = config["company_prefix"]
    shipper_company_prefix = config.get("shipper_company_prefix", company_prefix)  # Use shipper's company prefix for SSCCs
    item_product_code = config["item_product_code"]
    case_product_code = config["case_product_code"]
    inner_case_product_code = config.get("inner_case_product_code", "")
    item_indicator_digit = config["item_indicator_digit"]
    case_indicator_digit = config["case_indicator_digit"]
    inner_case_indicator_digit = config.get("inner_case_indicator_digit", "")
    use_inner_cases = config["use_inner_cases"]
    cases_per_sscc = config["cases_per_sscc"]
    
    # Helper function to add EPCClass attributes
    def add_epcclass_attributes(vocab_element, config):
        if config.get("package_ndc"):
            # Strip hyphens from package_ndc for EPCIS XML
            clean_package_ndc = config["package_ndc"].replace("-", "")
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentification")
            attr.text = clean_package_ndc
            
            attr_type = ET.SubElement(vocab_element, "attribute")
            attr_type.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentificationTypeCode")
            attr_type.text = "FDA_NDC_11"
        
        if config.get("regulated_product_name"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#regulatedProductName")
            attr.text = config["regulated_product_name"]
        
        if config.get("manufacturer_name"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName")
            attr.text = config["manufacturer_name"]
        
        if config.get("dosage_form_type"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#dosageFormType")
            attr.text = config["dosage_form_type"]
        
        if config.get("strength_description"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#strengthDescription")
            attr.text = config["strength_description"]
        
        if config.get("net_content_description"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#netContentDescription")
            attr.text = config["net_content_description"]
    
    # Create EPCClass vocabulary elements for each packaging level
    # Order: Item → Inner Case → Case
    
    # 1. Item Level EPCClass (always present)
    item_epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}.*"
    item_vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
    item_vocabulary_element.set("id", item_epc_pattern)
    add_epcclass_attributes(item_vocabulary_element, config)
    
    # 2. Inner Case Level EPCClass (if inner cases are used)
    if use_inner_cases and inner_case_product_code and inner_case_indicator_digit:
        inner_case_epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{inner_case_indicator_digit}{inner_case_product_code}.*"
        inner_case_vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
        inner_case_vocabulary_element.set("id", inner_case_epc_pattern)
        add_epcclass_attributes(inner_case_vocabulary_element, config)
    
    # 3. Case Level EPCClass (if cases are used)
    if cases_per_sscc > 0:
        case_epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}.*"
        case_vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
        case_vocabulary_element.set("id", case_epc_pattern)
        add_epcclass_attributes(case_vocabulary_element, config)
    
    # Add Location vocabulary
    location_vocabulary = ET.SubElement(vocabulary_list, "Vocabulary")
    location_vocabulary.set("type", "urn:epcglobal:epcis:vtype:Location")
    
    location_vocabulary_element_list = ET.SubElement(location_vocabulary, "VocabularyElementList")
    
    # Add location vocabulary elements for sender, receiver, and shipper
    for role, prefix in [("sender", "sender"), ("receiver", "receiver"), ("shipper", "shipper")]:
        gln = config.get(f"{prefix}_gln", "")
        sgln = config.get(f"{prefix}_sgln", "")
        name = config.get(f"{prefix}_name", "")
        street_address = config.get(f"{prefix}_street_address", "")
        city = config.get(f"{prefix}_city", "")
        state = config.get(f"{prefix}_state", "")
        postal_code = config.get(f"{prefix}_postal_code", "")
        country_code = config.get(f"{prefix}_country_code", "")
        
        if sgln:
            # Add SGLN location element (using SGLN instead of GLN)
            loc_element = ET.SubElement(location_vocabulary_element_list, "VocabularyElement")
            loc_element.set("id", f"urn:epc:id:sgln:{sgln}")
            
            # Add name attribute
            if name:
                name_attr = ET.SubElement(loc_element, "attribute")
                name_attr.set("id", "urn:epcglobal:cbv:mda#name")
                name_attr.text = name
            
            # Add street address attribute
            if street_address:
                street_attr = ET.SubElement(loc_element, "attribute")
                street_attr.set("id", "urn:epcglobal:cbv:mda#streetAddressOne")
                street_attr.text = street_address
            
            # Add city attribute
            if city:
                city_attr = ET.SubElement(loc_element, "attribute")
                city_attr.set("id", "urn:epcglobal:cbv:mda#city")
                city_attr.text = city
            
            # Add state attribute
            if state:
                state_attr = ET.SubElement(loc_element, "attribute")
                state_attr.set("id", "urn:epcglobal:cbv:mda#state")
                state_attr.text = state
            
            # Add postal code attribute
            if postal_code:
                postal_attr = ET.SubElement(loc_element, "attribute")
                postal_attr.set("id", "urn:epcglobal:cbv:mda#postalCode")
                postal_attr.text = postal_code
            
            # Add country code attribute
            if country_code:
                country_attr = ET.SubElement(loc_element, "attribute")
                country_attr.set("id", "urn:epcglobal:cbv:mda#countryCode")
                country_attr.text = country_code
    
    # Add gs1ushc:dscsaTransactionStatement before EPCISHeader closes
    dscsa_statement = ET.SubElement(epcis_header, "gs1ushc:dscsaTransactionStatement")
    
    affirm_statement = ET.SubElement(dscsa_statement, "gs1ushc:affirmTransactionStatement")
    affirm_statement.text = "true"
    
    legal_notice = ET.SubElement(dscsa_statement, "gs1ushc:legalNotice")
    legal_notice.text = "Seller has complied with each applicable subsection of FDCA Sec. 581(27)(A)-(G)."
    
    # Create EPCISBody
    epcis_body = ET.SubElement(root, "EPCISBody")
    event_list = ET.SubElement(epcis_body, "EventList")
    
    # Get additional configuration parameters
    lot_number = config.get("lot_number", "")
    expiration_date = config.get("expiration_date", "")
    sscc_indicator_digit = config["sscc_indicator_digit"]
    number_of_sscc = config["number_of_sscc"]
    
    # Use shipper SGLN for readPoint and bizLocation
    shipper_sgln = config.get("shipper_sgln", "")
    if shipper_sgln:
        read_point = f"urn:epc:id:sgln:{shipper_sgln}"
        biz_location = f"urn:epc:id:sgln:{shipper_sgln}"
    else:
        # Fallback to provided values if no shipper SGLN
        read_point = read_point
        biz_location = biz_location
    
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
    
    # Generate SSCC EPCs using shipper's company prefix
    for sscc_serial in sscc_serials:
        sscc_epc = f"urn:epc:id:sscc:{config['shipper_company_prefix']}.{sscc_indicator_digit}{sscc_serial}"
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
        event_time.text = get_next_timestamp()
        
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
        event_time.text = get_next_timestamp()
        
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
        event_time.text = get_next_timestamp()
        
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
        event_time.text = get_next_timestamp()
        
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
            event_time.text = get_next_timestamp()
            
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
            event_time.text = get_next_timestamp()
            
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
            event_time.text = get_next_timestamp()
            
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
            event_time.text = get_next_timestamp()
            
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
            event_time.text = get_next_timestamp()
            
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
    
    # 7. Shipping ObjectEvent (last event per GS1 Rx EPCIS guidelines)
    shipping_event = ET.SubElement(event_list, "ObjectEvent")
    
    event_time = ET.SubElement(shipping_event, "eventTime")
    event_time.text = get_next_timestamp()
    
    event_timezone = ET.SubElement(shipping_event, "eventTimeZoneOffset")
    event_timezone.text = "+00:00"
    
    # Add all SSCCs to the shipping event
    epc_list = ET.SubElement(shipping_event, "epcList")
    for sscc_epc in sscc_epcs:
        epc = ET.SubElement(epc_list, "epc")
        epc.text = sscc_epc
    
    action = ET.SubElement(shipping_event, "action")
    action.text = "OBSERVE"
    
    biz_step = ET.SubElement(shipping_event, "bizStep")
    biz_step.text = "urn:epcglobal:cbv:bizstep:shipping"
    
    disposition = ET.SubElement(shipping_event, "disposition")
    disposition.text = "urn:epcglobal:cbv:disp:in_transit"
    
    read_point_elem = ET.SubElement(shipping_event, "readPoint")
    read_point_id = ET.SubElement(read_point_elem, "id")
    read_point_id.text = read_point
    
    # Add bizTransactionList with PO and Despatch Advice information
    biz_transaction_list = ET.SubElement(shipping_event, "bizTransactionList")
    
    # Purchase Order transaction
    receiver_gln = config.get("receiver_gln", "")
    receiver_po_number = config.get("receiver_po_number", "")
    if receiver_gln and receiver_po_number:
        po_transaction = ET.SubElement(biz_transaction_list, "bizTransaction")
        po_transaction.set("type", "urn:epcglobal:cbv:btt:po")
        po_transaction.text = f"urn:epcglobal:cbv:bt:{receiver_gln}:{receiver_po_number}"
    
    # Despatch Advice transaction
    sender_gln = config.get("sender_gln", "")
    sender_despatch_advice_number = config.get("sender_despatch_advice_number", "")
    if sender_gln and sender_despatch_advice_number:
        desadv_transaction = ET.SubElement(biz_transaction_list, "bizTransaction")
        desadv_transaction.set("type", "urn:epcglobal:cbv:btt:desadv")
        desadv_transaction.text = f"urn:epcglobal:cbv:bt:{sender_gln}:{sender_despatch_advice_number}"
    
    # Add extension with sourceList and destinationList
    extension = ET.SubElement(shipping_event, "extension")
    
    # Source list (sender information)
    source_list = ET.SubElement(extension, "sourceList")
    sender_sgln = config.get("sender_sgln", "")
    shipper_sgln = config.get("shipper_sgln", "")
    if sender_sgln:
        # owning_party source (uses sender SGLN)
        source_owning = ET.SubElement(source_list, "source")
        source_owning.set("type", "urn:epcglobal:cbv:sdt:owning_party")
        source_owning.text = f"urn:epc:id:sgln:{sender_sgln}"
        
        # location source (uses shipper SGLN)
        source_location = ET.SubElement(source_list, "source")
        source_location.set("type", "urn:epcglobal:cbv:sdt:location")
        source_location.text = f"urn:epc:id:sgln:{shipper_sgln}"
    
    # Destination list (receiver information)
    destination_list = ET.SubElement(extension, "destinationList")
    receiver_sgln = config.get("receiver_sgln", "")
    if receiver_sgln:
        # owning_party destination
        dest_owning = ET.SubElement(destination_list, "destination")
        dest_owning.set("type", "urn:epcglobal:cbv:sdt:owning_party")
        dest_owning.text = f"urn:epc:id:sgln:{receiver_sgln}"
        
        # location destination
        dest_location = ET.SubElement(destination_list, "destination")
        dest_location.set("type", "urn:epcglobal:cbv:sdt:location")
        dest_location.text = f"urn:epc:id:sgln:{receiver_sgln}"
    
    # Update SBDH CreationDateAndTime to be the final timestamp (after all events)
    creation_date_time.text = get_final_timestamp()
    
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
    expose_headers=["Content-Disposition"],
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