#!/usr/bin/env python3
"""
Initial Super Admin Setup Script
Creates the first super admin user for the EPCIS application.
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

async def create_initial_admin():
    """Create the initial super admin user"""
    
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://mongo:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.epcis_app
    
    try:
        # Check if any admin already exists
        existing_admin = await db.users.find_one({"is_super_admin": True})
        if existing_admin:
            print("❌ A super admin already exists!")
            print(f"   Email: {existing_admin['email']}")
            print("   Use the admin panel to create additional admins.")
            return False
        
        # Get admin details
        print("🔧 Setting up initial Super Admin...")
        print()
        
        email = input("Enter admin email: ").strip()
        if not email:
            print("❌ Email is required!")
            return False
        
        password = input("Enter admin password: ").strip()
        if not password or len(password) < 6:
            print("❌ Password must be at least 6 characters!")
            return False
        
        first_name = input("Enter first name: ").strip() or "Super"
        last_name = input("Enter last name: ").strip() or "Admin"
        
        # Create admin user
        admin_data = {
            "id": str(uuid.uuid4()),
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "hashed_password": hash_password(password),
            "is_active": True,
            "is_super_admin": True,
            "status": "active",
            "approved_by": "system",
            "approved_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.users.insert_one(admin_data)
        
        print()
        print("✅ Super Admin created successfully!")
        print(f"   Email: {email}")
        print(f"   Name: {first_name} {last_name}")
        print()
        print("You can now access the admin panel at:")
        print("   /admin (login with the credentials above)")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = asyncio.run(create_initial_admin())
    sys.exit(0 if success else 1)