from fastapi import APIRouter, Depends, Query
from typing import Optional
from routers.auth import get_current_user

router = APIRouter(prefix="/api/subsidies", tags=["subsidies"])

SUBSIDIES_DATABASE = [
    {
        "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "type": "Direct Income Support",
        "benefit": "Direct benefit transfer of Rs. 6,000 per year (in 3 equal installments of Rs. 2,000)",
        "estimated_benefit_amount": 6000,
        "eligibility": "All landholding farmer families across the country",
        "official_url": "https://pmkisan.gov.in/",
        "documents_required": ["Aadhaar Card", "Land ownership documents (Khata/Patta)", "Bank Account Passbook"],
        "applicable_states": ["all"],
        "applicable_crops": ["all"],
        "max_farm_size": None,
        "farming_type": "all"
    },
    {
        "name": "PKVY (Paramparagat Krishi Vikas Yojana)",
        "type": "Organic Transition Subsidy",
        "benefit": "Rs. 50,000 per hectare for 3 years (Rs. 31,000 direct for organic inputs like bio-fertilizers/seeds)",
        "estimated_benefit_amount": 50000,
        "eligibility": "Small and marginal farmers participating in organic clusters of 20 hectares",
        "official_url": "https://jaivikkheti.in/",
        "documents_required": ["Aadhaar Card", "Land records (Chitta/Patta)", "Bank Passbook", "Organic Cluster Membership ID"],
        "applicable_states": ["all"],
        "applicable_crops": ["all"],
        "max_farm_size": 5.0, # in acres
        "farming_type": "organic"
    },
    {
        "name": "Tamil Nadu State Organic Seed Subsidy",
        "type": "Seed Concession",
        "benefit": "50% price concession on certified organic seeds of Paddy, Pulses, and Millets at local AEC centers",
        "estimated_benefit_amount": 4000,
        "eligibility": "Registered organic farmers growing seeds in Tamil Nadu",
        "official_url": "https://www.tnagrisnet.tn.gov.in/",
        "documents_required": ["Aadhaar Card", "Organic Farming Certification", "Land Cultivation proof (Adangal)"],
        "applicable_states": ["tamil nadu"],
        "applicable_crops": ["paddy", "rice", "pulses", "millets"],
        "max_farm_size": None,
        "farming_type": "organic"
    },
    {
        "name": "PM-KMY (Pradhan Mantri Kisan Maan-Dhan Yojana)",
        "type": "Pension Support",
        "benefit": "Assured monthly pension of Rs. 3,000 upon reaching the age of 60 years",
        "estimated_benefit_amount": 36000,
        "eligibility": "Small and marginal landholders with up to 2 hectares (5 acres) of cultivable land",
        "official_url": "https://pmkmy.gov.in/",
        "documents_required": ["Aadhaar Card", "Bank Passbook", "Land holding Document (Patta/Chitta)"],
        "applicable_states": ["all"],
        "applicable_crops": ["all"],
        "max_farm_size": 5.0, # in acres
        "farming_type": "all"
    },
    {
        "name": "Sub-Mission on Agricultural Mechanization (SMAM)",
        "type": "Machinery Subsidy",
        "benefit": "40% to 50% financial assistance for purchasing tractors, power tillers, rotavators, and sprayers",
        "estimated_benefit_amount": 75000,
        "eligibility": "All category farmers (with priority and higher subsidy rates for Small/Marginal/Women farmers)",
        "official_url": "https://agrimachinery.nic.in/",
        "documents_required": ["Aadhaar Card", "Land ownership documents", "Bank details", "Caste certificate (if applicable)"],
        "applicable_states": ["all"],
        "applicable_crops": ["all"],
        "max_farm_size": None,
        "farming_type": "all"
    },
    {
        "name": "TN Sustainable Cotton Cultivation Mission (SCCM)",
        "type": "Crop Specific Subsidy",
        "benefit": "Subsidy for certified seeds, intercropping seeds, and organic inputs (biopesticides)",
        "estimated_benefit_amount": 8000,
        "eligibility": "Cotton growing farmers in Tamil Nadu",
        "official_url": "https://www.tnagrisnet.tn.gov.in/",
        "documents_required": ["Aadhaar Card", "Chitta/Adangal land record", "Bank Passbook"],
        "applicable_states": ["tamil nadu"],
        "applicable_crops": ["cotton"],
        "max_farm_size": None,
        "farming_type": "all"
    },
    {
        "name": "National Food Security Mission (NFSM) Paddy Support",
        "type": "Paddy Cultivation Support",
        "benefit": "Financial assistance of Rs. 5,000 per hectare for purchasing certified organic seeds and bio-fertilizers",
        "estimated_benefit_amount": 5000,
        "eligibility": "Paddy farmers in target districts of Tamil Nadu and other selected states",
        "official_url": "https://nfsm.gov.in/",
        "documents_required": ["Aadhaar Card", "Land records", "Soil Health Card copy", "Bank details"],
        "applicable_states": ["tamil nadu", "andhra pradesh", "telangana"],
        "applicable_crops": ["paddy", "rice"],
        "max_farm_size": None,
        "farming_type": "all"
    }
]

@router.get("/{state}")
async def get_subsidies(
    state: str,
    crop: Optional[str] = None,
    farm_size: Optional[float] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get government subsidies and schemes based on the farmer's state, crop, and farm size.
    Calculates estimated benefit and required documents.
    """
    profile = current_user.get("farmer_profile") or {}
    
    # Resolve parameters prioritizing current user profile
    s_state = profile.get("state", state) or state
    s_crop = crop or profile.get("crop") or current_user.get("present_crop", "tomato")
    try:
        s_size = float(farm_size) if farm_size is not None else float(profile.get("farm_size") or current_user.get("land_acres", 2.0))
    except Exception:
        s_size = 2.0

    state_clean = s_state.strip().lower()
    crop_clean = s_crop.strip().lower()
    
    eligible_schemes = []
    for scheme in SUBSIDIES_DATABASE:
        state_match = "all" in scheme["applicable_states"] or state_clean in [x.lower() for x in scheme["applicable_states"]]
        crop_match = "all" in scheme["applicable_crops"] or crop_clean in [x.lower() for x in scheme["applicable_crops"]]
        size_match = scheme["max_farm_size"] is None or s_size <= scheme["max_farm_size"]
        
        if state_match and crop_match and size_match:
            eligible_schemes.append(scheme)
            
    total_benefit = sum(scheme["estimated_benefit_amount"] for scheme in eligible_schemes)
    
    # Collect unique documents
    docs = []
    for scheme in eligible_schemes:
        for doc in scheme["documents_required"]:
            if doc not in docs:
                docs.append(doc)
                
    return {
        "state": s_state,
        "crop": s_crop,
        "farm_size": s_size,
        "subsidies": eligible_schemes,
        "estimated_benefit": total_benefit,
        "required_documents": docs
    }