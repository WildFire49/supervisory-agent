# MCP Server-Client Architecture Documentation

## Overview

This document provides a detailed explanation of how the MCP (Model Context Protocol) server and client communicate in our supervisory agent system. Our implementation uses HTTP-based communication with FastMCP on the server side and a custom HTTP client that follows MCP principles.

## System Architecture

```
┌─────────────────┐    HTTP Requests    ┌─────────────────┐
│  Supervisory    │ ──────────────────► │   MCP Server    │
│     Agent       │                     │  (FastMCP +     │
│                 │                     │   FastAPI)      │
│  ┌───────────┐  │                     │                 │
│  │MCP Client │  │ ◄────────────────── │  ┌───────────┐  │
│  └───────────┘  │    HTTP Responses   │  │   Tools   │  │
└─────────────────┘                     │  │ - Weather │  │
                                        │  │ - BMI     │  │
                                        │  │ - Quotes  │  │
                                        │  └───────────┘  │
                                        └─────────────────┘
```

## Components Breakdown

### 1. MCP Server (`mcp_server.py`)

**Technology Stack:**
- **FastAPI**: HTTP server framework
- **FastMCP**: MCP protocol implementation
- **Uvicorn**: ASGI server

**Key Functions:**

#### Server Initialization
```python
# Creates FastAPI app
app = FastAPI(title="Supervisory Agent MCP Server")

# Creates MCP server from FastAPI app
mcp = FastMCP.from_fastapi(app=app)
```

**What happens:**
1. FastAPI creates HTTP endpoints for each tool
2. FastMCP wraps the FastAPI app to make it MCP-compliant
3. OpenAPI schema is automatically generated from FastAPI endpoints

#### Tool Definition Pattern
```python
@app.get("/get_weather")
async def get_weather(location: str, units: str = "metric"):
    # Tool implementation
    return weather_data
```

**What happens:**
1. FastAPI decorator creates HTTP endpoint
2. Function parameters become tool parameters
3. FastMCP automatically exposes this as an MCP tool
4. OpenAPI schema includes parameter types and descriptions

### 2. MCP Client (`app/agents/mcp_client.py`)

**Technology Stack:**
- **requests**: HTTP client library
- **httpx**: Modern HTTP client (imported but can replace requests)

## Detailed Process Flow

### Phase 1: Initialization & Discovery

#### Step 1: Client Initialization
```python
def __init__(self):
    self.server_url = settings.MCP_SERVER_URL  # http://localhost:8001
    self.api_key = settings.MCP_API_KEY        # "your-secret-api-key"
    self.headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }
```

**What happens:**
- Client loads server URL from environment variables
- Sets up authentication headers with Bearer token
- Initializes empty tool cache

#### Step 2: Connection Testing
```python
def _initialize_connection(self):
    response = requests.get(f"{self.server_url}/health", timeout=5)
    if response.status_code == 200:
        print("✅ Successfully connected to MCP server")
        self._discover_capabilities()
```

**HTTP Request:**
```
GET http://localhost:8001/health
Authorization: Bearer your-secret-api-key
```

**Server Response:**
```json
{
  "status": "healthy",
  "server": "MCP Server"
}
```

#### Step 3: Capability Discovery
```python
def _discover_capabilities(self):
    response = requests.get(f"{self.server_url}/openapi.json", timeout=10)
    schema = response.json()
```

**HTTP Request:**
```
GET http://localhost:8001/openapi.json
Authorization: Bearer your-secret-api-key
```

**OpenAPI Schema Response (Simplified):**
```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Supervisory Agent MCP Server",
    "version": "1.0.0"
  },
  "paths": {
    "/get_weather": {
      "get": {
        "summary": "Get Weather",
        "description": "Get current weather for a location",
        "parameters": [
          {
            "name": "location",
            "in": "query",
            "required": true,
            "schema": {"type": "string"}
          },
          {
            "name": "units",
            "in": "query",
            "required": false,
            "schema": {"type": "string", "default": "metric"}
          }
        ]
      }
    },
    "/calculate_bmi": {
      "post": {
        "summary": "Calculate Bmi",
        "description": "Calculate BMI from height and weight",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "height": {"type": "number"},
                  "weight": {"type": "number"}
                },
                "required": ["height", "weight"]
              }
            }
          }
        }
      }
    }
  }
}
```

#### Step 4: Tool Parsing
```python
def _discover_capabilities(self):
    tools = []
    paths = schema.get("paths", {})
    for path, methods in paths.items():
        # Skip system endpoints
        if path in ["/openapi.json", "/docs", "/health"]:
            continue
            
        for method, details in methods.items():
            tool_name = details.get("summary") or path.strip("/")
            tools.append({
                "name": tool_name,
                "description": details.get("description", ""),
                "path": path,
                "method": method.upper(),
                "parameters": self._extract_parameters_from_schema(details)
            })
```

**Parsed Tools Result:**
```python
[
    {
        "name": "Get Weather",
        "description": "Get current weather for a location",
        "path": "/get_weather",
        "method": "GET",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "units": {"type": "string", "default": "metric"}
            },
            "required": ["location"]
        }
    },
    {
        "name": "Calculate Bmi",
        "description": "Calculate BMI from height and weight",
        "path": "/calculate_bmi",
        "method": "POST",
        "parameters": {
            "type": "object",
            "properties": {
                "height": {"type": "number"},
                "weight": {"type": "number"}
            },
            "required": ["height", "weight"]
        }
    }
]
```

### Phase 2: Parameter Schema Extraction

#### Function: `_extract_parameters_from_schema()`

**For GET Requests (Query Parameters):**
```python
def _extract_parameters_from_schema(self, endpoint_details: dict):
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
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
```

**For POST Requests (Request Body):**
```python
def _extract_parameters_from_schema(self, endpoint_details: dict):
    request_body = endpoint_details.get("requestBody", {})
    if request_body:
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        if schema:
            return schema
```

### Phase 3: Tool Execution

#### Step 1: Tool Call Request
```python
def call_mcp_tool(self, tool_name: str, parameters: dict):
    # Find the tool
    tool = next((t for t in self._available_tools if t["name"] == tool_name), None)
    if not tool:
        return {"error": f"Tool '{tool_name}' not found on server"}
    
    url = f"{self.server_url}{tool['path']}"
    method = tool['method']
```

#### Step 2: HTTP Request Construction

**For GET Request (Weather Example):**
```python
if method == 'GET':
    response = requests.get(url, params=parameters, headers=self.headers, timeout=30)
```

**Actual HTTP Request:**
```
GET http://localhost:8001/get_weather?location=London&units=metric
Authorization: Bearer your-secret-api-key
Content-Type: application/json
```

**For POST Request (BMI Example):**
```python
elif method == 'POST':
    response = requests.post(url, json=parameters, headers=self.headers, timeout=30)
```

**Actual HTTP Request:**
```
POST http://localhost:8001/calculate_bmi
Authorization: Bearer your-secret-api-key
Content-Type: application/json

{
  "height": 1.75,
  "weight": 70
}
```

#### Step 3: Response Processing
```python
response.raise_for_status()
result = response.json()

# Return in MCP-compatible format
return {"result": result}
```

**Server Response (Weather Example):**
```json
{
  "location": "London, GB",
  "temperature": "21.45°C",
  "feels_like": "21.32°C",
  "description": "Overcast Clouds",
  "humidity": "64%",
  "wind_speed": "4.28 m/s",
  "pressure": "1015 hPa",
  "visibility": "10000 m",
  "cloudiness": "90%"
}
```

**Client Return Format:**
```json
{
  "result": {
    "location": "London, GB",
    "temperature": "21.45°C",
    "feels_like": "21.32°C",
    "description": "Overcast Clouds",
    "humidity": "64%",
    "wind_speed": "4.28 m/s",
    "pressure": "1015 hPa",
    "visibility": "10000 m",
    "cloudiness": "90%"
  }
}
```

## Authentication Flow

### API Key Configuration

**Environment Variables:**
```bash
MCP_API_KEY=your-secret-api-key
MCP_SERVER_URL=http://localhost:8001
```

**Server-Side Authentication (FastAPI Dependency):**
```python
from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException

security = HTTPBearer()

async def verify_api_key(token: HTTPAuthorizationCredentials = Depends(security)):
    if token.credentials != os.getenv("MCP_API_KEY", "your-secret-api-key"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token.credentials

@app.get("/get_weather")
async def get_weather(location: str, api_key: str = Depends(verify_api_key)):
    # Tool implementation
```

**Client-Side Authentication:**
```python
headers = {
    "Authorization": f"Bearer {self.api_key}",
    "Content-Type": "application/json"
}
```

## OpenAPI Schema Generation

### How FastAPI Generates OpenAPI Schema

1. **Automatic Introspection:**
   - FastAPI inspects function signatures
   - Extracts parameter types from Python type hints
   - Generates JSON schema from Pydantic models

2. **Schema Structure:**
   ```python
   @app.get("/get_weather")
   async def get_weather(location: str, units: str = "metric"):
   ```
   
   **Becomes:**
   ```json
   {
     "parameters": [
       {
         "name": "location",
         "in": "query",
         "required": true,
         "schema": {"type": "string"}
       },
       {
         "name": "units",
         "in": "query",
         "required": false,
         "schema": {"type": "string", "default": "metric"}
       }
     ]
   }
   ```

3. **FastMCP Integration:**
   - FastMCP reads the OpenAPI schema
   - Exposes each endpoint as an MCP tool
   - Maintains parameter validation and documentation

## Error Handling

### Client-Side Error Handling
```python
try:
    response.raise_for_status()
    return {"result": response.json()}
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        return {"error": f"Tool endpoint not found: {url}"}
    elif e.response.status_code == 401:
        return {"error": "Authentication failed - check MCP API key"}
    else:
        error_details = e.response.json().get('detail', str(e))
        return {"error": f"HTTP error calling tool: {error_details}"}
```

### Server-Side Error Handling
```python
@app.get("/get_weather")
async def get_weather(location: str, units: str = "metric"):
    try:
        # API call logic
        return weather_data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather: {e}")
```

## Cache Management

### Tool Cache Lifecycle
```python
def get_available_tools(self, force_refresh=False):
    if not self._tools_cache_valid or force_refresh:
        self._discover_capabilities()
    
    return {"tools": self._available_tools or []}
```

**Cache Invalidation Scenarios:**
1. First client initialization
2. Manual refresh via `refresh_capabilities()`
3. Tool call failure (automatic retry with fresh discovery)

## Dynamic Adaptation

### Adding New Tools to Server

1. **Add new endpoint to `mcp_server.py`:**
   ```python
   @app.post("/translate_text")
   async def translate_text(text: str, target_language: str):
       # Implementation
       return {"translated_text": result}
   ```

2. **Client automatically discovers it:**
   - Next `get_available_tools()` call fetches updated OpenAPI schema
   - New tool appears in available tools list
   - Agent can immediately use the new tool

### No Code Changes Required

The beauty of this architecture is that:
- **Server changes** are automatically reflected in the OpenAPI schema
- **Client discovery** happens dynamically via schema parsing
- **Agent routing** adapts automatically to new tools

This makes the system truly scalable and maintainable!

## Performance Considerations

### Caching Strategy
- Tools are cached after first discovery
- Cache is invalidated only when needed
- Health checks are lightweight (simple HTTP GET)

### Connection Pooling
- HTTP connections are reused via requests library
- Timeout settings prevent hanging requests
- Retry logic can be added for production use

## Security Considerations

### API Key Management
- Keys stored in environment variables
- Bearer token authentication
- Server validates all requests

### Input Validation
- FastAPI provides automatic request validation
- Pydantic models ensure type safety
- SQL injection protection through parameterized queries

This architecture provides a robust, scalable, and maintainable foundation for MCP-based tool execution in your supervisory agent system.
