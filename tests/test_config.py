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
