import requests
import json
from app.core.config import settings

class ExternalServicesClient:
    """Client for handling calls to various external (non-MCP) services."""

    def __init__(self):
        self.dashboard_agent_url = settings.DASHBOARD_AGENT_URL
        self.credit_analysis_url = settings.CREDIT_ANALYSIS_URL
        self.rule_saver_url = settings.RULE_SAVER_URL

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
            payload = {"input": {"metadata": json.dumps(rule_data)}}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.rule_saver_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to call Rule Saver API: {e}"}
