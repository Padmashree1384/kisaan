"""
MongoDB connection manager using Motor (async driver).
Provides a single shared client across the application.
"""

import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING
from app.config import settings

# Global client and database references
client: motor.motor_asyncio.AsyncIOMotorClient = None
db: motor.motor_asyncio.AsyncIOMotorDatabase = None


async def connect_db():
    """Initialize the MongoDB connection and create indexes."""
    global client, db

    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]

    # Create indexes for performance
    await _create_indexes()
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def disconnect_db():
    """Close the MongoDB connection gracefully."""
    global client
    if client:
        client.close()
        print("🔌 Disconnected from MongoDB")


async def _create_indexes():
    """Create all necessary indexes."""
    # Users: phone must be unique
    await db.users.create_index([("phone", ASCENDING)], unique=True)
    await db.users.create_index([("last_active", DESCENDING)])

    # Prices: compound index for fast lookups by commodity + mandi + date
    await db.prices.create_index([
        ("commodity", ASCENDING),
        ("state", ASCENDING),
        ("district", ASCENDING),
        ("market", ASCENDING),
        ("arrival_date", DESCENDING),
    ])
    await db.prices.create_index([("fetched_at", DESCENDING)])

    # Notifications: look up by user and status quickly
    await db.notifications.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    await db.notifications.create_index([("status", ASCENDING)])

    print("📑 MongoDB indexes created")


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Dependency injection helper for FastAPI routes."""
    return db
