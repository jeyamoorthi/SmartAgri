import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv

from db.mongodb import users_col
from models.user import UserCreate, UserLogin, UserResponse, Token, ProfileUpdate
from services.soil_service import fetch_soil_data
from services.weather_service import fetch_weather_data
from services.cluster_service import assign_cluster

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "smartagri_jwt_secret_key_2026_super_secure")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

def create_token(user_id: str, email: str) -> str:
    """Create a JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    """Dependency to extract and validate JWT from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
        
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
        
    from bson import ObjectId
    user = await users_col().find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    user["id"] = str(user["_id"])
    return user

def _user_to_response(user: dict) -> dict:
    soil_data = user.get("soil_data") or {}
    soil_ph = soil_data.get("ph") if isinstance(soil_data, dict) else 6.5
    if soil_ph is None:
        soil_ph = 6.5
        
    farmer_profile = {
        "name": user.get("username", ""),
        "language": user.get("preferred_language", "en"),
        "state": user.get("state", "Tamil Nadu"),
        "district": user.get("district", "Coimbatore"),
        "crop": user.get("present_crop", "tomato"),
        "crop_stage": user.get("present_crop_stage", "vegetative"),
        "farm_size": float(user.get("land_acres", 2.0)),
        "soil_type": user.get("soil_type", "Red Soil"),
        "soil_ph": float(soil_ph),
        "last_market_query": user.get("last_market_query", ""),
        "last_disease_query": user.get("last_disease_query", ""),
        "last_recommendation": user.get("last_recommendation", ""),
        "session_context": user.get("session_context") or []
    }

    return {
        "id": str(user.get("_id", user.get("id", ""))),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "present_crop": user.get("present_crop", ""),
        "present_crop_stage": user.get("present_crop_stage", ""),
        "land_acres": user.get("land_acres", 0),
        "gps_coordinates": user.get("gps_coordinates", {}),
        "past_crop": user.get("past_crop", ""),
        "past_disease": user.get("past_disease", ""),
        "soil_data": user.get("soil_data"),
        "weather_data": user.get("weather_data"),
        "cluster_id": user.get("cluster_id"),
        "preferred_language": user.get("preferred_language", "en"),
        "state": user.get("state", "Tamil Nadu"),
        "district": user.get("district", "Coimbatore"),
        "soil_type": user.get("soil_type", "Red Soil"),
        "farmer_profile": farmer_profile
    }

@router.post("/signup", response_model=Token)
async def signup(data: UserCreate):
    col = users_col()
    existing = await col.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed = pwd_context.hash(data.password)
    user_doc = {
        "username": data.username,
        "email": data.email,
        "password_hash": hashed,
        "present_crop": data.present_crop,
        "present_crop_stage": data.present_crop_stage.value,
        "land_acres": data.land_acres,
        "gps_coordinates": {
            "lat": data.gps_coordinates.lat,
            "lng": data.gps_coordinates.lng
        },
        "past_crop": data.past_crop,
        "past_disease": data.past_disease,
        "soil_data": None,
        "weather_data": None,
        "cluster_id": None,
        "state": data.state or "Tamil Nadu",
        "district": data.district or "Coimbatore",
        "soil_type": data.soil_type or "Red Soil",
        "preferred_language": data.preferred_language or "en",
        "last_market_query": "",
        "last_disease_query": "",
        "last_recommendation": "",
        "session_context": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await col.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    import asyncio
    async def enrich_user():
        try:
            lat = data.gps_coordinates.lat
            lng = data.gps_coordinates.lng
            
            soil_task = fetch_soil_data(lat, lng)
            weather_task = fetch_weather_data(lat, lng)
            cluster_task = assign_cluster(lat, lng)
            
            soil_data, weather_data, cluster_id = await asyncio.gather(
                soil_task, weather_task, cluster_task
            )
            
            from bson import ObjectId
            await col.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "soil_data": soil_data,
                    "weather_data": weather_data,
                    "cluster_id": cluster_id,
                }}
            )
            print(f"[INFO] User {user_id} enriched: soil + weather + cluster={cluster_id}")
        except Exception as e:
            print(f"[WARNING] Background enrichment failed for {user_id}: {e}")
            
    asyncio.create_task(enrich_user())
    
    token = create_token(user_id, data.email)
    user_doc["id"] = user_id
    return Token(
        access_token=token,
        user=UserResponse(**_user_to_response(user_doc))
    )

@router.post("/login", response_model=Token)
async def login(data: UserLogin):
    col = users_col()
    user = await col.find_one({"email": data.email})
    if not user or not pwd_context.verify(data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    user_id = str(user["_id"])
    token = create_token(user_id, data.email)
    user["id"] = user_id
    return Token(
        access_token=token,
        user=UserResponse(**_user_to_response(user))
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    col = users_col()
    update_data = {}
    if data.name is not None:
        update_data["username"] = data.name
    if data.language is not None:
        update_data["preferred_language"] = data.language
    if data.state is not None:
        update_data["state"] = data.state
    if data.district is not None:
        update_data["district"] = data.district
    if data.crop is not None:
        update_data["present_crop"] = data.crop
    if data.crop_stage is not None:
        update_data["present_crop_stage"] = data.crop_stage
    if data.farm_size is not None:
        update_data["land_acres"] = data.farm_size
    if data.soil_type is not None:
        update_data["soil_type"] = data.soil_type
    if data.soil_ph is not None:
        soil_data = current_user.get("soil_data") or {}
        if not isinstance(soil_data, dict):
            soil_data = {}
        soil_data["ph"] = data.soil_ph
        update_data["soil_data"] = soil_data
        
    if update_data:
        from bson import ObjectId
        await col.update_one({"_id": ObjectId(current_user["id"])}, {"$set": update_data})
        # Fetch updated user
        updated_user = await col.find_one({"_id": ObjectId(current_user["id"])})
        updated_user["id"] = str(updated_user["_id"])
        return _user_to_response(updated_user)
        
    return _user_to_response(current_user)

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return _user_to_response(current_user)
