from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):
    APP_NAME: str = "SchemeSathi"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    DATABASE_URL: str = "sqlite:///./schemesathi.db"

    TINYFISH_API_KEY: str = ""
    TINYFISH_BASE_URL: str = "https://agent.tinyfish.ai"
    TINYFISH_SEARCH_URL: str = "https://api.search.tinyfish.ai"
    TINYFISH_FETCH_URL: str = "https://api.fetch.tinyfish.ai"
    TINYFISH_BROWSER_URL: str = "https://api.browser.tinyfish.ai"

    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"

    OCR_ENGINE: str = "tesseract"
    TESSERACT_CMD: str = ""

    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    RESEND_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""

    ENABLE_SCHEDULER: bool = False

    @property
    def cors_origin_list(self) -> List[str]:
        """Comma-separated (or JSON list) CORS origins as a clean list."""
        raw = (self.CORS_ORIGINS or "").strip()
        if raw.startswith("["):
            import json

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(v).strip() for v in parsed if str(v).strip()]
            except Exception:
                pass
        return [v.strip() for v in raw.split(",") if v.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
