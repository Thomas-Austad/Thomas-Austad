from app.config import settings
from app.local_launcher import create_browser_workspace_url, request_browser_workspace_url


def test_launcher_creates_a_fragment_bootstrap_url_without_a_bearer_token() -> None:
    url = create_browser_workspace_url()

    assert "/app#bootstrap=" in url
    assert "LOCAL_ACCESS_TOKEN" not in url


def test_repeat_launcher_requests_a_fresh_browser_url_from_the_authenticated_api(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"browser_url": f"{settings.public_base_url}/app#bootstrap=fresh-token"}

    class Client:
        headers: dict[str, str] | None = None

        def post(self, _url: str, *, headers: dict[str, str]) -> Response:
            self.headers = headers
            return Response()

    monkeypatch.setattr(
        "app.local_launcher.local_auth_service.get_local_access_token",
        lambda: "local-test-token",
    )
    client = Client()

    url = request_browser_workspace_url(client)  # type: ignore[arg-type]

    assert url == f"{settings.public_base_url}/app#bootstrap=fresh-token"
    assert client.headers == {"Authorization": "Bearer local-test-token"}
    assert "local-test-token" not in url
