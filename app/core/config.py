import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_MODEL_NAME: str
    OPENAI_API_KEY: str
    MCP_API_KEY: str
    OPENWEATHER_API_KEY: str
    MCP_SERVER_URL: str = "http://localhost:8001"
    DASHBOARD_AGENT_URL: str = "http://13.201.208.156:8000/dashboard-agent"
    CREDIT_ANALYSIS_URL: str = "http://13.201.208.156:8200/analyze_credit"
    RULE_SAVER_URL: str = "http://13.201.208.156:8200/rule_saver"

    class Config:
        env_file = ".env"

settings = Settings()
