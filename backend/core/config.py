import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Stock Intelligence Dashboard API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # External APIs
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    DEFAULT_GROQ_API_KEY: str = os.getenv("DEFAULT_GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    



    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        case_sensitive = True


settings = Settings()
