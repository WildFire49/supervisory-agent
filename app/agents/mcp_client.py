import asyncio
import json
from typing import Dict, Any, List, Optional
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    """MCP-compliant HTTP client for dynamic tool and resource discovery and execution."""
    
    def __init__(self):
        self.server_url = settings.MCP_SERVER_URL
        self.api_key = settings.MCP_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self._available_tools = None
        self._available_resources = None
        self._tools_cache_valid = False
        self._resources_cache_valid = False
        
        # Initialize connection and discover capabilities
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize connection and test server availability."""
        try:
            print(f"🔗 Connecting to MCP server at {self.server_url}")
            
            # Test connection with health check
            import requests
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Successfully connected to MCP server")
                # Discover capabilities on initialization
                self._discover_capabilities()
            else:
                print(f"⚠️ MCP server responded with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            print(f"   Make sure the MCP server is running at {self.server_url}")

    def _discover_capabilities(self):
        """Discover available tools and resources from the MCP server via OpenAPI schema."""
        try:
            import requests
            
            # Get OpenAPI schema to discover tools
            response = requests.get(f"{self.server_url}/openapi.json", timeout=10)
            response.raise_for_status()
            schema = response.json()
            
            # Parse tools from OpenAPI paths
            tools = []
            paths = schema.get("paths", {})
            for path, methods in paths.items():
                # Skip system endpoints
                if path in ["/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc", "/health"]:
                    continue
                    
                for method, details in methods.items():
                    if details.get('deprecated'):
                        continue
                        
                    tool_name = details.get("summary") or path.strip("/").replace("-", "_")
                    tools.append({
                        "name": tool_name,
                        "description": details.get("description", ""),
                        "path": path,
                        "method": method.upper(),
                        "parameters": self._extract_parameters_from_schema(details)
                    })
            
            self._available_tools = tools
            self._tools_cache_valid = True
            
            # For now, assume no resources (can be extended later)
            self._available_resources = []
            self._resources_cache_valid = True
            
            print(f"📋 Discovered {len(tools)} tools")
            print(f"🔧 Available tools: {[tool['name'] for tool in tools]}")
            
        except Exception as e:
            print(f"❌ Failed to discover server capabilities: {e}")
            self._available_tools = []
            self._available_resources = []
    
    def _extract_parameters_from_schema(self, endpoint_details: dict) -> dict:
        """Extract parameter schema from OpenAPI endpoint details."""
        parameters = {}
        
        # Extract from requestBody if it exists (for POST requests)
        request_body = endpoint_details.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            if schema:
                parameters = schema
        
        # Extract from parameters (for GET requests)
        params = endpoint_details.get("parameters", [])
        if params:
            properties = {}
            required = []
            for param in params:
                param_name = param.get("name")
                param_schema = param.get("schema", {})
                if param_name:
                    properties[param_name] = param_schema
                    if param.get("required", False):
                        required.append(param_name)
            
            if properties:
                parameters = {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
        
        return parameters

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

    def call_mcp_tool(self, tool_name: str, parameters: dict):
        """Call a specific MCP tool via HTTP following MCP principles."""
        print(f"🔧 Calling MCP tool: {tool_name} with parameters: {parameters}")
        
        # Refresh tools if cache is invalid
        if not self._tools_cache_valid:
            self._discover_capabilities()
        
        # Find the tool
        tool = next((t for t in self._available_tools if t["name"] == tool_name), None)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found on server"}
        
        try:
            import requests
            
            url = f"{self.server_url}{tool['path']}"
            method = tool['method']
            
            # Make HTTP request based on method
            if method == 'GET':
                response = requests.get(url, params=parameters, headers=self.headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=parameters, headers=self.headers, timeout=30)
            else:
                return {"error": f"Unsupported HTTP method '{method}' for tool '{tool_name}'"}
            
            response.raise_for_status()
            result = response.json()
            
            # Return in MCP-compatible format
            return {"result": result}
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"error": f"Tool endpoint not found: {url}"}
            elif e.response.status_code == 401:
                return {"error": "Authentication failed - check MCP API key"}
            else:
                try:
                    error_details = e.response.json().get('detail', str(e))
                except:
                    error_details = str(e)
                return {"error": f"HTTP error calling tool: {error_details}"}
        except Exception as e:
            return {"error": f"Failed to call MCP tool: {e}"}

    def get_available_tools(self, force_refresh=False):
        """Get available tools from the MCP server."""
        if not self._tools_cache_valid or force_refresh:
            self._discover_capabilities()
        
        return {"tools": self._available_tools or []}

    def get_available_resources(self, force_refresh=False):
        """Get available resources from the MCP server."""
        if not self._resources_cache_valid or force_refresh:
            self._discover_capabilities()
        
        return {"resources": self._available_resources or []}

    def read_resource(self, uri: str):
        """Read a specific resource from the MCP server."""
        # For now, resources are not implemented in our FastMCP server
        # This can be extended when resources are added
        return {"error": "Resources not yet implemented in this MCP server"}

    def refresh_capabilities(self):
        """Force refresh the tools and resources cache from the MCP server."""
        print("🔄 Refreshing MCP server capabilities...")
        self._tools_cache_valid = False
        self._resources_cache_valid = False
        self._discover_capabilities()
        return self.get_available_tools(force_refresh=True)
    
    def list_tool_names(self) -> List[str]:
        """Get a list of available tool names."""
        tools_data = self.get_available_tools()
        return [tool['name'] for tool in tools_data.get('tools', [])]
    
    def list_resource_uris(self) -> List[str]:
        """Get a list of available resource URIs."""
        resources_data = self.get_available_resources()
        return [resource['uri'] for resource in resources_data.get('resources', [])]
