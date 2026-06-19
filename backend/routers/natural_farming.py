from fastapi import APIRouter, Depends, HTTPException
from routers.auth import get_current_user
from core.ai_gateway import AIGateway

router = APIRouter(prefix="/api/natural-farming", tags=["natural-farming"])

TECHNIQUES = [
    {
        "name": "Jivamrita",
        "description": "Fermented microbial culture that acts as a soil inoculant. Increases soil microbial activity.",
        "ingredients": "Cow dung (10kg), Cow urine (10L), Jaggery (2kg), Pulse flour (2kg), Handful of soil, Water (200L).",
        "preparation": "Mix all ingredients in a barrel. Ferment for 2-7 days in shade. Stir twice daily.",
        "application": "Apply to soil with irrigation water or spray. Use 200L per acre twice a month."
    },
    {
        "name": "Beejamrita",
        "description": "Seed treatment mixture that protects young roots from fungi and soil-borne diseases.",
        "ingredients": "Cow dung (5kg), Cow urine (5L), Lime (50g), Handful of soil, Water (20L).",
        "preparation": "Mix dung, urine, soil, and water. Put lime in a small cloth and suspend in the mix overnight.",
        "application": "Coats seeds prior to sowing. Air dry in shade before planting."
    },
    {
        "name": "Mulching (Acchadana)",
        "description": "Covering the topsoil with crop residues or green manure crops to conserve moisture and build humus.",
        "types": [
            {"type": "Soil Mulch", "detail": "Shallow cultivation to break soil capillaries and prevent evaporation."},
            {"type": "Straw Mulch", "detail": "Covering with dried organic wastes, crop stalks, dry leaves."},
            {"type": "Live Mulch", "detail": "Intercropping with fast-growing cover crops like Cowpea or Sunnhemp."}
        ]
    },
    {
        "name": "Whapasa (Moisture Conservation)",
        "description": "Creating air-water vapor microclimate in the soil root zone, reducing irrigation requirements by up to 90%.",
        "method": "Water only at noon along alternate furrows. Maintain soil coverage with dry mulch."
    }
]

STRATEGIES = {
    "five_layer_model": {
        "title": "5-Layer Multilevel Cropping Model",
        "concept": "Maximizing vertical solar space and root depth layers, mimicking a natural forest ecosystem.",
        "layers": [
            {
                "layer": "Layer 1: Canopy (Emergent)",
                "height": "30+ feet",
                "crops": "Coconut, Areca nut",
                "role": "Top solar collector, windbreak"
            },
            {
                "layer": "Layer 2: Tall (Medium Trees)",
                "height": "15-20 feet",
                "crops": "Banana, Moringa, Papaya",
                "role": "Filter light for lower layers"
            },
            {
                "layer": "Layer 3: Shrub (Bushes)",
                "height": "6-8 feet",
                "crops": "Coffee, Lemon, Curry Leaves",
                "role": "Understory woody plants"
            },
            {
                "layer": "Layer 4: Ground Cover (Herbs)",
                "height": "1-3 feet",
                "crops": "Chilli, Turmeric, Ginger, Pulses",
                "role": "Prevent weed growth, fix nitrogen"
            },
            {
                "layer": "Layer 5: Root Crop (Sub-surface)",
                "height": "Below ground",
                "crops": "Tapioca, Sweet Potato, Yam",
                "role": "Optimize root space utilization"
            }
        ]
    }
}

PEST_REMEDIES = {
    "tomato": {
        "pest": "Fruit Borer & Early Blight",
        "remedy": "Spray 5% NSKE (Neem Seed Kernel Extract) for borers. Use Sour Buttermilk spray (5%) for Blight control."
    },
    "paddy": {
        "pest": "Stem Borer & Leaf Folder",
        "remedy": "Release Trichogramma chilonis parasites. Spray Agniastra (cow urine, neem, garlic, green chilli ferment) at 2% concentration."
    },
    "default": {
        "pest": "General Fungal & Sucking Pests",
        "remedy": "Spray Neem Oil (10,000 ppm) at 5ml/L mixed with soap emulsifier. Apply Dashaparni Ark (10-leaf extract) for broad insect control."
    }
}


@router.get("/techniques")
async def get_techniques():
    """Get list of standard organic/natural farming techniques."""
    return {"techniques": TECHNIQUES}


@router.get("/strategies")
async def get_strategies():
    """Get details on the 5-layer multilevel cropping model."""
    return STRATEGIES


@router.get("/pest-remedies/{crop}")
async def get_pest_remedies(crop: str):
    """Get organic pest remedies for a specific crop."""
    crop_key = crop.lower().strip()
    remedy = PEST_REMEDIES.get(crop_key, PEST_REMEDIES["default"])
    return {
        "crop": crop,
        "remedy": remedy
    }


@router.post("/plan")
async def generate_farming_plan(current_user: dict = Depends(get_current_user)):
    """
    Generate a personalized natural farming plan based on user profile.
    Uses AI Gateway for advisory generation.
    """
    try:
        crop = current_user.get("present_crop", "Tomato")
        soil_data = current_user.get("soil_data", {})
        soil = soil_data.get("texture", "Clay")
        prompt = f"Create a detailed 3-step natural farming transition plan for {crop} grown in {soil} soil."
        
        plan = await AIGateway.get_advisory(prompt, is_comprehensive=True, profile=current_user)
        return {
            "crop": crop,
            "soil": soil,
            "plan": plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))