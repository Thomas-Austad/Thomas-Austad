"""Start the loopback application and open one short-lived browser workspace."""

from __future__ import annotations

import threading
import time
import webbrowser

import httpx
import uvicorn

from app.config import settings
from app.main import app, browser_sessions
from app.services import local_auth_service


def create_browser_workspace_url() -> str:
    """Create an unlogged, launcher-only URL without reading the bearer credential."""
    return f"{settings.public_base_url.rstrip('/')}/app#bootstrap={browser_sessions.create_bootstrap()}"


def request_browser_workspace_url(client: httpx.Client) -> str:
    """Get a fresh bootstrap from the active local API without exposing its credential."""
    try:
        token = local_auth_service.get_local_access_token()
    except local_auth_service.LocalCredentialUnavailable as exc:
        raise RuntimeError("Talent Advisor could not access its local sign-in credential") from exc

    try:
        response = client.post(
            f"{settings.public_base_url.rstrip('/')}/browser-session/launch",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError("Talent Advisor could not create a private browser workspace") from exc

    browser_url = response.json().get("browser_url")
    expected_prefix = f"{settings.public_base_url.rstrip('/')}/app#bootstrap="
    if not isinstance(browser_url, str) or not browser_url.startswith(expected_prefix):
        raise RuntimeError("Talent Advisor received an invalid private browser workspace address")
    return browser_url


def run() -> None:
    parsed = httpx.URL(settings.public_base_url)
    host = parsed.host or "127.0.0.1"
    port = parsed.port or 8000
    health_url = f"{settings.public_base_url.rstrip('/')}/health"
    server: uvicorn.Server | None = None
    thread: threading.Thread | None = None

    with httpx.Client(timeout=1) as client:
        try:
            health_response = client.get(health_url)
        except httpx.HTTPError:
            health_response = None

        if health_response is None or health_response.status_code != 200:
            server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()
            for _ in range(30):
                try:
                    if client.get(health_url).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.5)
            else:
                server.should_exit = True
                raise RuntimeError("Talent Advisor did not start on its local address")

        try:
            webbrowser.open(request_browser_workspace_url(client))
        except Exception:
            if server is not None:
                server.should_exit = True
            raise

    if thread is not None:
        thread.join()


if __name__ == "__main__":
    run()
