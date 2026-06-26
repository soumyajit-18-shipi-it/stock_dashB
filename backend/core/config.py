import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Stock Intelligence Dashboard API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv(
        "APP_ENV", os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))
    )

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

    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "")
    AI_REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "45"))
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_GROQ_API_KEY: str = os.getenv("DEFAULT_GROQ_API_KEY", GROQ_API_KEY)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")
    CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "")

    @property
    def cors_origins_list(self) -> list[str]:
        defaults = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        origins = []
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL)
        if self.CORS_ORIGINS_RAW:
            raw = self.CORS_ORIGINS_RAW.strip()
            if raw.startswith("["):
                import json

                try:
                    origins.extend(str(item).strip() for item in json.loads(raw))
                except Exception:
                    origins.extend(item.strip() for item in raw.split(","))
            else:
                origins.extend(item.strip() for item in raw.split(","))
        origins.extend(defaults)
        return list(dict.fromkeys(origin for origin in origins if origin))

    class Config:
        case_sensitive = True


settings = Settings()
