"""Start the loopback application and open one short-lived browser workspace."""

from __future__ import annotations

import threading
import time
import webbrowser

import httpx
import uvicorn

from app.config import settings
from app.main import app, browser_sessions


def create_browser_workspace_url() -> str:
    """Create an unlogged, launcher-only URL without reading the bearer credential."""
    return f"{settings.public_base_url.rstrip('/')}/app#bootstrap={browser_sessions.create_bootstrap()}"


def run() -> None:
    parsed = httpx.URL(settings.public_base_url)
    host = parsed.host or "127.0.0.1"
    port = parsed.port or 8000
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    health_url = f"{settings.public_base_url.rstrip('/')}/health"
    with httpx.Client(timeout=1) as client:
        for _ in range(30):
            try:
                if client.get(health_url).status_code == 200:
                    webbrowser.open(create_browser_workspace_url())
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
        else:
            server.should_exit = True
            raise RuntimeError("Talent Advisor did not start on its local address")
    thread.join()


if __name__ == "__main__":
    run()
