import requests
import json
from typing import Dict, Any, List, Optional
from app.core.config import settings

class MCPClient:
    def __init__(self):
        self.mcp_base_url = settings.MCP_SERVER_URL
        self.dashboard_agent_url = settings.DASHBOARD_AGENT_URL
        self.credit_analysis_url = settings.CREDIT_ANALYSIS_URL
        self.rule_saver_url = settings.RULE_SAVER_URL
        self._available_tools = None  # Cache for available tools

    def call_tool(self, tool_call_json: str):
        """
        Executes a tool call against the MCP server.
        Expects a JSON string like the one in your example.
        """
        try:
            payload = json.loads(tool_call_json)
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.mcp_base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for tool call."}
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to call MCP server: {e}"}

    def call_dashboard_agent(self, question: str):
        """
        Executes a query against the dashboard agent API.
        """
        try:
            payload = {"question": question}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.dashboard_agent_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to call Dashboard Agent: {e}"}

    def call_credit_analysis(self, metadata: dict):
        """
        Executes a credit analysis request.
        """
        try:
            payload = {"input": {"metadata": json.dumps(metadata)}}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.credit_analysis_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to call Credit Analysis API: {e}"}

    def call_rule_saver(self, rule_data: dict):
        """
        Executes a rule saver request.
        """
        try:
            # The payload structure seems to be {"input": {"metadata": "..."}} where metadata is a JSON string
            # We will replicate this structure
            payload = {"input": {"metadata": json.dumps(rule_data)}}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.rule_saver_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to call Rule Saver API: {e}"}

    def get_available_tools(self, force_refresh=False):
        """
        Return available MCP tools. For now, only weather tool is available.
        """
        if self._available_tools is not None and not force_refresh:
            return self._available_tools
        
        # Define available tools - weather tool using OpenWeather API
        tools_data = {
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get current weather for a location using OpenWeather API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name, coordinates, or zip code"
                            },
                            "units": {
                                "type": "string",
                                "description": "Temperature units (metric, imperial)",
                                "default": "metric"
                            }
                        },
                        "required": ["location"]
                    }
                }
            ]
        }
        
        self._available_tools = tools_data
        print(f"Available MCP tools: {[tool['name'] for tool in tools_data['tools']]}")
        return tools_data
    
    def call_mcp_tool(self, tool_name: str, parameters: dict):
        """
        Call a specific MCP tool with parameters.
        """
        print(f"Calling MCP tool: {tool_name} with parameters: {parameters}")
        
        # Handle weather tool directly
        if tool_name == "get_weather":
            return self._call_weather_tool(parameters)
        
        # For other tools, return error
        return {"error": f"Unknown MCP tool: {tool_name}"}
    
    def _call_weather_tool(self, parameters: dict):
        """Call the weather tool using OpenWeather API"""
        try:
            location = parameters.get("location")
            units = parameters.get("units", "metric")
            
            if not location:
                return {"error": "Location parameter is required"}
            
            # Use your OpenWeather API key
            api_key = "ce16d097e61ac8cab4364fafeadaedbf"
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            
            # Build API URL based on location format
            if "," in location and location.replace(",", "").replace(".", "").replace("-", "").isdigit():
                # Coordinates: "lat,lon"
                lat, lon = location.split(",")
                url = f"{base_url}?lat={lat}&lon={lon}&appid={api_key}&units={units}"
            else:
                # City name or zip code
                url = f"{base_url}?q={location}&appid={api_key}&units={units}"
            
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response nicely
            weather_info = {
                "location": f"{data['name']}, {data['sys']['country']}",
                "temperature": f"{data['main']['temp']}°{'C' if units == 'metric' else 'F'}",
                "feels_like": f"{data['main']['feels_like']}°{'C' if units == 'metric' else 'F'}",
                "description": data['weather'][0]['description'].title(),
                "humidity": f"{data['main']['humidity']}%",
                "wind_speed": f"{data['wind']['speed']} {'m/s' if units == 'metric' else 'mph'}",
                "pressure": f"{data['main']['pressure']} hPa"
            }
            
            return {
                "result": weather_info,
                "success": True
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch weather data: {str(e)}"}
        except Exception as e:
            return {"error": f"Error processing weather data: {str(e)}"}
