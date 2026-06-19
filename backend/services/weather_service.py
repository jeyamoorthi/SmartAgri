"""
OpenWeatherMap API integration.
Fetches current weather + 7-day forecast for given GPS coordinates.
"""
import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

OWM_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OWM_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


async def fetch_weather_data(lat: float, lon: float) -> dict:
    """
    Fetch current weather + 5-day/3-hour forecast from OpenWeatherMap.
    Returns structured dict with current conditions and daily forecast.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Current weather
            current_resp = await client.get(OWM_CURRENT_URL, params={
                "lat": lat, "lon": lon,
                "appid": OWM_API_KEY,
                "units": "metric",
            })
            current_resp.raise_for_status()
            current = current_resp.json()

            # 5-day forecast (3-hour intervals)
            forecast_resp = await client.get(OWM_FORECAST_URL, params={
                "lat": lat, "lon": lon,
                "appid": OWM_API_KEY,
                "units": "metric",
            })
            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()

        # Parse current weather
        weather = {
            "temp": current.get("main", {}).get("temp", 30.0),
            "humidity": current.get("main", {}).get("humidity", 65),
            "wind_speed": current.get("wind", {}).get("speed", 4.0),
            "condition": current.get("weather", [{}])[0].get("description", "clear sky"),
            "pressure": current.get("main", {}).get("pressure", 1010),
            "visibility": current.get("visibility", 10000),
            "clouds": current.get("clouds", {}).get("all", 0),
            "forecast": []
        }

        # Parse forecast data
        daily_forecasts = {}
        for entry in forecast_data.get("list", []):
            dt = datetime.fromtimestamp(entry["dt"], timezone.utc)
            day_key = dt.strftime("%Y-%m-%d")
            
            if day_key not in daily_forecasts:
                daily_forecasts[day_key] = {
                    "date": day_key,
                    "day": dt.strftime("%A"),
                    "temps": [],
                    "humidity": [],
                    "rain_mm": 0.0,
                    "conditions": []
                }
            
            df = daily_forecasts[day_key]
            df["temps"].append(entry["main"]["temp"])
            df["humidity"].append(entry["main"]["humidity"])
            df["conditions"].append(entry["weather"][0]["description"])
            
            # Check rain
            rain = entry.get("rain", {}).get("3h", 0.0)
            df["rain_mm"] += rain

        # Finalize daily forecast
        forecast = []
        for day_key in sorted(daily_forecasts.keys())[:7]:
            df = daily_forecasts[day_key]
            temps = df["temps"]
            forecast.append({
                "date": df["date"],
                "day": df["day"],
                "temp_max": round(max(temps), 1) if temps else 30.0,
                "temp_min": round(min(temps), 1) if temps else 20.0,
                "humidity": round(sum(df["humidity"]) / len(df["humidity"]), 0) if df["humidity"] else 60.0,
                "rainfall_mm": round(df["rain_mm"], 1),
                "condition": max(set(df["conditions"]), key=df["conditions"].count) if df["conditions"] else "clear sky",
            })

        weather["forecast"] = forecast
        weather["fetched_at"] = datetime.now(timezone.utc).isoformat()

        return weather

    except Exception as e:
        print(f"⚠ OpenWeatherMap API error: {e}")
        # Return sensible defaults for Tamil Nadu (tropical climate)
        return {
            "temp": 32.0,
            "humidity": 70,
            "wind_speed": 4.5,
            "condition": "partly cloudy",
            "pressure": 1010,
            "visibility": 8000,
            "clouds": 40,
            "forecast": [
                {
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "day": datetime.now(timezone.utc).strftime("%A"),
                    "temp_max": 34.0,
                    "temp_min": 26.0,
                    "humidity": 72,
                    "rainfall_mm": 0.0,
                    "condition": "partly cloudy",
                }
            ],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
