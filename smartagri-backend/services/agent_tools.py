import json
import re
from datetime import datetime, timezone
from db.mongodb import market_trends_col, vendors_col
from routers.subsidies import get_subsidies, SUBSIDIES_DATABASE
from services.weather_service import fetch_weather_data
from services.gemini_service import recommend_next_crop
from routers.natural_farming import TECHNIQUES, STRATEGIES

async def get_market_price(crop: str) -> dict:
    """
    Fetches mandi price, weekly trend, best buyer, and sell/hold recommendation for a crop.
    """
    crop_clean = crop.strip().lower()
    
    # Try to find in MongoDB trends
    trend = await market_trends_col().find_one(
        {"crop_name": {"$regex": crop_clean, "$options": "i"}},
        sort=[("timestamp", -1)]
    )
    
    if trend:
        price_qtl = trend.get("price_per_quintal", 2800)
        price_kg = round(price_qtl / 100.0, 1)
        direction = trend.get("price_trend", "stable")
    else:
        # Defaults
        if "tomato" in crop_clean:
            price_qtl = 2600
            price_kg = 26.0
            direction = "rising"
        elif "paddy" in crop_clean or "rice" in crop_clean:
            price_qtl = 2150
            price_kg = 21.5
            direction = "stable"
        else:
            price_qtl = 2800
            price_kg = 28.0
            direction = "stable"

    # Define dynamic trends
    if direction == "rising":
        trend_str = "+4% higher than yesterday"
        rec_str = "Hold harvest for 2 days to maximize profits"
    elif direction == "falling":
        trend_str = "-2% lower than yesterday"
        rec_str = "Sell harvest immediately to avoid price drops"
    else:
        trend_str = "Stable this week"
        rec_str = "Sell harvest on normal schedule"

    # Find matched vendor / buyer
    vendor = await vendors_col().find_one(
        {"crops_accepted": {"$regex": crop_clean, "$options": "i"}, "active": True}
    )
    if vendor:
        best_buyer_str = f"{vendor.get('name', 'Local Cooperative')} in {vendor.get('location', 'Nearby Mandi')}"
    else:
        if "tomato" in crop_clean:
            best_buyer_str = "Coimbatore Vegetable Mandi"
        elif "paddy" in crop_clean or "rice" in crop_clean:
            best_buyer_str = "Chennai Grain Merchant Association"
        else:
            best_buyer_str = "District Agro Marketing Cooperative"

    return {
        "crop": crop,
        "price": f"₹{price_kg}/kg (₹{price_qtl}/quintal)",
        "trend": trend_str,
        "best_buyer": best_buyer_str,
        "recommendation": rec_str
    }

async def get_weather(lat: float, lon: float) -> dict:
    """
    Fetches real-time weather and generates a ZBNF agricultural advisory.
    """
    w = await fetch_weather_data(lat, lon)
    temp = w.get("temp", 30.0)
    humidity = w.get("humidity", 65)
    condition = w.get("condition", "clear sky").lower()
    
    # Formulate organic farming advisory based on weather
    if "rain" in condition or "drizzle" in condition:
        advisory = "Rain expected. Postpone foliar sprays of Jivamrita/Agniastra. Ensure drainage trenches are clear."
    elif temp > 35.0:
        advisory = "High temperature. Increase mulching thickness to conserve soil moisture. Irrigate using alternate furrows (Whapasa method)."
    else:
        advisory = "Favorable weather. Excellent time to apply fermented Jivamrita (1:10 dilution) to boost soil microbes."
        
    return {
        "temp": f"{temp}°C",
        "humidity": f"{humidity}%",
        "condition": condition.capitalize(),
        "organic_advisory": advisory
    }

async def get_schemes(state: str, crop: str, farm_size: float) -> dict:
    """
    Applies the subsidies Eligibility Engine to filter government support schemes.
    """
    # Simply call the get_subsidies controller mapping
    res = await get_subsidies(state=state, crop=crop, farm_size=farm_size, current_user={})
    return res

async def get_crop_recommendation(state: str, crop: str, soil_type: str, farm_size: float) -> dict:
    """
    Queries the crop recommendation service.
    """
    mock_market = [
        {"crop_name": "Tomato", "price_per_quintal": 2600, "demand_level": "High"},
        {"crop_name": "Paddy", "price_per_quintal": 2150, "demand_level": "Medium"}
    ]
    profile = {
        "state": state,
        "crop": crop,
        "soil_type": soil_type,
        "farm_size": farm_size,
        "land_acres": farm_size
    }
    reco = await recommend_next_crop(profile, mock_market)
    return reco

async def diagnose_disease(disease_name: str, crop_context: str = "") -> dict:
    """
    Provides remedies and prevention for plant diseases.
    """
    d_clean = disease_name.strip().lower()
    c_clean = crop_context.strip().lower() if crop_context else "crop"
    
    # Base remedies dictionary
    disease_data = {
        "early blight": {
            "disease_name": "Early Blight",
            "severity_level": "Medium (5/10)",
            "organic_remedies": [
                "Spray 5% Neem Seed Kernel Extract (NSKE) at weekly intervals.",
                "Apply Sour Buttermilk spray (1L sour buttermilk + 20L water) every 10 days."
            ],
            "prevention_steps": [
                "Ensure proper row spacing for optimal air circulation.",
                "Practice mulching to prevent soil splashing onto lower leaves."
            ]
        },
        "leaf spot": {
            "disease_name": "Leaf Spot",
            "severity_level": "Moderate (4/10)",
            "organic_remedies": [
                "Spray Ginger-Garlic-Chilli extract (Agniastra formulation) at 2% concentration.",
                "Apply light dusting of wood ash on leaves in early morning."
            ],
            "prevention_steps": [
                "Remove and burn infected crop residues.",
                "Avoid overhead irrigation; water at soil level."
            ]
        },
        "stem borer": {
            "disease_name": "Stem Borer",
            "severity_level": "High (7/10)",
            "organic_remedies": [
                "Release Trichogramma chilonis egg parasitoids (2 cards/acre).",
                "Spray Neemastra (5L cow urine + 5kg neem leaves fermented for 24h) at 3% concentration."
            ],
            "prevention_steps": [
                "Clip and destroy seedling tips before transplanting.",
                "Use light traps to monitor and catch adult moths."
            ]
        }
    }
    
    # Match disease
    matched = None
    for k, v in disease_data.items():
        if k in d_clean:
            matched = v
            break
            
    if not matched:
        # Generic ZBNF disease response
        matched = {
            "disease_name": disease_name.capitalize() if disease_name else "Fungal/Insect Damage",
            "severity_level": "Moderate (4/10)",
            "organic_remedies": [
                "Spray Jivamrita (1:10 dilution with water) to boost leaf immunity.",
                "Spray 5% Neem Oil (5ml Neem oil + 1ml liquid soap emulsified in 1L water)."
            ],
            "prevention_steps": [
                "Maintain broad crop diversity (intercropping).",
                "Maintain healthy soil biology through crop mulching."
            ]
        }
    return matched

async def get_natural_farming_guide(topic: str) -> dict:
    """
    Retrieves ZBNF natural farming guidelines, recipes, and multilevel cropping designs.
    """
    topic_clean = topic.strip().lower()
    
    # 5-layer multilevel cropping check
    if "multilevel" in topic_clean or "5-layer" in topic_clean or "five layer" in topic_clean or "layer" in topic_clean:
        return {
            "title": "5-Layer Multilevel Cropping Model",
            "type": "cropping_strategy",
            "concept": "Maximizing vertical solar space and root depth layers, mimicking a natural forest ecosystem.",
            "guide_text": "Multilevel cropping layers plants of different heights and root depths. Layer 1 (Canopy): Coconut/Areca nut. Layer 2 (Tall): Banana/Moringa. Layer 3 (Shrub): Coffee/Lemon. Layer 4 (Ground): Chilli/Turmeric. Layer 5 (Root): Tapioca/Yam.",
            "layers": STRATEGIES["five_layer_model"]["layers"]
        }
        
    # Standard ZBNF inputs (Jivamrita, Beejamrita, etc.)
    for tech in TECHNIQUES:
        if tech["name"].lower() in topic_clean:
            return {
                "title": tech["name"],
                "type": "recipe",
                "guide_text": tech["description"],
                "ingredients": tech.get("ingredients", ""),
                "preparation": tech.get("preparation", ""),
                "application": tech.get("application", "")
            }
            
    # Default ZBNF overview
    return {
        "title": "Zero Budget Natural Farming (ZBNF)",
        "type": "overview",
        "guide_text": "ZBNF is a method of chemical-free agriculture based on Subhash Palekar's principles. Its four pillars are: Jiwamrita (soil inoculant), Beejamrita (seed treatment), Acchadana (mulching), and Whapasa (soil aeration & moisture conservation).",
        "pillars": [
            "Jiwamrita: Fermented microbial culture used as soil input.",
            "Beejamrita: Seed coating using cow dung/urine to protect roots.",
            "Acchadana (Mulching): Soil covering to conserve moisture.",
            "Whapasa: Aeration microclimate in root zone."
        ]
    }
