"""Provider-neutral model-service contract and safe failure semantics."""

from typing import Protocol

from pydantic import BaseModel

from app.config import settings


class ModelServiceError(Exception):
    """Base error whose subclasses are safe to map to public recovery messages."""


class ModelServiceUnavailable(ModelServiceError):
    """The configured model service cannot currently be reached."""


class ModelServiceTimeout(ModelServiceError):
    """The configured model service did not respond before its configured timeout."""


class ModelServiceOverloaded(ModelServiceError):
    """The configured model service is temporarily overloaded."""


class ModelServiceConfigurationError(ModelServiceError):
    """The configured model service cannot be used with the current settings."""


class ModelServiceMalformedOutput(ModelServiceError):
    """The configured model service returned output that failed schema validation."""


class ModelServiceRequestTooLarge(ModelServiceError):
    """The requested model operation exceeds its configured local bounds."""


class ModelService(Protocol):
    """Internal contract for deterministic agent workflows using a model provider."""

    async def structured(self, *, system: str, user: str, schema: type[BaseModel]) -> BaseModel: ...

    async def text(self, *, system: str, user: str) -> str: ...


def create_model_service() -> ModelService:
    """Return exactly the configured provider; never fall back to another provider."""
    if settings.model_provider == "openai":
        from app.services.openai_service import OpenAIService

        return OpenAIService()
    if settings.model_provider == "ollama":
        from app.services.ollama_service import OllamaService

        return OllamaService()
    raise ModelServiceConfigurationError("The configured model provider is not supported.")
