import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_MODEL_NAME: str
    OPENAI_API_KEY: str
    MCP_API_KEY: str
    OPENWEATHER_API_KEY: str
    MCP_SERVER_URL: str
    DASHBOARD_AGENT_URL: str
    CREDIT_ANALYSIS_URL: str
    RULE_SAVER_URL: str
    CHROMA_HOST: str
    CHROMA_PORT: int

    class Config:
        env_file = ".env"

settings = Settings()
