from app.services.model_service import create_model_service
from app.services.ollama_service import OllamaService


def test_factory_uses_explicitly_selected_openai_provider(monkeypatch) -> None:
    created = object()

    class FakeOpenAIService:
        def __new__(cls):
            return created

    monkeypatch.setattr("app.config.settings.model_provider", "openai")
    monkeypatch.setattr("app.services.openai_service.OpenAIService", FakeOpenAIService)

    assert create_model_service() is created


def test_factory_uses_the_explicitly_selected_local_provider(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.model_provider", "ollama")

    assert isinstance(create_model_service(), OllamaService)
