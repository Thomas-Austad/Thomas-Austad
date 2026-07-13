from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_DATABASE_URL = "postgresql+psycopg://talent:talent@localhost:5432/talent"
POSTGRES_SCHEMES = ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")


class Settings(BaseSettings):
    app_env: Literal["development", "test", "production"] = "development"
    model_provider: Literal["openai", "ollama"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6"
    openai_timeout_seconds: float = 30
    openai_max_retries: int = 2
    local_model_base_url: str = "http://127.0.0.1:11434"
    local_model_name: str = ""
    model_connect_timeout_seconds: float = Field(default=5, gt=0, le=60)
    model_read_timeout_seconds: float = Field(default=60, gt=0, le=300)
    model_max_retries: int = Field(default=1, ge=0, le=3)
    model_max_request_bytes: int = Field(default=16_384, gt=0, le=1_000_000)
    model_max_output_tokens: int = Field(default=4_096, ge=1, le=32_768)
    model_max_response_bytes: int = Field(default=2_000_000, gt=0, le=10_000_000)
    model_context_limit: int = Field(default=8_192, ge=512, le=131_072)
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
        parsed = urlsplit(value)
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("PUBLIC_BASE_URL must use an HTTP loopback address")
        return value

    @field_validator("local_model_base_url")
    @classmethod
    def require_loopback_local_model_base_url(cls, value: str) -> str:
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("LOCAL_MODEL_BASE_URL must use a valid loopback port") from exc
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or (port is not None and not 1 <= port <= 65_535)
        ):
            raise ValueError("LOCAL_MODEL_BASE_URL must use an HTTP(S) loopback address without a path")
        return value.rstrip("/")

    @model_validator(mode="after")
    def require_explicit_production_database_url(self) -> "Settings":
        if self.app_env == "production" and self.database_url == DEFAULT_DATABASE_URL:
            raise ValueError("Production DATABASE_URL must be set explicitly")
        if self.model_provider == "ollama" and not self.local_model_name.strip():
            raise ValueError("LOCAL_MODEL_NAME is required when MODEL_PROVIDER=ollama")
        if self.model_max_output_tokens >= self.model_context_limit:
            raise ValueError("MODEL_MAX_OUTPUT_TOKENS must be lower than MODEL_CONTEXT_LIMIT")
        max_context_request_bytes = (self.model_context_limit - self.model_max_output_tokens) * 4
        if self.model_max_request_bytes > max_context_request_bytes:
            raise ValueError("MODEL_MAX_REQUEST_BYTES exceeds the configured model context budget")
        return self


settings = Settings()
