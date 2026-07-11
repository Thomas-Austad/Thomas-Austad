from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_DATABASE_URL = "postgresql+psycopg://talent:talent@localhost:5432/talent"
POSTGRES_SCHEMES = ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")


class Settings(BaseSettings):
    app_env: Literal["development", "test", "production"] = "development"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6"
    openai_timeout_seconds: float = 30
    openai_max_retries: int = 2
    connector_timeout_seconds: float = 30
    connector_max_attempts: int = 2
    connector_max_response_bytes: int = Field(default=2_000_000, gt=0)
    api_rate_limit_enabled: bool = True
    api_rate_limit_window_seconds: int = Field(default=60, gt=0)
    api_default_rate_limit: int = Field(default=120, gt=0)
    api_model_rate_limit: int = Field(default=30, gt=0)
    api_upload_rate_limit: int = Field(default=10, gt=0)
    api_job_search_rate_limit: int = Field(default=30, gt=0)
    api_document_rate_limit: int = Field(default=30, gt=0)
    api_write_rate_limit: int = Field(default=60, gt=0)
    database_url: str = DEFAULT_DATABASE_URL
    public_base_url: str = "http://127.0.0.1:8000"
    audit_log_path: str = "var/audit/events.jsonl"
    local_access_token: str = Field(default="", repr=False)
    browser_bootstrap_ttl_seconds: int = Field(default=60, ge=10, le=300)
    browser_session_ttl_seconds: int = Field(default=3_600, ge=300, le=86_400)
    data_encryption_key_version: int = Field(default=1, ge=1)
    require_encrypted_storage: bool = False
    profile_retention_days: int = Field(default=730, ge=1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def require_postgres_database_url(cls, value: str) -> str:
        if not value:
            raise ValueError("DATABASE_URL is required")
        if not value.startswith(POSTGRES_SCHEMES):
            raise ValueError("DATABASE_URL must use PostgreSQL, for example postgresql+psycopg://...")
        return value

    @field_validator("local_access_token")
    @classmethod
    def validate_local_access_token(cls, value: str) -> str:
        if value and len(value) < 32:
            raise ValueError("LOCAL_ACCESS_TOKEN must be at least 32 characters when configured")
        return value

    @field_validator("public_base_url")
    @classmethod
    def require_loopback_public_base_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("PUBLIC_BASE_URL must use an HTTP loopback address")
        return value

    @model_validator(mode="after")
    def require_explicit_production_database_url(self) -> "Settings":
        if self.app_env == "production" and self.database_url == DEFAULT_DATABASE_URL:
            raise ValueError("Production DATABASE_URL must be set explicitly")
        return self


settings = Settings()
