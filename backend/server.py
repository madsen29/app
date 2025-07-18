from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
import jwt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Authentication configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Authentication models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    # Receiver Information fields as user defaults
    company_name: str = Field(default="", alias="companyName")
    street_address: str = Field(default="", alias="streetAddress")
    city: str = Field(default="", alias="city")
    state: str = Field(default="", alias="state")
    postal_code: str = Field(default="", alias="postalCode")
    country_code: str = Field(default="", alias="countryCode")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    street_address: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country_code: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    email: Optional[EmailStr] = None
    company_name: Optional[str] = Field(None, alias="companyName")
    street_address: Optional[str] = Field(None, alias="streetAddress")
    city: Optional[str] = Field(None, alias="city")
    state: Optional[str] = Field(None, alias="state")
    postal_code: Optional[str] = Field(None, alias="postalCode")
    country_code: Optional[str] = Field(None, alias="countryCode")

class PasswordUpdate(BaseModel):
    current_password: str = Field(alias="currentPassword")
    new_password: str = Field(alias="newPassword")

# Project Management Models
class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    user_id: str
    status: str = "In Progress"  # "In Progress", "Completed"
    current_step: int = 1
    configuration: Optional[dict] = None
    serial_numbers: Optional[list] = None  # Allow list for hierarchical structure
    epcis_file_content: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectCreate(BaseModel):
    name: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    current_step: Optional[int] = None
    configuration: Optional[dict] = None
    serial_numbers: Optional[list] = None  # Allow list for hierarchical structure
    epcis_file_content: Optional[str] = None

# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email from database"""
    user_data = await db.users.find_one({"email": email})
    if user_data:
        return User(**user_data)
    return None

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user_data = await db.users.find_one({"email": email})
    if not user_data:
        return None
    if not verify_password(password, user_data["hashed_password"]):
        return None
    return User(**user_data)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

async def create_user(user: UserCreate) -> User:
    """Create a new user"""
    # Check if user already exists
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_data = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "company_name": user.company_name,
        "street_address": user.street_address,
        "city": user.city,
        "state": user.state,
        "postal_code": user.postal_code,
        "country_code": user.country_code,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_data)
    
    # Return user without password
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})

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
    sscc_serial_numbers: List[str] = Field(alias="ssccSerialNumbers")
    case_serial_numbers: List[str] = Field(alias="caseSerialNumbers")
    inner_case_serial_numbers: List[str] = Field(default_factory=list, alias="innerCaseSerialNumbers")
    item_serial_numbers: List[str] = Field(alias="itemSerialNumbers")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SerialNumbersCreate(BaseModel):
    model_config = {"populate_by_name": True}
    
    sscc_serial_numbers: List[str] = Field(alias="ssccSerialNumbers")
    case_serial_numbers: List[str] = Field(alias="caseSerialNumbers")
    inner_case_serial_numbers: List[str] = Field(default_factory=list, alias="innerCaseSerialNumbers")
    item_serial_numbers: List[str] = Field(alias="itemSerialNumbers")

class EPCISGenerationRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
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

@api_router.put("/auth/profile", response_model=User)
async def update_user_profile(user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    """Update user profile information"""
    # Create update dictionary with only non-None values
    update_data = {}
    if user_update.first_name is not None:
        update_data["first_name"] = user_update.first_name
    if user_update.last_name is not None:
        update_data["last_name"] = user_update.last_name
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_user = await db.users.find_one({"email": user_update.email, "id": {"$ne": current_user.id}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        update_data["email"] = user_update.email
    if user_update.company_name is not None:
        update_data["company_name"] = user_update.company_name
    if user_update.street_address is not None:
        update_data["street_address"] = user_update.street_address
    if user_update.city is not None:
        update_data["city"] = user_update.city
    if user_update.state is not None:
        update_data["state"] = user_update.state
    if user_update.postal_code is not None:
        update_data["postal_code"] = user_update.postal_code
    if user_update.country_code is not None:
        update_data["country_code"] = user_update.country_code
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Update user in database
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": update_data}
    )
    
    # Return updated user
    updated_user = await db.users.find_one({"id": current_user.id})
    return User(**updated_user)

@api_router.put("/auth/password")
async def update_user_password(password_update: PasswordUpdate, current_user: User = Depends(get_current_user)):
    """Update user password"""
    # Get current user with password
    user_doc = await db.users.find_one({"id": current_user.id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_update.current_password, user_doc["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password
    hashed_password = get_password_hash(password_update.new_password)
    
    # Update password in database
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    return {"message": "Password updated successfully"}

# Project Management endpoints
@api_router.get("/projects", response_model=List[Project])
async def get_user_projects(current_user: User = Depends(get_current_user)):
    """Get all projects for the current user"""
    projects = await db.projects.find({"user_id": current_user.id}).to_list(1000)
    
    # Convert projects and handle data format migration
    converted_projects = []
    for project in projects:
        # Handle serial_numbers format migration (dict -> list)
        if project.get("serial_numbers") is not None:
            if isinstance(project["serial_numbers"], dict):
                # Convert old format to new format or set to None
                project["serial_numbers"] = None
        
        converted_projects.append(Project(**project))
    
    return converted_projects

@api_router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate, current_user: User = Depends(get_current_user)):
    """Create a new project"""
    project_data = {
        "id": str(uuid.uuid4()),
        "name": project.name,
        "user_id": current_user.id,
        "status": "In Progress",
        "current_step": 1,
        "configuration": None,
        "serial_numbers": None,
        "epcis_file_content": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.projects.insert_one(project_data)
    return Project(**project_data)

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific project"""
    project = await db.projects.find_one({"id": project_id, "user_id": current_user.id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Handle serial_numbers format migration (dict -> list)
    if project.get("serial_numbers") is not None:
        if isinstance(project["serial_numbers"], dict):
            # Convert old format to new format or set to None
            project["serial_numbers"] = None
    
    return Project(**project)

@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_update: ProjectUpdate, current_user: User = Depends(get_current_user)):
    """Update a project"""
    project = await db.projects.find_one({"id": project_id, "user_id": current_user.id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.projects.update_one(
        {"id": project_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    updated_project = await db.projects.find_one({"id": project_id, "user_id": current_user.id})
    
    # Handle serial_numbers format migration (dict -> list)
    if updated_project.get("serial_numbers") is not None:
        if isinstance(updated_project["serial_numbers"], dict):
            # Convert old format to new format or set to None
            updated_project["serial_numbers"] = None
    
    return Project(**updated_project)

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Delete a project"""
    result = await db.projects.delete_one({"id": project_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}

@api_router.post("/projects/{project_id}/duplicate", response_model=Project)
async def duplicate_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Duplicate a project"""
    project = await db.projects.find_one({"id": project_id, "user_id": current_user.id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create new project with copied data
    new_project_data = {
        "id": str(uuid.uuid4()),
        "name": f"{project['name']} (Copy)",
        "user_id": current_user.id,
        "status": "In Progress",
        "current_step": 1,
        "configuration": project.get("configuration"),
        "serial_numbers": None,  # Don't copy serial numbers
        "epcis_file_content": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.projects.insert_one(new_project_data)
    return Project(**new_project_data)

@api_router.post("/projects/{project_id}/configuration", response_model=SerialConfiguration)
async def create_configuration(project_id: str, input: SerialConfigurationCreate, current_user: User = Depends(get_current_user)):
    """Create configuration for a project"""
    # Verify project exists and belongs to user
    project = await db.projects.find_one({"id": project_id, "user_id": current_user.id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    config_dict = input.model_dump(by_alias=False)  # This gives us snake_case
    config_obj = SerialConfiguration(**config_dict)
    config_data = config_obj.model_dump(by_alias=False)
    
    # Save configuration to project
    await db.projects.update_one(
        {"id": project_id, "user_id": current_user.id},
        {"$set": {
            "configuration": config_data,
            "current_step": 2,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return config_obj

@api_router.get("/configuration", response_model=List[SerialConfiguration])
async def get_configurations():
    configurations = await db.configurations.find().to_list(1000)
    return [SerialConfiguration(**config) for config in configurations]

@api_router.post("/projects/{project_id}/serial-numbers", response_model=SerialNumbers)
async def create_serial_numbers(project_id: str, input: SerialNumbersCreate, current_user: User = Depends(get_current_user)):
    """Create serial numbers for a project"""
    # Verify project exists and belongs to user
    project = await db.projects.find_one({"id": project_id, "user_id": current_user.id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get configuration from project
    config = project.get("configuration")
    if not config:
        raise HTTPException(status_code=400, detail="Project configuration not found")
    
    # Handle both camelCase and snake_case keys
    def get_config_value(key_snake, key_camel):
        return config.get(key_snake, config.get(key_camel, 0))
    
    # Calculate expected quantities based on configuration
    cases_per_sscc = get_config_value("cases_per_sscc", "casesPerSscc")
    
    # If no cases, items go directly in SSCC
    if cases_per_sscc == 0:
        total_cases = 0
        total_inner_cases = 0
        total_items = get_config_value("items_per_case", "itemsPerCase") * get_config_value("number_of_sscc", "numberOfSscc")
    else:
        total_cases = cases_per_sscc * get_config_value("number_of_sscc", "numberOfSscc")
        
        if get_config_value("use_inner_cases", "useInnerCases"):
            total_inner_cases = get_config_value("inner_cases_per_case", "innerCasesPerCase") * total_cases
            total_items = get_config_value("items_per_inner_case", "itemsPerInnerCase") * total_inner_cases
        else:
            total_inner_cases = 0
            total_items = get_config_value("items_per_case", "itemsPerCase") * total_cases
    
    # Validate serial numbers count
    if len(input.sscc_serial_numbers) != get_config_value("number_of_sscc", "numberOfSscc"):
        raise HTTPException(
            status_code=400, 
            detail=f"Expected {get_config_value('number_of_sscc', 'numberOfSscc')} SSCC serial numbers, got {len(input.sscc_serial_numbers)}"
        )
    
    if len(input.case_serial_numbers) != total_cases:
        raise HTTPException(
            status_code=400, 
            detail=f"Expected {total_cases} case serial numbers, got {len(input.case_serial_numbers)}"
        )
    
    if get_config_value("use_inner_cases", "useInnerCases") and cases_per_sscc > 0:
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
    
    # Save serial numbers to project as a list structure for hierarchical data
    serial_numbers_list = []
    
    # Add SSCC serials
    for sscc_serial in serial_obj.sscc_serial_numbers:
        serial_numbers_list.append({
            "type": "sscc",
            "serial": sscc_serial
        })
    
    # Add case serials
    for case_serial in serial_obj.case_serial_numbers:
        serial_numbers_list.append({
            "type": "case", 
            "serial": case_serial
        })
    
    # Add inner case serials
    for inner_case_serial in serial_obj.inner_case_serial_numbers:
        serial_numbers_list.append({
            "type": "inner_case",
            "serial": inner_case_serial
        })
    
    # Add item serials
    for item_serial in serial_obj.item_serial_numbers:
        serial_numbers_list.append({
            "type": "item",
            "serial": item_serial
        })
    
    await db.projects.update_one(
        {"id": project_id, "user_id": current_user.id},
        {"$set": {
            "serial_numbers": serial_numbers_list,
            "current_step": 3,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return serial_obj

@api_router.get("/serial-numbers/{configuration_id}", response_model=SerialNumbers)
async def get_serial_numbers(configuration_id: str):
    serial_numbers = await db.serial_numbers.find_one({"configuration_id": configuration_id})
    if not serial_numbers:
        raise HTTPException(status_code=404, detail="Serial numbers not found")
    return SerialNumbers(**serial_numbers)

@api_router.post("/projects/{project_id}/generate-epcis")
async def generate_epcis(project_id: str, request: EPCISGenerationRequest, current_user: User = Depends(get_current_user)):
    """Generate EPCIS file for a project"""
    # Verify project exists and belongs to user
    project = await db.projects.find_one({"id": project_id, "user_id": current_user.id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get configuration and serial numbers from project
    config = project.get("configuration")
    if not config:
        raise HTTPException(status_code=400, detail="Project configuration not found")
    
    serial_numbers = project.get("serial_numbers")
    if not serial_numbers:
        raise HTTPException(status_code=400, detail="Project serial numbers not found")
    
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
    
    # Save EPCIS file content to project and mark as completed
    await db.projects.update_one(
        {"id": project_id, "user_id": current_user.id},
        {"$set": {
            "epcis_file_content": xml_content,
            "status": "Completed",
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Return as downloadable file
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/projects/{project_id}/download-epcis")
async def download_epcis(project_id: str, current_user: User = Depends(get_current_user)):
    """Download completed EPCIS file for a project"""
    project = await db.projects.find_one({"id": project_id, "user_id": current_user.id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.get("status") != "Completed":
        raise HTTPException(status_code=400, detail="Project is not completed")
    
    epcis_content = project.get("epcis_file_content")
    if not epcis_content:
        raise HTTPException(status_code=404, detail="EPCIS file not found")
    
    # Generate filename
    config = project.get("configuration", {})
    sender_gln = config.get("sender_gln", config.get("senderGln", ""))
    receiver_gln = config.get("receiver_gln", config.get("receiverGln", ""))
    today_date = datetime.now(timezone.utc).strftime("%y%m%d")
    
    if not sender_gln or not receiver_gln:
        filename = f"epcis-{today_date}.xml"
    else:
        filename = f"epcis-{sender_gln}-{receiver_gln}-{today_date}.xml"
    
    return Response(
        content=epcis_content,
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
    
    # Helper function to handle both camelCase and snake_case keys
    def get_config_value(key_snake, key_camel, default=None):
        return config.get(key_snake, config.get(key_camel, default))
    
    # Create root element as EPCISDocument (not StandardBusinessDocument)
    root = ET.Element("epcis:EPCISDocument")
    root.set("xmlns:epcis", "urn:epcglobal:epcis:xsd:1")
    root.set("xmlns", "urn:epcglobal:epcis:xsd:1")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xmlns:gs1ushc", "http://epcis.gs1us.org/hc/ns")
    root.set("schemaVersion", "1.2")
    root.set("creationDate", get_next_timestamp())
    
    # Create EPCISHeader
    epcis_header = ET.SubElement(root, "EPCISHeader")
    
    # Add SBDH namespaces to the root element
    root.set("xmlns:sbdh", "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader")
    # Note: cbvmda namespace is already registered globally via ET.register_namespace
    
    # Create SBDH Header directly under EPCISHeader (no StandardBusinessDocument wrapper)
    sbdh = ET.SubElement(epcis_header, "sbdh:StandardBusinessDocumentHeader")
    
    # Header Version
    header_version = ET.SubElement(sbdh, "sbdh:HeaderVersion")
    header_version.text = "1.0"
    
    # Sender
    sender = ET.SubElement(sbdh, "sbdh:Sender")
    sender_identifier = ET.SubElement(sender, "sbdh:Identifier")
    sender_identifier.set("Authority", "GS1")
    sender_identifier.text = get_config_value("sender_gln", "senderGln", "")
    
    # Receiver
    receiver = ET.SubElement(sbdh, "sbdh:Receiver")
    receiver_identifier = ET.SubElement(receiver, "sbdh:Identifier")
    receiver_identifier.set("Authority", "GS1")
    receiver_identifier.text = get_config_value("receiver_gln", "receiverGln", "")
    
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
    company_prefix = get_config_value("company_prefix", "companyPrefix")
    shipper_company_prefix = get_config_value("shipper_company_prefix", "shipperCompanyPrefix") or company_prefix  # Use shipper's company prefix for SSCCs
    item_product_code = get_config_value("item_product_code", "itemProductCode")
    case_product_code = get_config_value("case_product_code", "caseProductCode")
    inner_case_product_code = get_config_value("inner_case_product_code", "innerCaseProductCode", "")
    item_indicator_digit = get_config_value("item_indicator_digit", "itemIndicatorDigit")
    case_indicator_digit = get_config_value("case_indicator_digit", "caseIndicatorDigit")
    inner_case_indicator_digit = get_config_value("inner_case_indicator_digit", "innerCaseIndicatorDigit", "")
    use_inner_cases = get_config_value("use_inner_cases", "useInnerCases")
    cases_per_sscc = get_config_value("cases_per_sscc", "casesPerSscc")
    
    # Helper function to add EPCClass attributes
    def add_epcclass_attributes(vocab_element, config):
        if get_config_value("package_ndc", "packageNdc"):
            # Strip hyphens from package_ndc for EPCIS XML
            clean_package_ndc = get_config_value("package_ndc", "packageNdc").replace("-", "")
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentification")
            attr.text = clean_package_ndc
            
            attr_type = ET.SubElement(vocab_element, "attribute")
            attr_type.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentificationTypeCode")
            attr_type.text = "FDA_NDC_11"
        
        if get_config_value("regulated_product_name", "regulatedProductName"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#regulatedProductName")
            attr.text = get_config_value("regulated_product_name", "regulatedProductName")
        
        if get_config_value("manufacturer_name", "manufacturerName"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName")
            attr.text = get_config_value("manufacturer_name", "manufacturerName")
        
        if get_config_value("dosage_form_type", "dosageFormType"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#dosageFormType")
            attr.text = get_config_value("dosage_form_type", "dosageFormType")
        
        if get_config_value("strength_description", "strengthDescription"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#strengthDescription")
            attr.text = get_config_value("strength_description", "strengthDescription")
        
        if get_config_value("net_content_description", "netContentDescription"):
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#netContentDescription")
            attr.text = get_config_value("net_content_description", "netContentDescription")
    
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
        gln = get_config_value(f"{prefix}_gln", f"{prefix}Gln", "")
        sgln = get_config_value(f"{prefix}_sgln", f"{prefix}Sgln", "")
        name = get_config_value(f"{prefix}_name", f"{prefix}Name", "")
        street_address = get_config_value(f"{prefix}_street_address", f"{prefix}StreetAddress", "")
        city = get_config_value(f"{prefix}_city", f"{prefix}City", "")
        state = get_config_value(f"{prefix}_state", f"{prefix}State", "")
        postal_code = get_config_value(f"{prefix}_postal_code", f"{prefix}PostalCode", "")
        country_code = get_config_value(f"{prefix}_country_code", f"{prefix}CountryCode", "")
        
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
    lot_number = get_config_value("lot_number", "lotNumber", "")
    expiration_date = get_config_value("expiration_date", "expirationDate", "")
    sscc_indicator_digit = get_config_value("sscc_indicator_digit", "ssccIndicatorDigit")
    number_of_sscc = get_config_value("number_of_sscc", "numberOfSscc")
    
    # Use shipper SGLN for readPoint and bizLocation
    shipper_sgln = get_config_value("shipper_sgln", "shipperSgln", "")
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
        items_per_sscc = get_config_value("items_per_case", "itemsPerCase")  # In this case, items_per_case means items_per_sscc
    elif use_inner_cases:
        inner_cases_per_case = get_config_value("inner_cases_per_case", "innerCasesPerCase")
        items_per_inner_case = get_config_value("items_per_inner_case", "itemsPerInnerCase")
    else:
        items_per_case = get_config_value("items_per_case", "itemsPerCase")
    
    # Get serial numbers from the new list format
    sscc_serials = []
    case_serials = []
    inner_case_serials = []
    item_serials = []
    
    for serial_entry in serial_numbers:
        if serial_entry["type"] == "sscc":
            sscc_serials.append(serial_entry["serial"])
        elif serial_entry["type"] == "case":
            case_serials.append(serial_entry["serial"])
        elif serial_entry["type"] == "inner_case":
            inner_case_serials.append(serial_entry["serial"])
        elif serial_entry["type"] == "item":
            item_serials.append(serial_entry["serial"])
    
    # Generate proper EPC identifiers
    sscc_epcs = []
    case_epcs = []
    inner_case_epcs = []
    item_epcs = []
    
    # Generate SSCC EPCs using shipper's company prefix
    for sscc_serial in sscc_serials:
        sscc_epc = f"urn:epc:id:sscc:{shipper_company_prefix}.{sscc_indicator_digit}{sscc_serial}"
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
    allow_origins=["*", "https://72fab16c-c7e1-4095-8101-1dff788bbfa2.preview.emergentagent.com"],
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