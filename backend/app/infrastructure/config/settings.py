"""Application configuration via environment variables."""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Store Copilot"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    database_url: str = "sqlite+aiosqlite:///./dev.db"
    database_sync_url: str = "sqlite:///./dev.db"

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

    class Config:
        _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", ".env")
        env_file = _env_path if os.path.isfile(_env_path) else ".env"
        env_file_encoding = "utf-8"


settings = Settings()
