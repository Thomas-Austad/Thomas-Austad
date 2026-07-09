from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_DATABASE_URL = "postgresql+psycopg://talent:talent@localhost:5432/talent"
POSTGRES_SCHEMES = ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")


class Settings(BaseSettings):
    app_env: Literal["development", "test", "production"] = "development"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.5"
    openai_timeout_seconds: float = 30
    openai_max_retries: int = 2
    connector_timeout_seconds: float = 30
    connector_max_attempts: int = 2
    database_url: str = DEFAULT_DATABASE_URL
    public_base_url: str = "http://localhost:8000"
    audit_log_path: str = "var/audit/events.jsonl"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def require_postgres_database_url(cls, value: str) -> str:
        if not value:
            raise ValueError("DATABASE_URL is required")
        if not value.startswith(POSTGRES_SCHEMES):
            raise ValueError("DATABASE_URL must use PostgreSQL, for example postgresql+psycopg://...")
        return value

    @model_validator(mode="after")
    def require_explicit_production_database_url(self) -> "Settings":
        if self.app_env == "production" and self.database_url == DEFAULT_DATABASE_URL:
            raise ValueError("Production DATABASE_URL must be set explicitly")
        return self


settings = Settings()
