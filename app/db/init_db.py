"""
This script initializes the MongoDB database with required collections and indexes.
Usage: python init_db.py
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.core.config import settings

async def setup_database():
    """Set up MongoDB database with collections and indexes"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    # Create collections
    collections = ["users", "chat_sessions"]
    for collection_name in collections:
        if collection_name not in await db.list_collection_names():
            await db.create_collection(collection_name)
            print(f"Created collection: {collection_name}")
    
    # Create indexes
    # Users collection indexes
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    print("Created indexes for users collection")
    
    # Chat sessions collection indexes
    await db.chat_sessions.create_index("user_id")
    await db.chat_sessions.create_index([("user_id", 1), ("created_at", -1)])
    print("Created indexes for chat_sessions collection")
    
    print(f"Database {settings.DATABASE_NAME} initialized successfully!")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_database())