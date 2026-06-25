import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Stock Intelligence Dashboard API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Admin Emails
    ADMIN_EMAILS: str = os.getenv("ADMIN_EMAILS", os.getenv("VITE_ADMIN_EMAILS", ""))
    GOOGLE_AUTH_ENABLED: bool = os.getenv("GOOGLE_AUTH_ENABLED", "true").lower() in ("true", "1")

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() not in {"prod", "production"}

    @property
    def admin_emails_list(self) -> list[str]:
        if not self.ADMIN_EMAILS:
            return []
        return [email.strip().lower() for email in self.ADMIN_EMAILS.split(",") if email.strip()]

    # External APIs
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    DEFAULT_GROQ_API_KEY: str = os.getenv(
        "DEFAULT_GROQ_API_KEY", os.getenv("GROQ_API_KEY", "")
    )
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    class Config:
        case_sensitive = True


settings = Settings()
