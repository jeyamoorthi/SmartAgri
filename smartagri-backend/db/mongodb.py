"""
MongoDB async client using Motor.
Provides a singleton connection and collection accessors.
"""
import os
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "smartagri_db")

# Mock database classes for serverless/local fallback
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MockCursor:
    def __init__(self, data):
        self.data = list(data)
        
    def sort(self, key, direction=1):
        def sort_key(item):
            val = item.get(key)
            if val is None:
                return ""
            return val
        self.data.sort(key=sort_key, reverse=(direction == -1))
        return self
        
    async def to_list(self, length=None):
        if length is not None:
            return self.data[:length]
        return self.data

class MockCollection:
    def __init__(self, name, initial_data=None):
        self.name = name
        self.data = initial_data or []
        
    async def delete_many(self, filter=None):
        self.data = []
        return None
        
    async def insert_many(self, docs):
        for doc in docs:
            if "_id" not in doc:
                doc["_id"] = ObjectId()
            self.data.append(dict(doc))
        return None

    async def find_one(self, filter, sort=None):
        for item in self.data:
            match = True
            for k, v in filter.items():
                if k == "_id":
                    if str(item.get("_id")) != str(v):
                        match = False
                        break
                elif isinstance(v, dict) and "$regex" in v:
                    pattern = v["$regex"]
                    if not pattern.lower() in item.get(k, "").lower():
                        match = False
                        break
                else:
                    if item.get(k) != v:
                        match = False
                        break
            if match:
                return dict(item)
        return None
        
    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.data.append(dict(doc))
        class InsertResult:
            def __init__(self, id):
                self.inserted_id = id
        return InsertResult(doc["_id"])
        
    async def update_one(self, filter, update):
        doc = await self.find_one(filter)
        if doc:
            for item in self.data:
                if str(item.get("_id")) == str(doc.get("_id")):
                    if "$set" in update:
                        for k, v in update["$set"].items():
                            item[k] = v
                    break
        class UpdateResult:
            def __init__(self):
                self.modified_count = 1
        return UpdateResult()
        
    def find(self, filter=None, projection=None):
        filter = filter or {}
        results = []
        for item in self.data:
            match = True
            for k, v in filter.items():
                if isinstance(v, dict) and "$regex" in v:
                    pattern = v["$regex"]
                    if not pattern.lower() in item.get(k, "").lower():
                        match = False
                        break
                else:
                    if item.get(k) != v:
                        match = False
                        break
            if match:
                results.append(dict(item))
        return MockCursor(results)

class MockDatabase:
    def __init__(self):
        self.collections = {}
        
    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

# Global connection variables
client = None
db = None

def get_seeded_mock_db():
    mdb = MockDatabase()
    murugan_password_hash = pwd_context.hash("farmer123")
    
    # 1. Users
    user_doc = {
        "_id": ObjectId("65ccb2b9d6992d09adb77903"),
        "username": "Murugan Selvam",
        "email": "murugan.selvam@example.com",
        "password_hash": murugan_password_hash,
        "present_crop": "tomato",
        "present_crop_stage": "vegetative",
        "land_acres": 2.5,
        "district": "Madurai",
        "state": "Tamil Nadu",
        "soil_data": {
            "texture": "Red Clay",
            "pH": 6.8,
            "nitrogen_level": "medium",
            "phosphorus_level": "low",
            "potassium_level": "high"
        },
        "weather_data": {
            "temp": 31.5,
            "humidity": 70,
            "condition": "Partly Cloudy"
        },
        "past_crop": "tomato",
        "past_disease": "Early Blight",
        "preferred_language": "ta",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    user_alias_doc = dict(user_doc)
    user_alias_doc["_id"] = ObjectId("65ccb2b9d6992d09adb77904")
    user_alias_doc["email"] = "murugan@example.com"
    user_alias_doc["username"] = "Murugan"
    
    mdb["users"].data.extend([user_doc, user_alias_doc])
    
    # 2. Market Trends
    trends = [
        {
            "crop_name": "tomato",
            "price_per_quintal": 3200,
            "price_trend": "rising",
            "demand_level": "high",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "crop_name": "paddy",
            "price_per_quintal": 2150,
            "price_trend": "stable",
            "demand_level": "medium",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "crop_name": "onion",
            "price_per_quintal": 2800,
            "price_trend": "falling",
            "demand_level": "high",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]
    mdb["market_trends"].data.extend(trends)
    
    # 3. Vendors
    vendors = [
        {
            "_id": ObjectId(),
            "name": "Madurai Organic Exotics Buyer",
            "location": "Madurai, Tamil Nadu",
            "contact": "buyer@organicmadurai.com",
            "email": "buyer@organicmadurai.com",
            "crops_accepted": ["Dragon Fruit", "Passion Fruit", "Vanilla"],
            "active": True
        },
        {
            "_id": ObjectId(),
            "name": "Chennai Organic Mandi",
            "location": "Chennai, Tamil Nadu",
            "contact": "procurement@chennaiorganic.org",
            "email": "procurement@chennaiorganic.org",
            "crops_accepted": ["Dragon Fruit", "Tomato", "Paddy"],
            "active": True
        }
    ]
    mdb["vendors"].data.extend(vendors)
    
    # 4. Products
    products = [
        {
            "name": "Premium Neem Oil Spray",
            "category": "pest_control",
            "price": 450,
            "unit": "1 Liter",
            "description": "Cold-pressed pure neem oil water-soluble concentrate. 10000 ppm azadirachtin.",
            "supplier": "Tamil Nadu Bio-Inputs Corp",
            "stock": 150
        },
        {
            "name": "Organic Jivamrita Culture",
            "category": "fertilizer",
            "price": 250,
            "unit": "5 Liters",
            "description": "Fermented microbial culture to boost soil nitrogen-fixing bacteria.",
            "supplier": "Madurai Natural Farm Alliance",
            "stock": 80
        }
    ]
    mdb["products"].data.extend(products)
    
    # 5. Pest Alerts
    pest_alerts = [
        {
            "district": "Madurai",
            "crop": "tomato",
            "pest_name": "Fruit Borer",
            "severity": "high",
            "alert_date": datetime.now(timezone.utc).isoformat()
        }
    ]
    mdb["pest_alerts"].data.extend(pest_alerts)
    return mdb


async def connect_db():
    """Connect to MongoDB Atlas, falling back to a pre-seeded MockDatabase if unreachable."""
    global client, db
    
    if "placeholder_please_replace" in MONGODB_URI or "placeholder" in MONGODB_URI.lower():
        print("[MongoDB] Placeholder detected. Falling back to pre-seeded MockDatabase.")
        db = get_seeded_mock_db()
        return
        
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[MONGODB_DB]
        # Verify connection
        await client.admin.command("ping")
        print(f"[MongoDB] Connected to database: {MONGODB_DB}")
    except Exception as e:
        print(f"[MongoDB] Warning: Could not connect to database on startup ({e}). Falling back to pre-seeded MockDatabase.")
        db = get_seeded_mock_db()


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
