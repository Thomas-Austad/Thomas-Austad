from datetime import UTC, datetime, timedelta

from app.services.browser_session_service import BrowserSessionStore


def test_bootstrap_is_single_use_and_creates_an_opaque_session() -> None:
    store = BrowserSessionStore()
    bootstrap = store.create_bootstrap()

    session = store.redeem_bootstrap(bootstrap)

    assert session is not None
    assert session.session_id != session.csrf_token
    assert store.redeem_bootstrap(bootstrap) is None
    assert store.validate_csrf(session, session.csrf_token)
    assert not store.validate_csrf(session, "wrong-token")


def test_expired_session_is_rejected() -> None:
    store = BrowserSessionStore()
    session = store.redeem_bootstrap(store.create_bootstrap())
    assert session is not None
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    assert store.get_session(session.session_id) is None
