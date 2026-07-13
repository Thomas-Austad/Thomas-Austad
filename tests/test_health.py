from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import LocalModelReadiness


LOCAL_AUTH_HEADERS = {"Authorization": "Bearer test-local-access-token-that-is-at-least-32-characters"}


def test_health():
    assert TestClient(app).get("/health").json() == {"ok": True}


def test_local_model_readiness_requires_authentication_and_hides_runtime_details(monkeypatch) -> None:
    async def unavailable() -> LocalModelReadiness:
        return LocalModelReadiness(ready=False, status="runtime_unavailable")

    monkeypatch.setattr("app.main.check_local_model_readiness", unavailable)
    client = TestClient(app)

    assert client.get("/local-model/readiness").status_code == 401
    response = client.get("/local-model/readiness", headers=LOCAL_AUTH_HEADERS)

    assert response.status_code == 503
    assert response.json() == {"ready": False, "status": "runtime_unavailable"}
