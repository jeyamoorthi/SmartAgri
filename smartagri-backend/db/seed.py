"""
Seed script — Populate MongoDB with realistic India-relevant data.
Run: python seed.py (from backend/db/) or python -m db.seed (from backend/)
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from passlib.context import CryptContext
from dotenv import load_dotenv

# Add parent directory to path so we can import from db and models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "smartagri_db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed():
    """Seed all collections with realistic data."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]

    print("[INFO] Seeding SmartAgri database...")

    # ── 1. USERS ─────────────────────────────────────────────────────────────
    users_col = db["users"]
    await users_col.delete_many({})
    
    murugan_password_hash = pwd_context.hash("farmer123")
    farmers = [
        {
            "username": "Murugan Selvam",
            "email": "murugan.selvam@example.com",
            "password_hash": murugan_password_hash,
            "present_crop": "paddy",
            "present_crop_stage": "Vegetative",
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
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    await users_col.insert_many(farmers)
    print("  [OK] Murugan Selvam seeded.")

    # ── 2. MARKET TRENDS ─────────────────────────────────────────────────────
    market_trends_col = db["market_trends"]
    await market_trends_col.delete_many({})
    
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
    await market_trends_col.insert_many(trends)
    print("  [OK] Market trends seeded.")

    # ── 3. VENDORS ───────────────────────────────────────────────────────────
    vendors_col = db["vendors"]
    await vendors_col.delete_many({})
    
    vendors = [
        {
            "name": "Madurai Organic Exotics Buyer",
            "location": "Madurai, Tamil Nadu",
            "contact": "buyer@organicmadurai.com",
            "email": "buyer@organicmadurai.com",
            "crops_accepted": ["Dragon Fruit", "Passion Fruit", "Vanilla"],
            "active": True
        },
        {
            "name": "Chennai Organic Mandi",
            "location": "Chennai, Tamil Nadu",
            "contact": "procurement@chennaiorganic.org",
            "email": "procurement@chennaiorganic.org",
            "crops_accepted": ["Dragon Fruit", "Tomato", "Paddy"],
            "active": True
        }
    ]
    await vendors_col.insert_many(vendors)
    print("  [OK] Vendors seeded.")

    # ── 4. PRODUCTS ──────────────────────────────────────────────────────────
    products_col = db["products"]
    await products_col.delete_many({})
    
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
    await products_col.insert_many(products)
    print("  [OK] Products seeded.")

    # ── 5. PEST ALERTS ───────────────────────────────────────────────────────
    pest_alerts_col = db["pest_alerts"]
    await pest_alerts_col.delete_many({})
    
    pest_alerts = [
        {
            "district": "Madurai",
            "crop": "tomato",
            "pest_name": "Fruit Borer",
            "severity": "high",
            "alert_date": datetime.now(timezone.utc).isoformat()
        }
    ]
    await pest_alerts_col.insert_many(pest_alerts)
    print("  [OK] Pest alerts seeded.")

    print("\n[OK] Database seeding complete!")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
