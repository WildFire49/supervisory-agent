import os
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from pydantic import BaseModel

load_dotenv()

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Supervisory Agent MCP Server",
    description="A server providing various tools for the supervisory agent",
    version="1.0.0"
)

# --- Security and Authentication ---
security = HTTPBearer()
API_KEY = os.getenv("MCP_API_KEY", "your-secret-api-key")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# --- API Endpoints as Tools ---

@app.get("/get_weather", dependencies=[Depends(verify_api_key)])
def get_weather(location: str, units: str = "metric") -> dict:
    """Get current weather information for a specified location."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenWeather API key not configured")
    
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": location, "appid": api_key, "units": units}
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Format the response
        unit_symbol = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
        speed_unit = "m/s" if units == "metric" else "mph" if units == "imperial" else "m/s"
        
        return {
            "location": f"{data['name']}, {data['sys']['country']}",
            "temperature": f"{data['main']['temp']}{unit_symbol}",
            "feels_like": f"{data['main']['feels_like']}{unit_symbol}",
            "description": data['weather'][0]['description'].title(),
            "humidity": f"{data['main']['humidity']}%",
            "wind_speed": f"{data['wind']['speed']} {speed_unit}",
            "pressure": f"{data['main']['pressure']} hPa",
            "visibility": f"{data.get('visibility', 'N/A')} m" if data.get('visibility') else "N/A",
            "cloudiness": f"{data['clouds']['all']}%"
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {e}")

# @app.post("/calculate_bmi", dependencies=[Depends(verify_api_key)])
# def calculate_bmi(weight: float, height: float, unit_system: str = "metric") -> dict:
#     """Calculate Body Mass Index (BMI)."""
#     if unit_system == "imperial":
#         weight_kg = weight * 0.453592
#         height_m = (height * 2.54) / 100
#     else:
#         weight_kg = weight
#         height_m = height / 100
    
#     if height_m <= 0 or weight_kg <= 0:
#         raise HTTPException(status_code=400, detail="Weight and height must be positive")
    
#     bmi = weight_kg / (height_m ** 2)
    
#     if bmi < 18.5:
#         category = "Underweight"
#     elif bmi < 25:
#         category = "Normal weight"
#     elif bmi < 30:
#         category = "Overweight"
#     else:
#         category = "Obese"
        
#     return {"bmi": round(bmi, 2), "category": category, "weight_kg": round(weight_kg, 2), "height_m": round(height_m, 2)}

# @app.get("/get_random_quote", dependencies=[Depends(verify_api_key)])
# def get_random_quote() -> dict:
#     """Get a random inspirational quote."""
#     try:
#         response = requests.get("https://api.quotable.io/random", timeout=10)
#         response.raise_for_status()
#         data = response.json()
        
#         return {
#             "quote": data["content"],
#             "author": data["author"],
#             "tags": data.get("tags", [])
#         }
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "MCP Server"}

# --- MCP Server Generation and Execution ---

# Create an MCP server from the FastAPI app
mcp = FastMCP.from_fastapi(app=app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
