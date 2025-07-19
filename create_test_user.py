#!/usr/bin/env python3
"""
Create Test User Script
Creates an approved test user for EPCIS testing.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_test_user():
    """Create an approved test user"""
    
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.test_database  # Use correct database name
    
    try:
        # Create test user
        email = "epcis_test_user@test.com"
        password = "TestPassword123!"
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": email})
        if existing_user:
            print(f"✅ Test user already exists: {email}")
            return True
        
        user_data = {
            "id": str(uuid.uuid4()),
            "email": email,
            "first_name": "EPCIS",
            "last_name": "Tester",
            "hashed_password": hash_password(password),
            "is_active": True,
            "is_super_admin": False,
            "status": "active",  # Approved status
            "approved_by": "system",
            "approved_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.users.insert_one(user_data)
        
        print(f"✅ Approved test user created successfully!")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   Status: active")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = asyncio.run(create_test_user())
    sys.exit(0 if success else 1)