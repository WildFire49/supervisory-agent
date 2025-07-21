import requests
import json
from app.core.config import settings

class MCPClient:
    def __init__(self):
        self.base_url = settings.MCP_SERVER_URL

    def call_tool(self, tool_call_json: str):
        """
        Executes a tool call against the MCP server.
        Expects a JSON string like the one in your example.
        """
        try:
            payload = json.loads(tool_call_json)
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for tool call."}
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to call MCP server: {e}"}
