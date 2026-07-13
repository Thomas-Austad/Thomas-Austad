from fastapi.testclient import TestClient

from app.agents.profile_agent import CandidateProfileAgent
from app.main import app
from app.services.model_service import ModelServiceMalformedOutput, ModelServiceRequestTooLarge, ModelServiceUnavailable


LOCAL_AUTH_HEADERS = {"Authorization": "Bearer test-local-access-token-that-is-at-least-32-characters"}


def test_profile_connection_failure_returns_safe_recovery_message(monkeypatch) -> None:
    async def unavailable(*_args, **_kwargs):
        raise ModelServiceUnavailable("runtime details must not reach the API response")

    monkeypatch.setattr(CandidateProfileAgent, "__init__", lambda self: None)
    monkeypatch.setattr(CandidateProfileAgent, "run", unavailable)

    response = TestClient(app, headers=LOCAL_AUTH_HEADERS).post(
        "/profiles",
        json={"candidate_id": "synthetic", "resume_text": "Synthetic Candidate"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Model service cannot be reached. Check the configured model service and try again."
    }


def test_profile_malformed_model_output_returns_safe_recovery_message(monkeypatch) -> None:
    async def malformed(*_args, **_kwargs):
        raise ModelServiceMalformedOutput("raw candidate output must not reach the API response")

    monkeypatch.setattr(CandidateProfileAgent, "__init__", lambda self: None)
    monkeypatch.setattr(CandidateProfileAgent, "run", malformed)

    response = TestClient(app, headers=LOCAL_AUTH_HEADERS).post(
        "/profiles",
        json={"candidate_id": "synthetic", "resume_text": "Synthetic Candidate"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Model service returned an invalid response. No changes were saved; try again shortly."
    }


def test_profile_request_exceeding_local_model_limit_returns_safe_error(monkeypatch) -> None:
    async def too_large(*_args, **_kwargs):
        raise ModelServiceRequestTooLarge("resume text must not reach the API response")

    monkeypatch.setattr(CandidateProfileAgent, "__init__", lambda self: None)
    monkeypatch.setattr(CandidateProfileAgent, "run", too_large)

    response = TestClient(app, headers=LOCAL_AUTH_HEADERS).post(
        "/profiles",
        json={"candidate_id": "synthetic", "resume_text": "Synthetic Candidate"},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Model request exceeds the configured local limit."}
