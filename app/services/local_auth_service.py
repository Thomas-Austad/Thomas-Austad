from __future__ import annotations

import secrets
from functools import lru_cache

import keyring
from keyring.errors import KeyringError

from app.config import settings

LOCAL_AUTH_SERVICE = "talent-advisor-platform"
LOCAL_AUTH_ACCOUNT = "local-api-token"
LOCAL_ACTOR_ID = "local_user"


class LocalCredentialUnavailable(RuntimeError):
    """Raised when a local credential cannot be safely retrieved or created."""


@lru_cache(maxsize=1)
def get_local_access_token() -> str:
    """Return the local API credential without exposing it to logs or callers."""
    if settings.local_access_token:
        return settings.local_access_token

    try:
        stored_token = keyring.get_password(LOCAL_AUTH_SERVICE, LOCAL_AUTH_ACCOUNT)
        if stored_token:
            return stored_token

        generated_token = secrets.token_urlsafe(32)
        keyring.set_password(LOCAL_AUTH_SERVICE, LOCAL_AUTH_ACCOUNT, generated_token)
        return generated_token
    except KeyringError as exc:
        raise LocalCredentialUnavailable("Local credential storage is unavailable") from exc
