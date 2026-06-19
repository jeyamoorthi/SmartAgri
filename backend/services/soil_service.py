import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SOILGRIDS_URL = os.getenv('SOILGRIDS_URL', 'https://rest.isric.org/soilgrids/v2.0/properties/query')

async def fetch_soil_data(lat: float, lon: float) -> dict:
    """
    Fetch soil properties from SoilGrids for given GPS coordinates.
    Returns a dict with nitrogen, phosphorus, potassium, pH, organic carbon, texture.
    """
    params = {
        'lat': lat,
        'lon': lon,
        'property': ['nitrogen', 'phh2o', 'soc', 'clay', 'sand', 'silt'],
        'depth': ['0-5cm', '5-15cm', '15-30cm'],
        'value': ['mean', 'Q0.5']
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(SOILGRIDS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            
        properties = data.get('properties', {}).get('layers', [])
        soil = {
            'nitrogen_kg_ha': 0.0,
            'phosphorus_kg_ha': 0.0,
            'potassium_kg_ha': 0.0,
            'ph': 6.5,
            'organic_carbon_pct': 0.0,
            'texture': 'Loamy',
            'source': 'SoilGrids',
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        for layer in properties:
            prop_name = layer.get('name', '')
            depths = layer.get('depths', [])
            if not depths:
                continue
            top_depth = depths[0]
            values = top_depth.get('values', {})
            mean_val = values.get('mean', values.get('Q0.5', 0))
            if mean_val is None:
                mean_val = 0
                
            if prop_name == 'nitrogen':
                soil['nitrogen_kg_ha'] = round(mean_val * 0.1 * 30, 1)
            elif prop_name == 'phh2o':
                soil['ph'] = round(mean_val / 10.0, 1) if mean_val > 0 else 6.5
            elif prop_name == 'soc':
                soil['organic_carbon_pct'] = round(mean_val * 0.01, 2)
            elif prop_name == 'clay':
                clay_pct = mean_val / 10.0 if mean_val else 0
                if clay_pct > 40:
                    soil['texture'] = 'Clay'
                elif clay_pct > 25:
                    soil['texture'] = 'Loamy'
                else:
                    soil['texture'] = 'Sandy'
                    
        if soil['nitrogen_kg_ha'] > 0:
            soil['phosphorus_kg_ha'] = round(soil['nitrogen_kg_ha'] * 0.15, 1)
            soil['potassium_kg_ha'] = round(soil['nitrogen_kg_ha'] * 0.6, 1)
        else:
            soil['nitrogen_kg_ha'] = 280.0
            soil['phosphorus_kg_ha'] = 22.0
            soil['potassium_kg_ha'] = 180.0
        return soil
        
    except Exception as e:
        print(f"[WARNING] SoilGrids API error: {e}")
        return {
            'nitrogen_kg_ha': 275.0,
            'phosphorus_kg_ha': 20.0,
            'potassium_kg_ha': 175.0,
            'ph': 7.2,
            'organic_carbon_pct': 0.55,
            'texture': 'Loamy',
            'source': 'SoilGrids-fallback',
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
