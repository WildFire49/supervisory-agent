#!/usr/bin/env python3
"""
Simple Weather MCP Server
A lightweight FastAPI server that acts as an MCP server for weather data.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from typing import Dict, Any, List

app = FastAPI(
    title="Weather MCP Server",
    description="A simple MCP server providing weather tools via OpenWeather API",
    version="1.0.0"
)

# Your OpenWeather API key
OPENWEATHER_API_KEY = "ce16d097e61ac8cab4364fafeadaedbf"
OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"

class ToolCallRequest(BaseModel):
    method: str
    params: Dict[str, Any]

class ToolsResponse(BaseModel):
    tools: List[Dict[str, Any]]

@app.get("/tools", response_model=ToolsResponse)
async def get_tools():
    """Return available weather tools"""
    tools = [
        {
            "name": "get_current_weather",
            "description": "Get current weather for a location (city name, coordinates, or zip code)",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location (city name, 'lat,lon', or 'zip,country')"
                    },
                    "units": {
                        "type": "string",
                        "description": "Temperature units (metric, imperial, kelvin)",
                        "default": "metric"
                    }
                },
                "required": ["location"]
            }
        },
        {
            "name": "get_weather_forecast",
            "description": "Get 5-day weather forecast for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location (city name, 'lat,lon', or 'zip,country')"
                    },
                    "units": {
                        "type": "string",
                        "description": "Temperature units (metric, imperial, kelvin)",
                        "default": "metric"
                    }
                },
                "required": ["location"]
            }
        }
    ]
    return ToolsResponse(tools=tools)

@app.post("/")
async def call_tool(request: ToolCallRequest):
    """Handle MCP tool calls"""
    method = request.method
    params = request.params
    
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "get_current_weather":
            return await get_current_weather(arguments)
        elif tool_name == "get_weather_forecast":
            return await get_weather_forecast(arguments)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

async def get_current_weather(args: Dict[str, Any]):
    """Get current weather for a location"""
    location = args.get("location")
    units = args.get("units", "metric")
    
    if not location:
        return {"error": "Location is required"}
    
    try:
        # Build API URL based on location format
        if "," in location and location.replace(",", "").replace(".", "").replace("-", "").isdigit():
            # Coordinates: "lat,lon"
            lat, lon = location.split(",")
            url = f"{OPENWEATHER_BASE_URL}/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units={units}"
        elif location.isdigit() or ("," in location and any(c.isdigit() for c in location)):
            # ZIP code: "12345" or "12345,US"
            url = f"{OPENWEATHER_BASE_URL}/weather?zip={location}&appid={OPENWEATHER_API_KEY}&units={units}"
        else:
            # City name
            url = f"{OPENWEATHER_BASE_URL}/weather?q={location}&appid={OPENWEATHER_API_KEY}&units={units}"
        
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Format the response nicely
        weather_info = {
            "location": f"{data['name']}, {data['sys']['country']}",
            "temperature": f"{data['main']['temp']}°{'C' if units == 'metric' else 'F' if units == 'imperial' else 'K'}",
            "feels_like": f"{data['main']['feels_like']}°{'C' if units == 'metric' else 'F' if units == 'imperial' else 'K'}",
            "description": data['weather'][0]['description'].title(),
            "humidity": f"{data['main']['humidity']}%",
            "wind_speed": f"{data['wind']['speed']} {'m/s' if units == 'metric' else 'mph' if units == 'imperial' else 'm/s'}",
            "pressure": f"{data['main']['pressure']} hPa",
            "visibility": f"{data.get('visibility', 'N/A')} meters" if data.get('visibility') else "N/A"
        }
        
        return {
            "result": weather_info,
            "raw_data": data
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing weather data: {str(e)}"}

async def get_weather_forecast(args: Dict[str, Any]):
    """Get 5-day weather forecast for a location"""
    location = args.get("location")
    units = args.get("units", "metric")
    
    if not location:
        return {"error": "Location is required"}
    
    try:
        # Build API URL based on location format
        if "," in location and location.replace(",", "").replace(".", "").replace("-", "").isdigit():
            # Coordinates: "lat,lon"
            lat, lon = location.split(",")
            url = f"{OPENWEATHER_BASE_URL}/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units={units}"
        elif location.isdigit() or ("," in location and any(c.isdigit() for c in location)):
            # ZIP code: "12345" or "12345,US"
            url = f"{OPENWEATHER_BASE_URL}/forecast?zip={location}&appid={OPENWEATHER_API_KEY}&units={units}"
        else:
            # City name
            url = f"{OPENWEATHER_BASE_URL}/forecast?q={location}&appid={OPENWEATHER_API_KEY}&units={units}"
        
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Format the forecast nicely
        forecasts = []
        for item in data['list'][:10]:  # Get next 10 forecasts (about 2.5 days)
            forecast = {
                "datetime": item['dt_txt'],
                "temperature": f"{item['main']['temp']}°{'C' if units == 'metric' else 'F' if units == 'imperial' else 'K'}",
                "description": item['weather'][0]['description'].title(),
                "humidity": f"{item['main']['humidity']}%",
                "wind_speed": f"{item['wind']['speed']} {'m/s' if units == 'metric' else 'mph' if units == 'imperial' else 'm/s'}"
            }
            forecasts.append(forecast)
        
        return {
            "result": {
                "location": f"{data['city']['name']}, {data['city']['country']}",
                "forecasts": forecasts
            },
            "raw_data": data
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch forecast data: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing forecast data: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Weather MCP Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
