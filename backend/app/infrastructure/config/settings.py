"""Application configuration via environment variables."""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Store Copilot"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_store_copilot"
    database_sync_url: str = "postgresql://postgres:postgres@localhost:5433/ai_store_copilot"

    # PostgreSQL connection details (for CLI / dev scripts)
    pg_host: str = "localhost"
    pg_port: int = 5433
    pg_user: str = "postgres"
    pg_password: str = "postgres"
    pg_database: str = "ai_store_copilot"

    redis_url: str = ""

    ai_provider: str = "deepseek"
    ai_api_key: str = ""
    ai_base_url: str = "https://api.deepseek.com"
    ai_model: str = "deepseek-chat"
    ai_embed_model: str = "deepseek-embedding"

    wecom_corp_id: str = ""
    wecom_agent_id: str = ""
    wecom_secret: str = ""
    wecom_token: str = ""
    wecom_encoding_aes_key: str = ""
    wecom_webhook_url: str = ""

    jwt_secret_key: str = "change-me-in-production"
    jwt_access_token_expire_minutes: int = 120
    jwt_refresh_token_expire_days: int = 7

    log_level: str = "INFO"

    # ── CORS ────────────────────────────────────────────────
    cors_origins: str = ""  # comma-separated; empty = allow all in dev
    otel_service_name: str = "ai-store-copilot"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        origins = self.cors_origins.strip()
        if not origins:
            return ["*"]
        return [o.strip() for o in origins.split(",") if o.strip()]

    class Config:
        _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", ".env")
        env_file = _env_path if os.path.isfile(_env_path) else ".env"
        env_file_encoding = "utf-8"


settings = Settings()
