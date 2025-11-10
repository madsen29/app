from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
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
ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60  # 8 hours for collaborative work

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Authentication models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    is_active: bool = True
    is_super_admin: bool = False
    status: str = "pending"  # pending, active, inactive
    approved_by: Optional[str] = None  # Admin ID who approved
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    email: Optional[EmailStr] = None

class PasswordUpdate(BaseModel):
    current_password: str = Field(alias="currentPassword")
    new_password: str = Field(alias="newPassword")

# Admin models
class AdminUserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    email: Optional[EmailStr] = None
    status: Optional[str] = None  # pending, active, inactive
    is_super_admin: Optional[bool] = Field(None, alias="isSuperAdmin")

class AdminPasswordReset(BaseModel):
    new_password: str = Field(alias="newPassword")

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class CreateAdminUser(BaseModel):
    email: EmailStr
    password: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")

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
    product_serials: Optional[list] = None  # Multi-product serial numbers
    epcis_file_content: Optional[str] = None

# Location model for saved locations
class LocationCreate(BaseModel):
    name: str
    company_prefix: str = Field(default="", alias="companyPrefix")
    gln: str = Field(default="", alias="gln")
    sgln: str = Field(default="", alias="sgln")
    company_name: str = Field(default="", alias="companyName")
    street_address: str = Field(default="", alias="streetAddress")
    city: str = Field(default="", alias="city")
    state: str = Field(default="", alias="state")
    postal_code: str = Field(default="", alias="postalCode")
    country_code: str = Field(default="", alias="countryCode")

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    company_prefix: Optional[str] = Field(default=None, alias="companyPrefix")
    gln: Optional[str] = Field(default=None, alias="gln")
    sgln: Optional[str] = Field(default=None, alias="sgln")
    company_name: Optional[str] = Field(default=None, alias="companyName")
    street_address: Optional[str] = Field(default=None, alias="streetAddress")
    city: Optional[str] = Field(default=None, alias="city")
    state: Optional[str] = Field(default=None, alias="state")
    postal_code: Optional[str] = Field(default=None, alias="postalCode")
    country_code: Optional[str] = Field(default=None, alias="countryCode")

class Location(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    company_prefix: str = ""
    gln: str = ""
    sgln: str = ""
    company_name: str = ""
    street_address: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country_code: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    
    # Check if user is active and approved (for regular users)
    if not user_data.get("is_super_admin", False):
        if user_data.get("status") != "active":
            return None  # User not approved or deactivated
    
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
    
    # Create new user (pending approval)
    hashed_password = get_password_hash(user.password)
    user_data = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_super_admin": False,
        "status": "pending",  # Requires admin approval
        "approved_by": None,
        "approved_at": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
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
    sscc_extension_digit: str = Field(alias="ssccExtensionDigit")
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
    sscc_extension_digit: str = Field(alias="ssccExtensionDigit")
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user_from_token(token: str) -> User:
    """Get user from JWT token without dependency injection"""
    try:
        token_data = verify_token(token)
        user = await get_user_by_email(token_data.email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_admin_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current admin user from JWT token"""
    try:
        user = await get_current_user_from_token(token)
        if not user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    
    # Check for multi-product serials first, fall back to legacy format
    product_serials = project.get("product_serials")
    serial_numbers = project.get("serial_numbers")
    
    print(f"DEBUG EPCIS Endpoint: project has product_serials={product_serials is not None}, serial_numbers={serial_numbers is not None}")
    if product_serials:
        print(f"DEBUG: product_serials type={type(product_serials)}, length={len(product_serials) if isinstance(product_serials, list) else 'not list'}")
    
    if not product_serials and not serial_numbers:
        raise HTTPException(status_code=400, detail="Project serial numbers not found")
    
    # Generate EPCIS XML (multi-product aware)
    xml_content = generate_epcis_xml(
        config, 
        serial_numbers,
        request.read_point,
        request.biz_location,
        product_serials=product_serials
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

# Locations endpoints
@api_router.get("/locations")
async def get_user_locations(current_user: User = Depends(get_current_user)):
    """Get all locations for the current user"""
    try:
        cursor = db.locations.find({"user_id": current_user.id})
        locations = []
        async for location in cursor:
            location_data = {
                "id": location["id"],
                "name": location["name"],
                "companyPrefix": location.get("company_prefix", ""),
                "gln": location.get("gln", ""),
                "sgln": location.get("sgln", ""),
                "companyName": location.get("company_name", ""),
                "streetAddress": location.get("street_address", ""),
                "city": location.get("city", ""),
                "state": location.get("state", ""),
                "postalCode": location.get("postal_code", ""),
                "countryCode": location.get("country_code", ""),
                "createdAt": location.get("created_at"),
                "updatedAt": location.get("updated_at")
            }
            locations.append(location_data)
        
        return {"locations": locations}
    except Exception as e:
        logger.error(f"Error fetching locations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/locations")
async def create_location(location_data: LocationCreate, current_user: User = Depends(get_current_user)):
    """Create a new location for the current user"""
    try:
        location = Location(
            user_id=current_user.id,
            name=location_data.name,
            company_prefix=location_data.company_prefix,
            gln=location_data.gln,
            sgln=location_data.sgln,
            company_name=location_data.company_name,
            street_address=location_data.street_address,
            city=location_data.city,
            state=location_data.state,
            postal_code=location_data.postal_code,
            country_code=location_data.country_code
        )
        
        await db.locations.insert_one(location.dict())
        
        return {
            "message": "Location created successfully",
            "location": {
                "id": location.id,
                "name": location.name,
                "companyPrefix": location.company_prefix,
                "gln": location.gln,
                "sgln": location.sgln,
                "companyName": location.company_name,
                "streetAddress": location.street_address,
                "city": location.city,
                "state": location.state,
                "postalCode": location.postal_code,
                "countryCode": location.country_code
            }
        }
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.put("/locations/{location_id}")
async def update_location(
    location_id: str, 
    location_update: LocationUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Update a location"""
    try:
        # Check if location exists and belongs to current user
        location = await db.locations.find_one({"id": location_id, "user_id": current_user.id})
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        
        # Prepare update data - only include fields that are not None
        update_data = {}
        if location_update.name is not None:
            update_data["name"] = location_update.name
        if location_update.company_prefix is not None:
            update_data["company_prefix"] = location_update.company_prefix
        if location_update.gln is not None:
            update_data["gln"] = location_update.gln
        if location_update.sgln is not None:
            update_data["sgln"] = location_update.sgln
        if location_update.company_name is not None:
            update_data["company_name"] = location_update.company_name
        if location_update.street_address is not None:
            update_data["street_address"] = location_update.street_address
        if location_update.city is not None:
            update_data["city"] = location_update.city
        if location_update.state is not None:
            update_data["state"] = location_update.state
        if location_update.postal_code is not None:
            update_data["postal_code"] = location_update.postal_code
        if location_update.country_code is not None:
            update_data["country_code"] = location_update.country_code
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.locations.update_one(
            {"id": location_id, "user_id": current_user.id},
            {"$set": update_data}
        )
        
        # Return updated location
        updated_location = await db.locations.find_one({"id": location_id, "user_id": current_user.id})
        
        return {
            "message": "Location updated successfully",
            "location": {
                "id": updated_location["id"],
                "name": updated_location["name"],
                "companyPrefix": updated_location.get("company_prefix", ""),
                "gln": updated_location.get("gln", ""),
                "sgln": updated_location.get("sgln", ""),
                "companyName": updated_location.get("company_name", ""),
                "streetAddress": updated_location.get("street_address", ""),
                "city": updated_location.get("city", ""),
                "state": updated_location.get("state", ""),
                "postalCode": updated_location.get("postal_code", ""),
                "countryCode": updated_location.get("country_code", "")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.delete("/locations/{location_id}")
async def delete_location(location_id: str, current_user: User = Depends(get_current_user)):
    """Delete a location"""
    try:
        result = await db.locations.delete_one({"id": location_id, "user_id": current_user.id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {"message": "Location deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Admin endpoints
@api_router.post("/admin/login", response_model=Token)
async def admin_login(admin: AdminLogin):
    """Admin login"""
    try:
        user_data = await db.users.find_one({"email": admin.email})
        
        if not user_data or not user_data.get("is_super_admin", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(admin.password, user_data["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_data["email"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@api_router.get("/admin/users")
async def get_all_users(current_admin: User = Depends(get_current_admin_user)):
    """Get all users (admin only)"""
    try:
        cursor = db.users.find({})
        users = []
        async for user in cursor:
            user_data = {
                "id": user["id"],
                "email": user["email"],
                "firstName": user.get("first_name", ""),
                "lastName": user.get("last_name", ""),
                "status": user.get("status", "pending"),
                "isSuperAdmin": user.get("is_super_admin", False),
                "isActive": user.get("is_active", True),
                "approvedBy": user.get("approved_by"),
                "approvedAt": user.get("approved_at"),
                "createdAt": user.get("created_at"),
                "updatedAt": user.get("updated_at")
            }
            users.append(user_data)
        
        return {"users": users}
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(
    user_id: str, 
    user_update: AdminUserUpdate, 
    current_admin: User = Depends(get_current_admin_user)
):
    """Update user (admin only)"""
    try:
        # Check if user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        
        if user_update.first_name is not None:
            update_data["first_name"] = user_update.first_name
        if user_update.last_name is not None:
            update_data["last_name"] = user_update.last_name
        if user_update.email is not None:
            # Check if email is already taken
            existing_user = await db.users.find_one({"email": user_update.email, "id": {"$ne": user_id}})
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already taken")
            update_data["email"] = user_update.email
        if user_update.status is not None:
            update_data["status"] = user_update.status
            # If approving user, set approval info
            if user_update.status == "active" and user.get("status") != "active":
                update_data["approved_by"] = current_admin.id
                update_data["approved_at"] = datetime.utcnow()
        if user_update.is_super_admin is not None:
            update_data["is_super_admin"] = user_update.is_super_admin
        
        # Update user
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        
        # Return updated user
        updated_user = await db.users.find_one({"id": user_id})
        return {
            "message": "User updated successfully",
            "user": {
                "id": updated_user["id"],
                "email": updated_user["email"],
                "firstName": updated_user.get("first_name", ""),
                "lastName": updated_user.get("last_name", ""),
                "status": updated_user.get("status", "pending"),
                "isSuperAdmin": updated_user.get("is_super_admin", False),
                "isActive": updated_user.get("is_active", True),
                "approvedBy": updated_user.get("approved_by"),
                "approvedAt": updated_user.get("approved_at")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.put("/admin/users/{user_id}/password")
async def admin_reset_password(
    user_id: str, 
    password_data: AdminPasswordReset, 
    current_admin: User = Depends(get_current_admin_user)
):
    """Reset user password (admin only)"""
    try:
        # Check if user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Hash new password
        hashed_password = get_password_hash(password_data.new_password)
        
        # Update password
        await db.users.update_one(
            {"id": user_id}, 
            {"$set": {
                "hashed_password": hashed_password,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {"message": "Password reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str, 
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete user (admin only)"""
    try:
        # Check if user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent self-deletion
        if user_id == current_admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
        # Delete user and their projects
        await db.users.delete_one({"id": user_id})
        await db.projects.delete_many({"user_id": user_id})
        await db.locations.delete_many({"user_id": user_id})
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/admin/users")
async def admin_create_user(
    user_data: CreateAdminUser, 
    current_admin: User = Depends(get_current_admin_user)
):
    """Create new admin user (admin only)"""
    try:
        # Check if email already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new admin user
        hashed_password = get_password_hash(user_data.password)
        new_user_data = {
            "id": str(uuid.uuid4()),
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_super_admin": True,
            "status": "active",  # Admin users are automatically active
            "approved_by": current_admin.id,
            "approved_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.users.insert_one(new_user_data)
        
        return {
            "message": "Admin user created successfully",
            "user": {
                "id": new_user_data["id"],
                "email": new_user_data["email"],
                "firstName": new_user_data["first_name"],
                "lastName": new_user_data["last_name"],
                "isSuperAdmin": True,
                "status": "active"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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

def generate_product_events(event_list, get_next_timestamp, read_point, biz_location,
                           sscc_serials, case_serials, inner_case_serials, item_serials,
                           shipper_company_prefix, sscc_extension_digit,
                           company_prefix, item_product_code, case_product_code, inner_case_product_code,
                           item_indicator_digit, case_indicator_digit, inner_case_indicator_digit,
                           use_inner_cases, direct_sscc_items, lot_number, expiration_date):
    """Generate ObjectEvents for a single product"""
    
    # Helper function to add ILMD extension
    def add_ilmd_extension(object_event, lot_number, expiration_date):
        if lot_number or expiration_date:
            extension = ET.SubElement(object_event, "extension")
            ilmd = ET.SubElement(extension, "ilmd")
            
            if lot_number:
                lot = ET.SubElement(ilmd, "cbvmda:lotNumber")
                lot.text = lot_number
            
            if expiration_date:
                exp_date = ET.SubElement(ilmd, "cbvmda:itemExpirationDate")
                exp_date.text = expiration_date
    
    # Generate EPCs
    sscc_epcs = [f"urn:epc:id:sscc:{shipper_company_prefix}.{sscc_extension_digit}{s}" for s in sscc_serials if s]
    case_epcs = [f"urn:epc:id:sgtin:{company_prefix}.{case_indicator_digit}{case_product_code}.{s}" for s in case_serials if s] if not direct_sscc_items else []
    inner_case_epcs = [f"urn:epc:id:sgtin:{company_prefix}.{inner_case_indicator_digit}{inner_case_product_code}.{s}" for s in inner_case_serials if s] if use_inner_cases and not direct_sscc_items else []
    item_epcs = [f"urn:epc:id:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}.{s}" for s in item_serials if s]
    
    print(f"  EPC Generation: {len(item_epcs)} item EPCs created from {len(item_serials)} serials")
    if len(item_epcs) > 0:
        print(f"    Sample item EPCs: {item_epcs[:2]}")
    
    # 1. Single Commissioning Event for All Items
    if item_epcs:
        print(f"    Creating commissioning event with {len(item_epcs)} items")
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
        add_ilmd_extension(object_event, lot_number, expiration_date)
    
    # 2. Commissioning Event for Inner Cases (if used)
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
        add_ilmd_extension(object_event, lot_number, expiration_date)
    
    # 3. Commissioning Event for Cases (if used)
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
        add_ilmd_extension(object_event, lot_number, expiration_date)
    
    # 4. Commissioning Event for SSCCs
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
    
    # Calculate hierarchy values needed for aggregation
    items_per_sscc = len(item_serials) // len(sscc_serials) if sscc_serials else 0
    items_per_case = len(item_serials) // len(case_serials) if case_serials and not use_inner_cases else 0
    items_per_inner_case = len(item_serials) // len(inner_case_serials) if inner_case_serials else 0
    inner_cases_per_case = len(inner_case_serials) // len(case_serials) if inner_case_serials and case_serials else 0
    cases_per_sscc = len(case_serials) // len(sscc_serials) if case_serials and sscc_serials else 0
    
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
            child_epcs_elem = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = sscc_index * items_per_sscc
            end_idx = start_idx + items_per_sscc
            for item_epc in item_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs_elem, "epc")
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
            child_epcs_elem = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = inner_case_index * items_per_inner_case
            end_idx = start_idx + items_per_inner_case
            for item_epc in item_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs_elem, "epc")
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
            child_epcs_elem = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = case_index * inner_cases_per_case
            end_idx = start_idx + inner_cases_per_case
            for inner_case_epc in inner_case_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs_elem, "epc")
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
            child_epcs_elem = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = case_index * items_per_case
            end_idx = start_idx + items_per_case
            for item_epc in item_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs_elem, "epc")
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
            child_epcs_elem = ET.SubElement(aggregation_event, "childEPCs")
            start_idx = sscc_index * cases_per_sscc
            end_idx = start_idx + cases_per_sscc
            for case_epc in case_epcs[start_idx:end_idx]:
                child_epc = ET.SubElement(child_epcs_elem, "epc")
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

def generate_epcis_xml(config, serial_numbers, read_point, biz_location, product_serials=None):
    """Generate GS1 EPCIS 1.2 XML with SBDH for pharmaceutical aggregation (multi-product aware)"""
    
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
    
    # Determine if we have multi-product configuration
    products_list = config.get("products", [])
    is_multi_product = len(products_list) > 0
    
    # Get shipper company prefix (used for SSCCs across all products)
    shipper_company_prefix = get_config_value("shipper_company_prefix", "shipperCompanyPrefix")
    if not shipper_company_prefix and is_multi_product and len(products_list) > 0:
        shipper_company_prefix = products_list[0].get("companyPrefix")
    elif not shipper_company_prefix:
        shipper_company_prefix = get_config_value("company_prefix", "companyPrefix")
    
    # Helper function to add EPCClass attributes (can work with full config or product dict)
    def add_epcclass_attributes(vocab_element, product_config):
        # Helper to get value from product dict (supports both snake_case and camelCase)
        def get_value(key_snake, key_camel):
            if isinstance(product_config, dict):
                return product_config.get(key_snake, product_config.get(key_camel))
            return None
        
        package_ndc = get_value("package_ndc", "packageNdc")
        if package_ndc:
            # Strip hyphens from package_ndc for EPCIS XML
            clean_package_ndc = package_ndc.replace("-", "")
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentification")
            attr.text = clean_package_ndc
            
            attr_type = ET.SubElement(vocab_element, "attribute")
            attr_type.set("id", "urn:epcglobal:cbv:mda#additionalTradeItemIdentificationTypeCode")
            attr_type.text = "FDA_NDC_11"
        
        regulated_name = get_value("regulated_product_name", "regulatedProductName")
        if regulated_name:
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#regulatedProductName")
            attr.text = regulated_name
        
        manufacturer = get_value("manufacturer_name", "manufacturerName")
        if manufacturer:
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#manufacturerOfTradeItemPartyName")
            attr.text = manufacturer
        
        dosage_form = get_value("dosage_form_type", "dosageFormType")
        if dosage_form:
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#dosageFormType")
            attr.text = dosage_form
        
        strength = get_value("strength_description", "strengthDescription")
        if strength:
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#strengthDescription")
            attr.text = strength
        
        net_content = get_value("net_content_description", "netContentDescription")
        if net_content:
            attr = ET.SubElement(vocab_element, "attribute")
            attr.set("id", "urn:epcglobal:cbv:mda#netContentDescription")
            attr.text = net_content
    
    # Create EPCClass vocabulary elements for each product
    if is_multi_product:
        # Multi-product mode - iterate through products
        for product in products_list:
            company_prefix = product.get("companyPrefix")
            product_code = product.get("productCode")
            item_indicator = product.get("itemIndicatorDigit", "0")
            case_indicator = product.get("caseIndicatorDigit", "0")
            inner_case_indicator = product.get("innerCaseIndicatorDigit", "0")
            use_inner = product.get("useInnerCases", False)
            cases_per_sscc = product.get("casesPerSscc", 0)
            
            # 1. Item Level EPCClass (always present)
            item_epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{item_indicator}{product_code}.*"
            item_vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
            item_vocabulary_element.set("id", item_epc_pattern)
            add_epcclass_attributes(item_vocabulary_element, product)
            
            # 2. Inner Case Level EPCClass (if inner cases are used)
            if use_inner and product_code and inner_case_indicator:
                inner_case_epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{inner_case_indicator}{product_code}.*"
                inner_case_vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
                inner_case_vocabulary_element.set("id", inner_case_epc_pattern)
                add_epcclass_attributes(inner_case_vocabulary_element, product)
            
            # 3. Case Level EPCClass (if cases are used)
            if cases_per_sscc > 0:
                case_epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{case_indicator}{product_code}.*"
                case_vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
                case_vocabulary_element.set("id", case_epc_pattern)
                add_epcclass_attributes(case_vocabulary_element, product)
    else:
        # Legacy single product mode
        company_prefix = get_config_value("company_prefix", "companyPrefix")
        base_product_code = get_config_value("product_code", "productCode", "")
        if not base_product_code:
            item_product_code = get_config_value("item_product_code", "itemProductCode", "")
            case_product_code = get_config_value("case_product_code", "caseProductCode", "")
            inner_case_product_code = get_config_value("inner_case_product_code", "innerCaseProductCode", "")
        else:
            item_product_code = base_product_code
            case_product_code = base_product_code
            inner_case_product_code = base_product_code
        
        item_indicator_digit = get_config_value("item_indicator_digit", "itemIndicatorDigit", "")
        case_indicator_digit = get_config_value("case_indicator_digit", "caseIndicatorDigit", "")
        inner_case_indicator_digit = get_config_value("inner_case_indicator_digit", "innerCaseIndicatorDigit", "")
        use_inner_cases = get_config_value("use_inner_cases", "useInnerCases")
        cases_per_sscc = get_config_value("cases_per_sscc", "casesPerSscc")
        
        # 1. Item Level EPCClass
        item_epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{item_indicator_digit}{item_product_code}.*"
        item_vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
        item_vocabulary_element.set("id", item_epc_pattern)
        add_epcclass_attributes(item_vocabulary_element, config)
        
        # 2. Inner Case Level EPCClass
        if use_inner_cases and inner_case_product_code and inner_case_indicator_digit:
            inner_case_epc_pattern = f"urn:epc:idpat:sgtin:{company_prefix}.{inner_case_indicator_digit}{inner_case_product_code}.*"
            inner_case_vocabulary_element = ET.SubElement(vocabulary_element_list, "VocabularyElement")
            inner_case_vocabulary_element.set("id", inner_case_epc_pattern)
            add_epcclass_attributes(inner_case_vocabulary_element, config)
        
        # 3. Case Level EPCClass
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
    sscc_extension_digit = get_config_value("sscc_extension_digit", "ssccExtensionDigit", "")
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
    
    # Get hierarchy configuration (for legacy single-product mode)
    # For multi-product, this will be overridden per product
    if not is_multi_product:
        # Legacy single-product mode
        company_prefix = get_config_value("company_prefix", "companyPrefix")
        use_inner_cases = get_config_value("use_inner_cases", "useInnerCases", False)
        cases_per_sscc = get_config_value("cases_per_sscc", "casesPerSscc", 0)
        
        # Get product code
        base_product_code = get_config_value("product_code", "productCode", "")
        if not base_product_code:
            item_product_code = get_config_value("item_product_code", "itemProductCode", "")
            case_product_code = get_config_value("case_product_code", "caseProductCode", "")
            inner_case_product_code = get_config_value("inner_case_product_code", "innerCaseProductCode", "")
        else:
            item_product_code = base_product_code
            case_product_code = base_product_code
            inner_case_product_code = base_product_code
        
        # Get indicator digits
        item_indicator_digit = get_config_value("item_indicator_digit", "itemIndicatorDigit", "")
        case_indicator_digit = get_config_value("case_indicator_digit", "caseIndicatorDigit", "")
        inner_case_indicator_digit = get_config_value("inner_case_indicator_digit", "innerCaseIndicatorDigit", "")
    else:
        # For multi-product, use first product's config as default
        # (will be overridden when processing each product's serials)
        first_product = products_list[0] if products_list else {}
        company_prefix = first_product.get("companyPrefix", "")
        use_inner_cases = first_product.get("useInnerCases", False)
        cases_per_sscc = first_product.get("casesPerSscc", 0)
        
        # Product codes
        product_code = first_product.get("productCode", "")
        item_product_code = product_code
        case_product_code = product_code
        inner_case_product_code = product_code
        
        # Indicator digits
        item_indicator_digit = first_product.get("itemIndicatorDigit", "0")
        case_indicator_digit = first_product.get("caseIndicatorDigit", "0")
        inner_case_indicator_digit = first_product.get("innerCaseIndicatorDigit", "0")
    
    # Check if we have direct SSCC → Items aggregation
    direct_sscc_items = cases_per_sscc == 0
    
    if direct_sscc_items:
        items_per_sscc = get_config_value("items_per_case", "itemsPerCase")  # In this case, items_per_case means items_per_sscc
    elif use_inner_cases:
        inner_cases_per_case = get_config_value("inner_cases_per_case", "innerCasesPerCase")
        items_per_inner_case = get_config_value("items_per_inner_case", "itemsPerInnerCase")
    else:
        items_per_case = get_config_value("items_per_case", "itemsPerCase")
    
    # === MULTI-PRODUCT EVENT GENERATION ===
    # Determine which products to process
    print(f"DEBUG: is_multi_product={is_multi_product}, product_serials={product_serials is not None}, len={len(product_serials) if product_serials else 0}")
    if is_multi_product and product_serials and len(product_serials) > 0:
        # Multi-product mode: Generate events for each product
        print(f"DEBUG: Multi-product mode activated. Processing {len(product_serials)} products")
        for product_serial_entry in product_serials:
            product_index = product_serial_entry.get("productIndex", 0)
            product_hierarchical_serials = product_serial_entry.get("hierarchicalSerials", [])
            
            # Get product configuration
            if product_index < len(products_list):
                product = products_list[product_index]
                
                # Override config variables with product-specific values
                company_prefix = product.get("companyPrefix", "")
                product_code = product.get("productCode", "")
                item_product_code = product_code
                case_product_code = product_code
                inner_case_product_code = product_code
                
                item_indicator_digit = product.get("itemIndicatorDigit", "0")
                case_indicator_digit = product.get("caseIndicatorDigit", "0")
                inner_case_indicator_digit = product.get("innerCaseIndicatorDigit", "0")
                sscc_extension_digit_product = product.get("ssccExtensionDigit", "0")
                
                use_inner_cases = product.get("useInnerCases", False)
                cases_per_sscc = product.get("casesPerSscc", 0)
                direct_sscc_items = cases_per_sscc == 0
                
                lot_number = product.get("lotNumber", "")
                expiration_date = product.get("expirationDate", "")
                
                # Extract serials from hierarchical structure
                sscc_serials = []
                case_serials = []
                inner_case_serials = []
                item_serials = []
                
                for sscc_entry in product_hierarchical_serials:
                    sscc_serials.append(sscc_entry.get("ssccSerial", ""))
                    
                    if "cases" in sscc_entry:
                        for case_entry in sscc_entry["cases"]:
                            case_serials.append(case_entry.get("caseSerial", ""))
                            
                            if "innerCases" in case_entry and case_entry["innerCases"]:
                                for inner_case_entry in case_entry["innerCases"]:
                                    inner_case_serials.append(inner_case_entry.get("innerCaseSerial", ""))
                                    if "items" in inner_case_entry:
                                        for item_entry in inner_case_entry["items"]:
                                            item_serials.append(item_entry.get("itemSerial", ""))
                            
                            if "items" in case_entry:
                                for item_entry in case_entry["items"]:
                                    item_serials.append(item_entry.get("itemSerial", ""))
                    
                    if "items" in sscc_entry:
                        for item_entry in sscc_entry["items"]:
                            item_serials.append(item_entry.get("itemSerial", ""))
                
                # Generate events for this product
                print(f"DEBUG: Generating events for product {product_index}")
                print(f"  - SSCC serials: {len(sscc_serials)}")
                print(f"  - Case serials: {len(case_serials)}")
                print(f"  - Inner case serials: {len(inner_case_serials)}")
                print(f"  - Item serials: {len(item_serials)}")
                print(f"  - Item serials list: {item_serials[:3]}")  # Show first 3
                generate_product_events(
                    event_list, get_next_timestamp, read_point, biz_location,
                    sscc_serials, case_serials, inner_case_serials, item_serials,
                    shipper_company_prefix, sscc_extension_digit_product,
                    company_prefix, item_product_code, case_product_code, inner_case_product_code,
                    item_indicator_digit, case_indicator_digit, inner_case_indicator_digit,
                    use_inner_cases, direct_sscc_items, lot_number, expiration_date
                )
        
        # Skip legacy single-product processing
        pass
    else:
        # Legacy single-product mode
        # Normalize serial numbers data structure to handle both formats
        sscc_serials = []
        case_serials = []
        inner_case_serials = []
        item_serials = []
        
        # Check if serial_numbers is in the new list format with "type" fields
        if serial_numbers and isinstance(serial_numbers, list) and len(serial_numbers) > 0 and isinstance(serial_numbers[0], dict) and "type" in serial_numbers[0]:
            # Handle new list format with "type" and "serial" fields
            for serial_entry in serial_numbers:
                if serial_entry["type"] == "sscc":
                    sscc_serials.append(serial_entry["serial"])
                elif serial_entry["type"] == "case":
                    case_serials.append(serial_entry["serial"])
                elif serial_entry["type"] == "inner_case":
                    inner_case_serials.append(serial_entry["serial"])
                elif serial_entry["type"] == "item":
                    item_serials.append(serial_entry["serial"])
        elif serial_numbers and isinstance(serial_numbers, list) and len(serial_numbers) > 0 and isinstance(serial_numbers[0], dict) and "ssccIndex" in serial_numbers[0]:
            # Handle frontend hierarchical format (from auto-save)
            for sscc_entry in serial_numbers:
                sscc_serials.append(sscc_entry.get("ssccSerial", ""))
                
                # Extract case serials and item serials from nested structure
                if "cases" in sscc_entry:
                    for case_entry in sscc_entry["cases"]:
                        case_serials.append(case_entry.get("caseSerial", ""))
                        
                        # Handle inner cases if present
                        if "innerCases" in case_entry and case_entry["innerCases"]:
                            for inner_case_entry in case_entry["innerCases"]:
                                inner_case_serials.append(inner_case_entry.get("innerCaseSerial", ""))
                                
                                # Handle items within inner cases
                                if "items" in inner_case_entry:
                                    for item_entry in inner_case_entry["items"]:
                                        item_serials.append(item_entry.get("itemSerial", ""))
                        
                        # Handle items directly under cases (no inner cases)
                        if "items" in case_entry:
                            for item_entry in case_entry["items"]:
                                item_serials.append(item_entry.get("itemSerial", ""))
                
                # Handle items directly under SSCC (no cases)  
                if "items" in sscc_entry:
                    for item_entry in sscc_entry["items"]:
                        item_serials.append(item_entry.get("itemSerial", ""))
        elif serial_numbers and isinstance(serial_numbers, dict):
            # Handle simple hierarchical format (legacy)
            sscc_serials = serial_numbers.get("ssccSerialNumbers", serial_numbers.get("sscc_serial_numbers", []))
            case_serials = serial_numbers.get("caseSerialNumbers", serial_numbers.get("case_serial_numbers", []))
            inner_case_serials = serial_numbers.get("innerCaseSerialNumbers", serial_numbers.get("inner_case_serial_numbers", []))
            item_serials = serial_numbers.get("itemSerialNumbers", serial_numbers.get("item_serial_numbers", []))
    
            # Generate proper EPC identifiers
            sscc_epcs = []
            case_epcs = []
            inner_case_epcs = []
            item_epcs = []
            
            # Generate SSCC EPCs using shipper's company prefix
            for sscc_serial in sscc_serials:
                sscc_epc = f"urn:epc:id:sscc:{shipper_company_prefix}.{sscc_extension_digit}{sscc_serial}"
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
    # Collect all SSCCs for the shipping event
    all_sscc_epcs = []
    
    if is_multi_product and product_serials and len(product_serials) > 0:
        # Multi-product mode: collect SSCCs from all products
        for product_serial_entry in product_serials:
            product_hierarchical_serials = product_serial_entry.get("hierarchicalSerials", [])
            for sscc_entry in product_hierarchical_serials:
                sscc_serial = sscc_entry.get("ssccSerial", "")
                if sscc_serial:
                    sscc_epc = f"urn:epc:id:sscc:{shipper_company_prefix}.{sscc_extension_digit}{sscc_serial}"
                    all_sscc_epcs.append(sscc_epc)
    else:
        # Legacy mode: use sscc_epcs from else block
        all_sscc_epcs = sscc_epcs if 'sscc_epcs' in locals() else []
    
    shipping_event = ET.SubElement(event_list, "ObjectEvent")
    
    event_time = ET.SubElement(shipping_event, "eventTime")
    event_time.text = get_next_timestamp()
    
    event_timezone = ET.SubElement(shipping_event, "eventTimeZoneOffset")
    event_timezone.text = "+00:00"
    
    # Add all SSCCs to the shipping event
    epc_list = ET.SubElement(shipping_event, "epcList")
    for sscc_epc in all_sscc_epcs:
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
    receiver_gln = get_config_value("receiver_gln", "receiverGln", "")
    receiver_po_number = get_config_value("receiver_po_number", "receiverPoNumber", "")
    if receiver_gln and receiver_po_number:
        po_transaction = ET.SubElement(biz_transaction_list, "bizTransaction")
        po_transaction.set("type", "urn:epcglobal:cbv:btt:po")
        po_transaction.text = f"urn:epcglobal:cbv:bt:{receiver_gln}:{receiver_po_number}"
    
    # Despatch Advice transaction
    sender_gln = get_config_value("sender_gln", "senderGln", "")
    sender_despatch_advice_number = get_config_value("sender_despatch_advice_number", "senderDespatchAdviceNumber", "")
    if sender_gln and sender_despatch_advice_number:
        desadv_transaction = ET.SubElement(biz_transaction_list, "bizTransaction")
        desadv_transaction.set("type", "urn:epcglobal:cbv:btt:desadv")
        desadv_transaction.text = f"urn:epcglobal:cbv:bt:{sender_gln}:{sender_despatch_advice_number}"
    
    # Add extension with sourceList and destinationList
    extension = ET.SubElement(shipping_event, "extension")
    
    # Source list (sender information)
    source_list = ET.SubElement(extension, "sourceList")
    sender_sgln = get_config_value("sender_sgln", "senderSgln", "")
    shipper_sgln = get_config_value("shipper_sgln", "shipperSgln", "")
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
    receiver_sgln = get_config_value("receiver_sgln", "receiverSgln", "")
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
    allow_origins=["*", "https://scandit-epcis.preview.emergentagent.com"],
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