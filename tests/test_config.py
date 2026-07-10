import pytest
from pydantic import ValidationError

from app.config import DEFAULT_DATABASE_URL, Settings


def test_default_database_url_uses_postgres() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.database_url.startswith("postgresql+psycopg://")


@pytest.mark.parametrize(
    "database_url",
    [
        "",
        "sqlite:///./talent_advisor.db",
        "mysql://talent:talent@localhost/talent",
    ],
)
def test_database_url_must_be_postgres(database_url: str) -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(database_url=database_url, _env_file=None)


def test_production_requires_explicit_database_url() -> None:
    with pytest.raises(ValidationError, match="Production DATABASE_URL"):
        Settings(app_env="production", _env_file=None)


def test_production_accepts_explicit_postgres_database_url() -> None:
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://app:secret@db.example.com:5432/talent",
        _env_file=None,
    )

    assert settings.database_url == "postgresql+psycopg://app:secret@db.example.com:5432/talent"


def test_api_rate_limit_defaults_are_enabled_and_bounded() -> None:
    settings = Settings(_env_file=None)

    assert settings.api_rate_limit_enabled is True
    assert settings.api_rate_limit_window_seconds == 60
    assert settings.api_model_rate_limit > 0
    assert settings.api_upload_rate_limit > 0
    assert settings.api_write_rate_limit > 0


def test_api_rate_limits_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="greater than 0"):
        Settings(api_model_rate_limit=0, _env_file=None)
