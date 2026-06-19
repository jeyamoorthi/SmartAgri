"""
Recommendations router — exotic crop recommendations with vendor matching.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from bson import ObjectId

from db.mongodb import (
    users_col, vendors_col, exotic_recommendations_col, market_trends_col
)
from models.user import CropInterest
from routers.auth import get_current_user, _user_to_response
from services.gemini_service import recommend_next_crop
from services.email_service import send_vendor_introduction

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/crop")
async def get_crop_recommendation(current_user: dict = Depends(get_current_user)):
    """
    Get a suitable high-profit crop recommendation using Gemini AI.
    Matches with local vendors and stores the recommendation.
    """
    user_id = str(current_user["_id"])
    profile = _user_to_response(current_user)["farmer_profile"]

    # Check if recent recommendation exists and matches the user's current profile settings
    existing = await exotic_recommendations_col().find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)],
    )

    if existing and existing.get("user_crop") == profile.get("crop") and existing.get("user_soil_type") == profile.get("soil_type") and existing.get("user_state") == profile.get("state"):
        existing["id"] = str(existing.pop("_id"))
        return {"status": "success", "recommendation": existing}

    # Fetch recent market data for context
    market_data = await market_trends_col().find(
        {},
        {"_id": 0, "crop_name": 1, "price_per_quintal": 1, "demand_level": 1}
    ).sort("timestamp", -1).to_list(length=20)

    # Generate recommendation using Gemini
    reco = await recommend_next_crop(profile, market_data)
    crop_name = reco.get("crop_name", "Groundnut")

    # Find matching vendor
    vendor = await vendors_col().find_one({
        "crops_accepted": {"$regex": crop_name, "$options": "i"},
        "active": True
    })

    vendor_match = None
    if vendor:
        vendor_match = {
            "id": str(vendor["_id"]),
            "name": vendor.get("name", ""),
            "location": vendor.get("location", ""),
            "contact": vendor.get("contact", ""),
            "crops_accepted": vendor.get("crops_accepted", [])
        }

    reco_doc = {
        "user_id": user_id,
        "user_crop": profile.get("crop", "paddy"),
        "user_soil_type": profile.get("soil_type", "Red Soil"),
        "user_state": profile.get("state", "Tamil Nadu"),
        "crop_name": crop_name,
        "secondary_recommendation": reco.get("secondary_recommendation", ""),
        "why_suitable": reco.get("why_suitable", ""),
        "expected_yield_per_acre": reco.get("expected_yield_per_acre", "2-3 tonnes"),
        "expected_profit_inr": reco.get("profit_estimate", reco.get("expected_profit_inr", 150000)),
        "best_season": reco.get("best_season", ""),
        "care_tips": reco.get("care_tips", ""),
        "market_demand_score": reco.get("market_demand_score", 8),
        "grow_duration_days": reco.get("grow_duration_days", 120),
        "risk_score": reco.get("risk_score", 3),
        "vendor_match": vendor_match,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    result = await exotic_recommendations_col().insert_one(reco_doc)
    reco_doc["id"] = str(result.inserted_id)
    if "_id" in reco_doc:
        del reco_doc["_id"]

    return {"status": "success", "recommendation": reco_doc}


@router.post("/interested")
async def express_interest(
    data: CropInterest,
    current_user: dict = Depends(get_current_user),
):
    """
    Farmer expresses interest in growing recommended crop.
    Saves preference and emails the matched vendor.
    """
    user_id = str(current_user["_id"])

    # Find matching vendor
    vendor = await vendors_col().find_one(
        {"crops_accepted": {"$regex": data.crop_name, "$options": "i"}, "active": True}
    )

    # Save interest
    await exotic_recommendations_col().update_one(
        {"user_id": user_id, "crop_name": data.crop_name},
        {"$set": {"interested": True, "interested_at": datetime.now(timezone.utc).isoformat()}},
    )

    # Email vendor if found
    if vendor and vendor.get("contact"):
        import asyncio

        async def notify():
            vendor_email = vendor.get("email", vendor.get("contact", ""))
            if "@" in vendor_email:
                await send_vendor_introduction(
                    vendor_email,
                    vendor.get("name", "Vendor"),
                    current_user.get("username", "Farmer"),
                    current_user.get("email", ""),
                    data.crop_name,
                )

        asyncio.create_task(notify())

    return {
        "status": "success",
        "message": f"Interest recorded for {data.crop_name}",
        "vendor_notified": bool(vendor),
    }
