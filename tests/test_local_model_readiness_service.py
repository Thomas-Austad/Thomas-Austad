import httpx

from app.services.local_model_readiness_service import check_local_model_readiness


def _transport(payload: object, status_code: int = 200) -> httpx.MockTransport:
    return httpx.MockTransport(lambda _request: httpx.Response(status_code, json=payload))


async def test_readiness_accepts_only_the_configured_local_model(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.model_provider", "ollama")
    monkeypatch.setattr("app.config.settings.local_model_name", "qwen3:8b")

    readiness = await check_local_model_readiness(
        transport=_transport({"models": [{"name": "qwen3:8b"}]})
    )

    assert readiness.ready is True
    assert readiness.status == "ready"


async def test_readiness_fails_closed_for_missing_or_malformed_runtime_data(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.model_provider", "ollama")
    monkeypatch.setattr("app.config.settings.local_model_name", "qwen3:8b")

    missing = await check_local_model_readiness(transport=_transport({"models": [{"name": "other:latest"}]}))
    malformed = await check_local_model_readiness(transport=_transport({"unexpected": []}))
    unavailable = await check_local_model_readiness(transport=_transport({"error": "hidden"}, 503))

    assert (missing.ready, missing.status) == (False, "model_unavailable")
    assert (malformed.ready, malformed.status) == (False, "runtime_unavailable")
    assert (unavailable.ready, unavailable.status) == (False, "runtime_unavailable")


async def test_readiness_rejects_missing_local_model_configuration(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.local_model_name", "")

    readiness = await check_local_model_readiness(transport=_transport({"models": [{"name": "qwen3:8b"}]}))

    assert (readiness.ready, readiness.status) == (False, "configuration_invalid")
