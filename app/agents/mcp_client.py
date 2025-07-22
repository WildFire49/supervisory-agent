import requests
import json
import os
from typing import Dict, Any, List, Optional
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        self.mcp_base_url = settings.MCP_SERVER_URL
        self.mcp_headers = {
            "Authorization": f"Bearer {settings.MCP_API_KEY}",
            "Content-Type": "application/json"
        }
        self._available_tools = None
        self._tools_cache_valid = False
        
        # Test connection to MCP server on initialization
        self._test_connection()

    def _test_connection(self):
        """Test connection to MCP server and log status"""
        try:
            response = requests.get(f"{self.mcp_base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Successfully connected to MCP server at {self.mcp_base_url}")
            else:
                print(f"⚠️ MCP server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            print(f"   Make sure the MCP server is running at {self.mcp_base_url}")

    def call_tool(self, tool_call_json: str):
        """
        Executes a tool call against the MCP server.
        Expects a JSON string with tool name and parameters.
        """
        try:
            payload = json.loads(tool_call_json)
            tool_name = payload.get("tool_name")
            parameters = payload.get("parameters", {})
            
            if not tool_name:
                return {"error": "Tool name is required in the payload"}
            
            return self.call_mcp_tool(tool_name, parameters)
            
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for tool call."}
        except Exception as e:
            return {"error": f"Failed to process tool call: {e}"}



    def get_available_tools(self, force_refresh=False):
        """Fetch available tools from the server's OpenAPI schema."""
        if self._tools_cache_valid and not force_refresh:
            return self._available_tools

        try:
            response = requests.get(f"{self.mcp_base_url}/openapi.json", timeout=10)
            response.raise_for_status()
            schema = response.json()
            
            tools = []
            paths = schema.get("paths", {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    # Ignore FastAPI default endpoints
                    if path in ["/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"] or details.get('deprecated'):
                        continue
                    
                    tool_name = details.get("summary") or path.strip("/")
                    tools.append({
                        "name": tool_name,
                        "path": path,
                        "method": method.upper(),
                        "description": details.get("description", ""),
                        "parameters": details.get("parameters", [])
                    })

            self._available_tools = {"tools": tools}
            self._tools_cache_valid = True
            print(f"📋 Available MCP tools: {[tool['name'] for tool in tools]}")
            return self._available_tools

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch OpenAPI schema: {e}")
            self._available_tools = {"tools": []}
            self._tools_cache_valid = False
            return self._available_tools
    
    def call_mcp_tool(self, tool_name: str, parameters: dict):
        """Call a specific MCP tool by dynamically building the request from the OpenAPI schema."""
        print(f"🔧 Calling MCP tool: {tool_name} with parameters: {parameters}")
        
        tool_schema = self.get_tool_schema(tool_name)
        if not tool_schema:
            return {"error": f"Tool '{tool_name}' not found or schema unavailable."}

        try:
            url = f"{self.mcp_base_url}{tool_schema['path']}"
            method = tool_schema['method']

            if method == 'GET':
                response = requests.get(url, params=parameters, headers=self.mcp_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=parameters, headers=self.mcp_headers, timeout=30)
            else:
                return {"error": f"Unsupported HTTP method '{method}' for tool '{tool_name}'."}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"error": f"Tool endpoint not found: {e.response.url}"}
            elif e.response.status_code == 401:
                return {"error": "Authentication failed - check MCP API key"}
            else:
                error_details = e.response.json().get('detail', e.response.text)
                return {"error": f"HTTP error calling tool: {error_details}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Network error calling MCP tool: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error calling MCP tool: {e}"}
    
    def refresh_tools_cache(self):
        """
        Force refresh the tools cache from the MCP server.
        """
        print("🔄 Refreshing tools cache...")
        self._tools_cache_valid = False
        return self.get_available_tools(force_refresh=True)
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """
        Get the schema for a specific tool.
        """
        tools_data = self.get_available_tools()
        for tool in tools_data.get('tools', []):
            if tool['name'] == tool_name:
                return tool
        return None
    
    def list_tool_names(self) -> List[str]:
        """
        Get a list of available tool names.
        """
        tools_data = self.get_available_tools()
        return [tool['name'] for tool in tools_data.get('tools', [])]
