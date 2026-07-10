import pytest
from keyring.errors import KeyringError

from app.config import settings
from app.services import local_auth_service


def test_configured_local_access_token_is_used(monkeypatch) -> None:
    token = "configured-local-access-token-that-is-at-least-32-characters"
    monkeypatch.setattr(settings, "local_access_token", token)
    local_auth_service.get_local_access_token.cache_clear()

    assert local_auth_service.get_local_access_token() == token


def test_keyring_failure_is_reported_without_insecure_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "local_access_token", "")

    def fail_to_read(*args, **kwargs) -> str:
        raise KeyringError("keyring unavailable")

    monkeypatch.setattr(local_auth_service.keyring, "get_password", fail_to_read)
    local_auth_service.get_local_access_token.cache_clear()

    with pytest.raises(local_auth_service.LocalCredentialUnavailable):
        local_auth_service.get_local_access_token()
