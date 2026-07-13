import httpx

from openai import APIConnectionError
from fastapi.testclient import TestClient

from app.agents.profile_agent import CandidateProfileAgent
from app.main import app


LOCAL_AUTH_HEADERS = {"Authorization": "Bearer test-local-access-token-that-is-at-least-32-characters"}


def test_profile_connection_failure_returns_safe_recovery_message(monkeypatch) -> None:
    async def unavailable(*_args, **_kwargs):
        raise APIConnectionError(message="connection failed", request=httpx.Request("POST", "https://api.openai.com/v1/responses"))

    monkeypatch.setattr(CandidateProfileAgent, "run", unavailable)

    response = TestClient(app, headers=LOCAL_AUTH_HEADERS).post(
        "/profiles",
        json={"candidate_id": "synthetic", "resume_text": "Synthetic Candidate"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Profile service cannot be reached. Check your internet connection and try again."}
