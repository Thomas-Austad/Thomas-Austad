"""Short-lived, local browser sessions without exposing the API bearer token."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(slots=True)
class BrowserSession:
    session_id: str
    csrf_token: str
    expires_at: datetime


class BrowserSessionStore:
    """Bounded in-memory bootstrap and session state for the local UI."""

    def __init__(self, *, bootstrap_ttl_seconds: int = 60, session_ttl_seconds: int = 3_600) -> None:
        self.bootstrap_ttl = timedelta(seconds=bootstrap_ttl_seconds)
        self.session_ttl = timedelta(seconds=session_ttl_seconds)
        self._bootstraps: dict[str, datetime] = {}
        self._sessions: dict[str, BrowserSession] = {}

    def create_bootstrap(self) -> str:
        self._purge_expired()
        token = secrets.token_urlsafe(32)
        self._bootstraps[token] = datetime.now(UTC) + self.bootstrap_ttl
        return token

    def redeem_bootstrap(self, token: str) -> BrowserSession | None:
        self._purge_expired()
        expires_at = self._bootstraps.pop(token, None)
        if expires_at is None or expires_at <= datetime.now(UTC):
            return None
        return self._new_session()

    def get_session(self, session_id: str) -> BrowserSession | None:
        self._purge_expired()
        session = self._sessions.get(session_id)
        if session is None:
            return None
        session.expires_at = datetime.now(UTC) + self.session_ttl
        return session

    def validate_csrf(self, session: BrowserSession, token: str) -> bool:
        return secrets.compare_digest(session.csrf_token, token)

    def revoke(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def _new_session(self) -> BrowserSession:
        session = BrowserSession(
            session_id=secrets.token_urlsafe(32),
            csrf_token=secrets.token_urlsafe(32),
            expires_at=datetime.now(UTC) + self.session_ttl,
        )
        self._sessions[session.session_id] = session
        return session

    def _purge_expired(self) -> None:
        now = datetime.now(UTC)
        self._bootstraps = {
            token: expires_at for token, expires_at in self._bootstraps.items() if expires_at > now
        }
        self._sessions = {
            session_id: session
            for session_id, session in self._sessions.items()
            if session.expires_at > now
        }
