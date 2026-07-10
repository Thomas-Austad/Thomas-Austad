"""Authenticated encryption for sensitive locally persisted payloads."""

from __future__ import annotations

import base64
import binascii
import json
import secrets
from typing import Any

import keyring
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from keyring.errors import KeyringError

from app.config import settings

DATA_PROTECTION_SERVICE = "talent-advisor-platform"
DATA_PROTECTION_ACCOUNT_PREFIX = "data-encryption-key-v"
ENVELOPE_VERSION = 1
NONCE_BYTES = 12
KEY_BYTES = 32


class SensitiveDataProtectionError(RuntimeError):
    """Base class for data-protection failures safe to report to callers."""


class SensitiveDataKeyUnavailable(SensitiveDataProtectionError):
    """Raised when a required OS-keystore key cannot be safely obtained."""


class SensitiveDataIntegrityError(SensitiveDataProtectionError):
    """Raised when an encrypted payload is malformed or fails authentication."""


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value.encode("ascii"))
    except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
        raise SensitiveDataIntegrityError("Encrypted data is malformed") from exc


class SensitiveDataProtector:
    """Encrypt JSON values with a versioned AES-GCM key from the OS key store."""

    def _account(self, key_version: int) -> str:
        return f"{DATA_PROTECTION_ACCOUNT_PREFIX}{key_version}"

    def _key(self, key_version: int, *, create: bool) -> bytes:
        if key_version < 1:
            raise SensitiveDataKeyUnavailable("Encryption key version is invalid")
        if settings.app_env == "test":
            return bytes([key_version]) * KEY_BYTES

        try:
            stored_key = keyring.get_password(DATA_PROTECTION_SERVICE, self._account(key_version))
            if stored_key is None:
                if not create:
                    raise SensitiveDataKeyUnavailable("Required encryption key is unavailable")
                key = secrets.token_bytes(KEY_BYTES)
                keyring.set_password(
                    DATA_PROTECTION_SERVICE,
                    self._account(key_version),
                    _encode(key),
                )
                return key
        except KeyringError as exc:
            raise SensitiveDataKeyUnavailable("Local encryption key storage is unavailable") from exc

        key = _decode(stored_key)
        if len(key) != KEY_BYTES:
            raise SensitiveDataKeyUnavailable("Stored encryption key is invalid")
        return key

    @staticmethod
    def _aad(purpose: str, record_id: str) -> bytes:
        return f"talent-advisor:v{ENVELOPE_VERSION}:{purpose}:{record_id}".encode("utf-8")

    def encrypt_json(self, value: Any, *, purpose: str, record_id: str) -> dict[str, Any]:
        key_version = settings.data_encryption_key_version
        nonce = secrets.token_bytes(NONCE_BYTES)
        plaintext = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        ciphertext = AESGCM(self._key(key_version, create=True)).encrypt(
            nonce,
            plaintext,
            self._aad(purpose, record_id),
        )
        return {
            "version": ENVELOPE_VERSION,
            "key_version": key_version,
            "nonce": _encode(nonce),
            "ciphertext": _encode(ciphertext),
        }

    def decrypt_json(self, envelope: Any, *, purpose: str, record_id: str) -> Any:
        if not isinstance(envelope, dict) or set(envelope) != {
            "version",
            "key_version",
            "nonce",
            "ciphertext",
        }:
            raise SensitiveDataIntegrityError("Encrypted data is malformed")
        if envelope["version"] != ENVELOPE_VERSION or not isinstance(envelope["key_version"], int):
            raise SensitiveDataIntegrityError("Encrypted data version is unsupported")
        if not isinstance(envelope["nonce"], str) or not isinstance(envelope["ciphertext"], str):
            raise SensitiveDataIntegrityError("Encrypted data is malformed")
        nonce = _decode(envelope["nonce"])
        if len(nonce) != NONCE_BYTES:
            raise SensitiveDataIntegrityError("Encrypted data nonce is invalid")
        try:
            plaintext = AESGCM(self._key(envelope["key_version"], create=False)).decrypt(
                nonce,
                _decode(envelope["ciphertext"]),
                self._aad(purpose, record_id),
            )
            return json.loads(plaintext.decode("utf-8"))
        except (InvalidTag, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SensitiveDataIntegrityError("Encrypted data failed integrity validation") from exc


protector = SensitiveDataProtector()
