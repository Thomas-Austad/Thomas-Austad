from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from app.config import settings
from app.main import BROWSER_SESSION_COOKIE, app


LOCAL_AUTH_HEADERS = {
    "Authorization": "Bearer test-local-access-token-that-is-at-least-32-characters"
}


def _launch_browser_session(client: TestClient) -> tuple[str, str]:
    launch = client.post("/browser-session/launch")
    assert launch.status_code == 200
    fragment = parse_qs(urlsplit(launch.json()["browser_url"]).fragment)
    bootstrap = client.post("/browser-session/bootstrap", json={"bootstrap_token": fragment["bootstrap"][0]})
    assert bootstrap.status_code == 200
    cookie = bootstrap.cookies.get(BROWSER_SESSION_COOKIE)
    assert cookie
    return cookie, bootstrap.json()["csrf_token"]


def test_browser_bootstrap_is_single_use_and_never_returns_bearer_token() -> None:
    client = TestClient(app, headers=LOCAL_AUTH_HEADERS)
    launch = client.post("/browser-session/launch")
    token = parse_qs(urlsplit(launch.json()["browser_url"]).fragment)["bootstrap"][0]

    first = client.post("/browser-session/bootstrap", json={"bootstrap_token": token})
    replay = client.post("/browser-session/bootstrap", json={"bootstrap_token": token})

    assert first.status_code == 200
    assert set(first.json()) == {"csrf_token"}
    assert "HttpOnly" in first.headers["set-cookie"]
    assert "SameSite=strict" in first.headers["set-cookie"]
    assert "Secure" in first.headers["set-cookie"]
    assert replay.status_code == 401


def test_browser_session_requires_csrf_origin_and_fetch_metadata_for_writes() -> None:
    launcher_client = TestClient(app, headers=LOCAL_AUTH_HEADERS)
    cookie, csrf_token = _launch_browser_session(launcher_client)
    client = TestClient(app)
    browser_headers = {"Origin": settings.public_base_url, "Sec-Fetch-Site": "same-origin"}

    missing_csrf = client.post("/privacy/retention/purge", cookies={BROWSER_SESSION_COOKIE: cookie}, json={"confirmed_by_user": True}, headers=browser_headers)
    wrong_origin = client.post(
        "/privacy/retention/purge",
        cookies={BROWSER_SESSION_COOKIE: cookie},
        json={"confirmed_by_user": True},
        headers={**browser_headers, "Origin": "https://attacker.invalid", "X-CSRF-Token": csrf_token},
    )
    accepted = client.post(
        "/privacy/retention/purge",
        cookies={BROWSER_SESSION_COOKIE: cookie},
        json={"confirmed_by_user": True},
        headers={**browser_headers, "X-CSRF-Token": csrf_token},
    )

    assert missing_csrf.status_code == 403
    assert wrong_origin.status_code == 403
    assert accepted.status_code == 200


def test_browser_session_cannot_be_combined_with_bearer_authentication() -> None:
    launcher_client = TestClient(app, headers=LOCAL_AUTH_HEADERS)
    cookie, _ = _launch_browser_session(launcher_client)
    client = TestClient(app, headers=LOCAL_AUTH_HEADERS)

    response = client.get("/privacy/retention", cookies={BROWSER_SESSION_COOKIE: cookie})

    assert response.status_code == 400
