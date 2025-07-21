import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_MODEL_NAME: str
    OPENAI_API_KEY: str
    MCP_SERVER_URL: str = "http://13.201.208.156:8200/mcp"

    class Config:
        env_file = ".env"

settings = Settings()
