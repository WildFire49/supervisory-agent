import requests
import json
from app.core.config import settings

class MCPClient:
    def __init__(self):
        self.mcp_base_url = settings.MCP_SERVER_URL
        self.dashboard_agent_url = settings.DASHBOARD_AGENT_URL
        self.credit_analysis_url = settings.CREDIT_ANALYSIS_URL
        self.rule_saver_url = settings.RULE_SAVER_URL

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
