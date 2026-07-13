from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError
from app.config import settings
from app.services.model_service import (
    ModelServiceConfigurationError,
    ModelServiceMalformedOutput,
    ModelServiceOverloaded,
    ModelServiceTimeout,
    ModelServiceUnavailable,
)


class OpenAIService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )

    async def structured(self, *, system: str, user: str, schema: type[BaseModel]) -> BaseModel:
        try:
            response = await self.client.responses.parse(
                model=settings.openai_model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                text_format=schema,
            )
        except RateLimitError as exc:
            raise ModelServiceOverloaded("The model service is overloaded.") from exc
        except AuthenticationError as exc:
            raise ModelServiceConfigurationError("The model service configuration is invalid.") from exc
        except APITimeoutError as exc:
            raise ModelServiceTimeout("The model service timed out.") from exc
        except APIConnectionError as exc:
            raise ModelServiceUnavailable("The model service is unavailable.") from exc
        except APIStatusError as exc:
            raise ModelServiceUnavailable("The model service is unavailable.") from exc
        if response.output_parsed is None:
            raise ModelServiceMalformedOutput("The model service returned no structured output.")
        try:
            return schema.model_validate(response.output_parsed)
        except ValidationError as exc:
            raise ModelServiceMalformedOutput("The model service returned invalid structured output.") from exc

    async def text(self, *, system: str, user: str) -> str:
        try:
            response = await self.client.responses.create(
                model=settings.openai_model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except RateLimitError as exc:
            raise ModelServiceOverloaded("The model service is overloaded.") from exc
        except AuthenticationError as exc:
            raise ModelServiceConfigurationError("The model service configuration is invalid.") from exc
        except APITimeoutError as exc:
            raise ModelServiceTimeout("The model service timed out.") from exc
        except APIConnectionError as exc:
            raise ModelServiceUnavailable("The model service is unavailable.") from exc
        except APIStatusError as exc:
            raise ModelServiceUnavailable("The model service is unavailable.") from exc
        if not response.output_text:
            raise ModelServiceMalformedOutput("The model service returned empty text output.")
        return response.output_text
