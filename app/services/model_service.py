"""Provider-neutral model-service contract and safe failure semantics."""

from typing import Protocol

from pydantic import BaseModel



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
    """Return the sole local model provider; remote fallback is not supported."""
    from app.services.ollama_service import OllamaService

    return OllamaService()
