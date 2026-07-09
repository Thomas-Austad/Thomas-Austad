from app.services.openai_service import OpenAIService


def test_openai_service_configures_timeout_and_retries(monkeypatch) -> None:
    captured = {}

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("app.services.openai_service.AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setattr("app.services.openai_service.settings.openai_api_key", "test-key")
    monkeypatch.setattr("app.services.openai_service.settings.openai_timeout_seconds", 12)
    monkeypatch.setattr("app.services.openai_service.settings.openai_max_retries", 3)

    OpenAIService()

    assert captured == {
        "api_key": "test-key",
        "timeout": 12,
        "max_retries": 3,
    }
