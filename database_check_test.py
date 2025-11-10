#!/usr/bin/env python3
"""
Database Direct Check - Check if product_serials is stored in MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

PROJECT_ID = "a57661ea-634c-44b3-8d4e-08eb72f9c23a"

async def check_database():
    """Check the database directly for product_serials"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Find the project directly in MongoDB
        project = await db.projects.find_one({"id": PROJECT_ID})
        
        if project:
            print(f"📋 PROJECT FOUND IN DATABASE:")
            print(f"   Project ID: {project.get('id')}")
            print(f"   Name: {project.get('name')}")
            
            # Check all fields
            print(f"\n🔍 ALL DATABASE FIELDS:")
            for key, value in project.items():
                if key == '_id':
                    continue  # Skip MongoDB internal ID
                print(f"   {key}: {type(value)}")
                if key == 'product_serials':
                    print(f"      Value: {value}")
            
            # Specifically check product_serials
            product_serials = project.get('product_serials')
            print(f"\n📦 PRODUCT_SERIALS IN DATABASE:")
            print(f"   Exists: {'Yes' if 'product_serials' in project else 'No'}")
            print(f"   Value: {product_serials}")
            print(f"   Type: {type(product_serials)}")
            
            if product_serials:
                print(f"   Length: {len(product_serials) if isinstance(product_serials, list) else 'N/A'}")
                if isinstance(product_serials, list) and len(product_serials) > 0:
                    print(f"   First item: {product_serials[0]}")
            
        else:
            print(f"❌ Project {PROJECT_ID} not found in database")
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_database())