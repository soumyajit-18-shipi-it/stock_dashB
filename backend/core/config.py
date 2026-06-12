import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

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
    
    # CORS
    CORS_ORIGINS: list = ["*"]

    class Config:
        case_sensitive = True

settings = Settings()
