"""
MongoDB async client using Motor.
Provides a singleton connection and collection accessors.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "smartagri_db")

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Connect to MongoDB Atlas."""
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[MONGODB_DB]
        # Verify connection
        await client.admin.command("ping")
        print(f"[MongoDB] Connected to database: {MONGODB_DB}")
    except Exception as e:
        print(f"[MongoDB] Warning: Could not connect to database on startup: {e}")
        # Note: client and db are still initialized, but operations requiring DB will fail.



async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("[MongoDB] Connection closed")


def get_db():
    """Return the database instance."""
    return db


# ── Collection accessors ──────────────────────────────────────────────────────
def users_col():
    return db["users"]

def market_trends_col():
    return db["market_trends"]

def pest_alerts_col():
    return db["pest_alerts"]

def advisory_plans_col():
    return db["advisory_plans"]

def products_col():
    return db["products"]

def vendors_col():
    return db["vendors"]

def exotic_recommendations_col():
    return db["exotic_recommendations"]

def orders_col():
    return db["orders"]

def produce_listings_col():
    return db["produce_listings"]
