from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import DEFAULT_DATABASE_URL, Settings


def test_default_database_url_uses_postgres() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_default_model_matches_the_example_configuration() -> None:
    settings = Settings(_env_file=None)
    example_config = Path(__file__).parents[1] / ".env.example"
    example_model = next(
        line.partition("=")[2]
        for line in example_config.read_text(encoding="utf-8").splitlines()
        if line.startswith("OPENAI_MODEL=")
    )

    assert settings.openai_model == "gpt-5.6"
    assert settings.openai_model == example_model


def test_openai_model_can_be_explicitly_configured() -> None:
    settings = Settings(openai_model="configured-model", _env_file=None)

    assert settings.openai_model == "configured-model"


def test_ollama_requires_an_explicit_local_model_name() -> None:
    with pytest.raises(ValidationError, match="LOCAL_MODEL_NAME"):
        Settings(model_provider="ollama", _env_file=None)


def test_ollama_accepts_validated_loopback_configuration() -> None:
    settings = Settings(
        model_provider="ollama",
        local_model_name="synthetic-model",
        local_model_base_url="https://[::1]:11434",
        _env_file=None,
    )

    assert settings.local_model_base_url == "https://[::1]:11434"


@pytest.mark.parametrize(
    "base_url",
    [
        "http://192.168.1.10:11434",
        "http://localhost.evil.example:11434",
        "http://user:password@127.0.0.1:11434",
        "http://127.0.0.1:11434/api",
        "ftp://127.0.0.1:11434",
        "http://[::ffff:127.0.0.1]:11434",
    ],
)
def test_local_model_base_url_must_be_a_fixed_loopback_endpoint(base_url: str) -> None:
    with pytest.raises(ValidationError, match="LOCAL_MODEL_BASE_URL"):
        Settings(local_model_base_url=base_url, _env_file=None)


def test_model_output_limit_cannot_exceed_context_limit() -> None:
    with pytest.raises(ValidationError, match="MODEL_MAX_OUTPUT_TOKENS"):
        Settings(model_max_output_tokens=8_193, model_context_limit=8_192, _env_file=None)


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


@pytest.mark.parametrize(
    "public_base_url",
    ["https://example.com", "http://0.0.0.0:8000", "http://192.168.1.10:8000"],
)
def test_public_base_url_must_use_loopback(public_base_url: str) -> None:
    with pytest.raises(ValidationError, match="loopback"):
        Settings(public_base_url=public_base_url, _env_file=None)


def test_configured_local_access_token_must_be_long_enough() -> None:
    with pytest.raises(ValidationError, match="LOCAL_ACCESS_TOKEN"):
        Settings(local_access_token="too-short", _env_file=None)
