"""
Pydantic models for user-related schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum


class CropStage(str, Enum):
    SOWING = "sowing"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    HARVEST = "harvest"


class GPSCoordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class SoilData(BaseModel):
    nitrogen_kg_ha: Optional[float] = None
    phosphorus_kg_ha: Optional[float] = None
    potassium_kg_ha: Optional[float] = None
    ph: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    texture: Optional[str] = None
    source: str = "SoilGrids"
    fetched_at: Optional[str] = None


class WeatherDataStored(BaseModel):
    temp: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    condition: Optional[str] = None
    forecast: Optional[list] = None
    fetched_at: Optional[str] = None


# ── Auth Schemas ──────────────────────────────────────────────────────────────

class FarmerProfile(BaseModel):
    name: str = ""
    language: str = "en"
    state: str = "Tamil Nadu"
    district: str = "Coimbatore"
    crop: str = "tomato"
    crop_stage: str = "vegetative"
    farm_size: float = 2.0
    soil_type: str = "Red Soil"
    soil_ph: float = 6.5
    last_market_query: Optional[str] = ""
    last_disease_query: Optional[str] = ""
    last_recommendation: Optional[str] = ""
    session_context: Optional[List[dict]] = []


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    present_crop: str
    present_crop_stage: CropStage
    land_acres: float
    gps_coordinates: GPSCoordinates
    past_crop: Optional[str] = ""
    past_disease: Optional[str] = ""
    state: Optional[str] = "Tamil Nadu"
    district: Optional[str] = "Coimbatore"
    soil_type: Optional[str] = "Red Soil"
    preferred_language: Optional[str] = "en"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    present_crop: str
    present_crop_stage: str
    land_acres: float
    gps_coordinates: dict
    past_crop: Optional[str] = ""
    past_disease: Optional[str] = ""
    soil_data: Optional[dict] = None
    weather_data: Optional[dict] = None
    cluster_id: Optional[str] = None
    preferred_language: Optional[str] = "en"
    state: Optional[str] = "Tamil Nadu"
    district: Optional[str] = "Coimbatore"
    soil_type: Optional[str] = "Red Soil"
    farmer_profile: Optional[FarmerProfile] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    crop: Optional[str] = None
    crop_stage: Optional[str] = None
    farm_size: Optional[float] = None
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Advisory Schemas ─────────────────────────────────────────────────────────

class IrrigationSlot(BaseModel):
    day: str
    time: str
    duration_mins: int
    method: str


class PestWarning(BaseModel):
    pest_name: str
    risk_level: str
    remedy: str


class HarvestPlan(BaseModel):
    expected_date: str
    yield_estimate: str
    post_harvest_tips: List[str]


class AdvisoryPlan(BaseModel):
    irrigation_schedule: List[IrrigationSlot]
    pest_warnings: List[PestWarning]
    harvest_plan: HarvestPlan
    sustainable_tips: List[str]


class AdvisoryPlanRequest(BaseModel):
    include_sustainable: bool = True


# ── Pest Schemas ──────────────────────────────────────────────────────────────

class PestReportCreate(BaseModel):
    pest_name: str
    severity: int = Field(..., ge=1, le=10)
    crop: str = ""
    image_base64: Optional[str] = None


class ProductOrder(BaseModel):
    product_id: str
    quantity: int = 1


# ── Market Schemas ────────────────────────────────────────────────────────────

class ProduceListingCreate(BaseModel):
    quantity_quintals: float
    expected_price: float
    available_from: str


# ── Recommendation Schemas ────────────────────────────────────────────────────

class CropInterest(BaseModel):
    crop_name: str


# ── Voice Chat Schema ────────────────────────────────────────────────────────

class VoiceChatRequest(BaseModel):
    audio_base64: str
    lang_code: str = "ta"
