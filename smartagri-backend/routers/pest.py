from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from db.mongodb import pest_alerts_col, products_col, users_col, orders_col
from models.user import PestReportCreate, ProductOrder
from routers.auth import get_current_user
from services.cluster_service import get_nearby_users
from services.email_service import send_pest_alert, send_order_confirmation

router = APIRouter(prefix="/api/pest", tags=["pest"])

@router.post("/report")
async def report_pest(
    data: PestReportCreate,
    current_user: dict = Depends(get_current_user)
):
    """Report a pest sighting, notify nearby farmers, and recommend products."""
    user_id = str(current_user["_id"])
    coords = current_user.get("gps_coordinates", {})
    lat = coords.get("lat", 0)
    lng = coords.get("lng", 0)
    
    reporter_name = current_user.get("username", "Anonymous")
    crop = data.crop if data.crop else current_user.get("present_crop", "")
    
    alert_doc = {
        "reported_by_user_id": user_id,
        "reporter_name": reporter_name,
        "crop": crop,
        "pest_name": data.pest_name,
        "severity": data.severity,
        "location_coords": {"lat": lat, "lng": lng},
        "image_base64": data.image_base64,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notified_cluster": current_user.get("cluster_id", "")
    }
    
    result = await pest_alerts_col().insert_one(alert_doc)
    alert_id = str(result.inserted_id)
    
    nearby_users = await get_nearby_users(lat, lng)
    nearby_emails = [
        u["email"] for u in nearby_users
        if u.get("email") and str(u["_id"]) != user_id
    ]
    
    import asyncio
    async def send_alerts():
        location_desc = f"{lat:.2f}°N, {lng:.2f}°E (within 15km of your farm)"
        try:
            await send_pest_alert(
                nearby_emails,
                data.pest_name,
                data.severity,
                location_desc,
                alert_doc["crop"]
            )
        except Exception as e:
            print(f"[WARNING] Pest alert email failed: {e}")
            
    if nearby_emails:
        asyncio.create_task(send_alerts())
        
    products = await products_col().find(
        {"$or": [
            {"target_pest": {"$regex": data.pest_name, "$options": "i"}},
            {"target_pest": {"$regex": "general", "$options": "i"}}
        ]},
        {"_id": 1, "name": 1, "type": 1, "target_pest": 1, "price": 1, "delivery_days": 1, "in_stock": 1}
    ).to_list(length=20)
    
    for p in products:
        p["id"] = str(p.pop("_id"))
        
    return {
        "status": "success",
        "alert_id": alert_id,
        "nearby_farmers_notified": len(nearby_emails),
        "recommended_products": products
    }

@router.get("/alerts")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    """Fetch nearby pest alerts for the user's cluster or coordinates."""
    cluster_id = current_user.get("cluster_id", "")
    coords = current_user.get("gps_coordinates", {})
    lat = coords.get("lat", 0)
    lng = coords.get("lng", 0)
    
    alerts = await pest_alerts_col().find(
        {"$or": [
            {"notified_cluster": cluster_id},
            {"location_coords.lat": {"$gte": lat - 0.15, "$lte": lat + 0.15}}
        ]},
        {"_id": 1, "pest_name": 1, "severity": 1, "crop": 1, "timestamp": 1, "reporter_name": 1, "location_coords": 1}
    ).sort("timestamp", -1).to_list(length=50)
    
    for a in alerts:
        a["id"] = str(a.pop("_id"))
        
    return {"alerts": alerts}

@router.post("/order")
async def order_product(
    data: ProductOrder,
    current_user: dict = Depends(get_current_user)
):
    """Order a recommended crop protection product and confirm via email."""
    product = await products_col().find_one({"_id": ObjectId(data.product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    if not product.get("in_stock", False):
        raise HTTPException(status_code=400, detail="Product out of stock")
        
    order_doc = {
        "user_id": str(current_user["_id"]),
        "user_email": current_user.get("email", ""),
        "product_id": data.product_id,
        "product_name": product.get("name", ""),
        "quantity": data.quantity,
        "total_price": product.get("price", 0) * data.quantity,
        "delivery_days": product.get("delivery_days", 2),
        "status": "confirmed",
        "ordered_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await orders_col().insert_one(order_doc)
    
    import asyncio
    async def confirm():
        await send_order_confirmation(
            current_user.get("email", ""),
            product.get("name", ""),
            data.quantity,
            product.get("price", 0)
        )
        
    asyncio.create_task(confirm())
    
    return {
        "status": "confirmed",
        "order_id": str(result.inserted_id),
        "product": product.get("name", ""),
        "total": order_doc["total_price"],
        "delivery_days": order_doc["delivery_days"]
    }
