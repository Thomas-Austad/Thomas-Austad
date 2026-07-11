from app.local_launcher import create_browser_workspace_url


def test_launcher_creates_a_fragment_bootstrap_url_without_a_bearer_token() -> None:
    url = create_browser_workspace_url()

    assert "/app#bootstrap=" in url
    assert "LOCAL_ACCESS_TOKEN" not in url
