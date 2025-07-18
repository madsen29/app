from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
from fastapi import HTTPException, status
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    company_name: str
    street_address: str
    city: str
    state: str
    postal_code: str
    country_code: str
    created_at: datetime
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(email=email)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_user_by_email(email: str):
    """Get user by email from database"""
    user = await db.users.find_one({"email": email})
    if user:
        return User(**user)
    return None

async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    user_data = await db.users.find_one({"email": email})
    if not user_data:
        return False
    if not verify_password(password, user_data["password"]):
        return False
    return User(**user_data)

async def create_user(user: UserCreate):
    """Create a new user in database"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_dict = user.model_dump(by_alias=True)
    user_dict["password"] = get_password_hash(user.password)
    user_dict["created_at"] = datetime.now(timezone.utc)
    user_dict["is_active"] = True
    user_dict["id"] = str(user_dict.get("_id", ""))
    
    # Insert user
    result = await db.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    
    # Return user without password
    user_dict.pop("password")
    return User(**user_dict)