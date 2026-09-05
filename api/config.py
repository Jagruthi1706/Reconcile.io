import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, field_validator


class Settings(BaseModel):

    app_env: str = "development"
    api_port: int = 8000
    web_port: int = 3000
    jwt_secret: SecretStr = SecretStr("change-me-in-dev-too")
    database_url: str = "postgresql+asyncpg://afc:afc@localhost:5432/afc"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"
    razorpay_key_id: str = ""
    razorpay_key_secret: SecretStr = SecretStr("")
    razorpay_webhook_secret: SecretStr = SecretStr("")
    razorpay_mode: str = Field(default="test")
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-sonnet-4-6"
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-2.0-flash"
    match_auto_accept_confidence: float = 0.90
    match_amount_tolerance_pct: float = 1.5
    match_date_window_days: int = 5

    @field_validator("database_url")
    @classmethod
    def require_async_postgres_driver(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme in {"postgres", "postgresql"}:
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            query.pop("channel_binding", None)
            if query.get("sslmode") == "require":
                query["ssl"] = query.pop("sslmode")
            return urlunsplit(("postgresql+asyncpg", parsed.netloc, parsed.path, urlencode(query), parsed.fragment))
        if parsed.scheme != "postgresql+asyncpg":
            raise ValueError("DATABASE_URL must use PostgreSQL with the asyncpg driver")
        return value

    @field_validator("razorpay_mode")
    @classmethod
    def require_test_mode(cls, value: str) -> str:
        if value != "test":
            raise ValueError('RAZORPAY_MODE must be "test"')
        return value


@lru_cache
def get_settings() -> Settings:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    values = {
        field_name: os.getenv(env_name, default)
        for field_name, env_name, default in (
            ("app_env", "APP_ENV", "development"),
            ("api_port", "API_PORT", 8000),
            ("web_port", "WEB_PORT", 3000),
            ("jwt_secret", "JWT_SECRET", "change-me-in-dev-too"),
            ("database_url", "DATABASE_URL", "postgresql+asyncpg://afc:afc@localhost:5432/afc"),
            ("redis_url", "REDIS_URL", "redis://localhost:6379/0"),
            ("cors_origins", "CORS_ORIGINS", "http://localhost:3000"),
            ("razorpay_key_id", "RAZORPAY_KEY_ID", ""),
            ("razorpay_key_secret", "RAZORPAY_KEY_SECRET", ""),
            ("razorpay_webhook_secret", "RAZORPAY_WEBHOOK_SECRET", ""),
            ("razorpay_mode", "RAZORPAY_MODE", "test"),
            ("anthropic_api_key", "ANTHROPIC_API_KEY", ""),
            ("anthropic_model", "ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            ("gemini_api_key", "GEMINI_API_KEY", ""),
            ("gemini_model", "GEMINI_MODEL", "gemini-2.0-flash"),
            ("match_auto_accept_confidence", "MATCH_AUTO_ACCEPT_CONFIDENCE", 0.90),
            ("match_amount_tolerance_pct", "MATCH_AMOUNT_TOLERANCE_PCT", 1.5),
            ("match_date_window_days", "MATCH_DATE_WINDOW_DAYS", 5),
        )
    }
    return Settings(**values)
