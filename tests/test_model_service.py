from app.services.model_service import create_model_service
from app.services.ollama_service import OllamaService


def test_factory_uses_the_sole_local_provider() -> None:
    assert isinstance(create_model_service(), OllamaService)
