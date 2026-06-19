from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from bson import ObjectId

from db.mongodb import market_trends_col, vendors_col, produce_listings_col, users_col
from models.user import ProduceListingCreate
from routers.auth import get_current_user
from services.email_service import send_email

router = APIRouter(prefix="/api/market", tags=["market"])

@router.get("/trends")
async def get_trends(current_user: dict = Depends(get_current_user)):
    """Get last 30 days of price data for user's current crop."""
    crop = current_user.get("present_crop", "paddy")
    trends = await market_trends_col().find(
        {"crop_name": {"$regex": crop, "$options": "i"}},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(length=60)
    
    if not trends:
        trends = await market_trends_col().find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(length=30)
        
    if len(trends) >= 2:
        recent_price = trends[-1].get("price_per_quintal", 0)
        older_price = trends[0].get("price_per_quintal", 0)
        if recent_price > older_price * 1.02:
            trend_direction = "rising"
        elif recent_price < older_price * 0.98:
            trend_direction = "falling"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "stable"
        
    prices = [t.get("price_per_quintal", 0) for t in trends if t.get("price_per_quintal") is not None]
    avg_price = round(sum(prices) / len(prices), 2) if prices else 0
    
    return {
        "crop": crop,
        "trends": trends,
        "trend_direction": trend_direction,
        "average_price": avg_price,
        "data_points": len(trends)
    }

@router.get("/vendors")
async def get_vendors(current_user: dict = Depends(get_current_user)):
    """Get list of active vendors accepting farmer's crop."""
    crop = current_user.get("present_crop", "paddy")
    vendors = await vendors_col().find(
        {"active": True},
        {"_id": 1, "name": 1, "location": 1, "crops_accepted": 1, "contact": 1}
    ).to_list(length=50)
    
    matched = []
    for v in vendors:
        v["id"] = str(v.pop("_id"))
        crops = v.get("crops_accepted", [])
        if isinstance(crops, list):
            if any(crop.lower() in c.lower() for c in crops):
                v["match"] = True
                matched.insert(0, v)
            else:
                v["match"] = False
                matched.append(v)
        else:
            matched.append(v)
            
    return {"vendors": matched, "crop": crop}

@router.post("/sell")
async def list_produce(
    data: ProduceListingCreate,
    current_user: dict = Depends(get_current_user)
):
    """List farmer's produce for sale and notify matching vendors."""
    user_id = str(current_user["_id"])
    crop = current_user.get("present_crop", "paddy")
    
    listing_doc = {
        "user_id": user_id,
        "farmer_name": current_user.get("username", ""),
        "farmer_email": current_user.get("email", ""),
        "crop": crop,
        "quantity_quintals": data.quantity_quintals,
        "expected_price": data.expected_price,
        "available_from": data.available_from,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await produce_listings_col().insert_one(listing_doc)
    vendors = await vendors_col().find({"active": True}).to_list(length=50)
    
    import asyncio
    async def notify_vendors():
        for vendor in vendors:
            crops = vendor.get("crops_accepted", [])
            vendor_email = vendor.get("email", vendor.get("contact", ""))
            if isinstance(crops, list):
                if any(crop.lower() in c.lower() for c in crops):
                    if "@" in str(vendor_email):
                        subject = f"🌾 New Produce Listing – {crop} | SmartAgri"
                        html = f"""
                        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #FAFAF7; border-radius: 16px; overflow: hidden;">
                            <div style="background: linear-gradient(135deg, #2D6A4F, #74C69D); padding: 30px; text-align: center;">
                                <h1 style="color: white; margin: 0;">🌾 New Produce Available</h1>
                            </div>
                            <div style="padding: 30px;">
                                <p>A SmartAgri farmer has listed produce that matches your interest:</p>
                                <div style="background: #E8F5E9; border-radius: 12px; padding: 20px; margin: 15px 0;">
                                    <p><strong>🌱 Crop:</strong> {crop}</p>
                                    <p><strong>📦 Quantity:</strong> {data.quantity_quintals} quintals</p>
                                    <p><strong>💰 Expected Price:</strong> ₹{data.expected_price}/quintal</p>
                                    <p><strong>📅 Available From:</strong> {data.available_from}</p>
                                    <p><strong>🧑‍🌾 Farmer:</strong> {current_user.get("username", "")}</p>
                                </div>
                                <p>Contact the farmer at: {current_user.get("email", "")}</p>
                            </div>
                        </div>
                        """
                        await send_email(vendor_email, subject, html)
                        
    asyncio.create_task(notify_vendors())
    
    return {
        "status": "success",
        "listing_id": str(result.inserted_id),
        "message": "Produce listed. Matched vendors will be notified."
    }
