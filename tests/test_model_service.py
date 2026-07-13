import pytest

from app.services.model_service import ModelServiceUnavailable, create_model_service


def test_factory_uses_explicitly_selected_openai_provider(monkeypatch) -> None:
    created = object()

    class FakeOpenAIService:
        def __new__(cls):
            return created

    monkeypatch.setattr("app.config.settings.model_provider", "openai")
    monkeypatch.setattr("app.services.openai_service.OpenAIService", FakeOpenAIService)

    assert create_model_service() is created


def test_factory_never_falls_back_from_the_selected_local_provider(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.model_provider", "ollama")

    with pytest.raises(ModelServiceUnavailable, match="configured local model provider"):
        create_model_service()
