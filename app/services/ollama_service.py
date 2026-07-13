"""Bounded, local-only Ollama implementation of the model-service contract."""

import json
from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.services.model_service import (
    ModelServiceConfigurationError,
    ModelServiceMalformedOutput,
    ModelServiceOverloaded,
    ModelServiceRequestTooLarge,
    ModelServiceTimeout,
    ModelServiceUnavailable,
)


class OllamaService:
    """Call the configured loopback Ollama runtime without remote fallback."""

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport

    async def structured(self, *, system: str, user: str, schema: type[BaseModel]) -> BaseModel:
        response_schema = schema.model_json_schema()
        trusted_system = (
            f"{system}\n\n"
            "Return only a JSON object that strictly conforms to this trusted response schema:\n"
            f"{json.dumps(response_schema, separators=(',', ':'))}"
        )
        response = await self._chat(
            system=trusted_system,
            user=user,
            response_format=response_schema,
        )
        content = self._message_content(response)
        try:
            parsed = json.loads(content)
            _reject_unexpected_fields(parsed, response_schema)
            return schema.model_validate(parsed)
        except (TypeError, ValueError, ValidationError, json.JSONDecodeError) as exc:
            raise ModelServiceMalformedOutput("The model service returned invalid structured output.") from exc

    async def text(self, *, system: str, user: str) -> str:
        response = await self._chat(system=system, user=user)
        return self._message_content(response)

    async def _chat(
        self,
        *,
        system: str,
        user: str,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if len(system.encode("utf-8")) + len(user.encode("utf-8")) > settings.model_max_request_bytes:
            raise ModelServiceRequestTooLarge("The local model request exceeds the configured size limit.")
        payload: dict[str, Any] = {
            "model": settings.local_model_name,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": 0,
                "num_ctx": settings.model_context_limit,
                "num_predict": settings.model_max_output_tokens,
            },
        }
        if response_format is not None:
            payload["format"] = response_format
        for attempt in range(settings.model_max_retries + 1):
            try:
                return await self._request(payload)
            except (ModelServiceOverloaded, ModelServiceTimeout, ModelServiceUnavailable):
                if attempt == settings.model_max_retries:
                    raise
        raise AssertionError("Model retry loop must return or raise")

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        timeout = httpx.Timeout(
            connect=settings.model_connect_timeout_seconds,
            read=settings.model_read_timeout_seconds,
            write=settings.model_read_timeout_seconds,
            pool=settings.model_connect_timeout_seconds,
        )
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
                transport=self._transport,
            ) as client:
                async with client.stream(
                    "POST",
                    f"{settings.local_model_base_url}/api/chat",
                    json=payload,
                    headers={"Accept": "application/json"},
                ) as response:
                    self._raise_for_status(response)
                    raw_response = await _read_bounded_response(response)
        except httpx.TimeoutException as exc:
            raise ModelServiceTimeout("The local model service timed out.") from exc
        except httpx.RequestError as exc:
            raise ModelServiceUnavailable("The local model service is unavailable.") from exc
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ModelServiceMalformedOutput("The local model service returned invalid JSON.") from exc
        if not isinstance(data, dict):
            raise ModelServiceMalformedOutput("The local model service returned an invalid response.")
        return data

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_redirect:
            raise ModelServiceUnavailable("The local model service redirected the request.")
        if response.status_code == 429:
            raise ModelServiceOverloaded("The local model service is overloaded.")
        if response.status_code == 404:
            raise ModelServiceConfigurationError("The configured local model is unavailable.")
        if response.status_code >= 500:
            raise ModelServiceUnavailable("The local model service is unavailable.")
        if response.is_error:
            raise ModelServiceConfigurationError("The local model service rejected the request.")

    @staticmethod
    def _message_content(response: dict[str, Any]) -> str:
        message = response.get("message")
        if not isinstance(message, dict):
            raise ModelServiceMalformedOutput("The local model service returned no message.")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ModelServiceMalformedOutput("The local model service returned empty output.")
        return content


async def _read_bounded_response(response: httpx.Response) -> bytes:
    content_length = response.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.model_max_response_bytes:
                raise ModelServiceMalformedOutput("The local model response exceeded the configured size limit.")
        except ValueError as exc:
            raise ModelServiceMalformedOutput("The local model response had an invalid size.") from exc
    content = bytearray()
    async for chunk in response.aiter_bytes():
        content.extend(chunk)
        if len(content) > settings.model_max_response_bytes:
            raise ModelServiceMalformedOutput("The local model response exceeded the configured size limit.")
    return bytes(content)


def _reject_unexpected_fields(value: Any, schema: Mapping[str, Any], root_schema: Mapping[str, Any] | None = None) -> None:
    """Reject fields that Pydantic's default extra=ignore behavior would discard."""
    root = root_schema or schema
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
            raise ValueError("Unsupported model schema reference")
        definition_name = reference.removeprefix("#/$defs/")
        definitions = root.get("$defs")
        if not isinstance(definitions, Mapping) or not isinstance(definitions.get(definition_name), Mapping):
            raise ValueError("Unknown model schema reference")
        _reject_unexpected_fields(value, definitions[definition_name], root)
        return
    alternatives = schema.get("anyOf") or schema.get("oneOf")
    if isinstance(alternatives, list):
        for alternative in alternatives:
            if not isinstance(alternative, Mapping):
                continue
            try:
                _reject_unexpected_fields(value, alternative, root)
            except ValueError:
                continue
            return
        raise ValueError("Model output does not match an allowed schema variant")
    if isinstance(value, dict):
        properties = schema.get("properties")
        additional_properties = schema.get("additionalProperties", False)
        if not isinstance(properties, Mapping):
            properties = {}
        for key, item in value.items():
            property_schema = properties.get(key)
            if isinstance(property_schema, Mapping):
                _reject_unexpected_fields(item, property_schema, root)
            elif isinstance(additional_properties, Mapping):
                _reject_unexpected_fields(item, additional_properties, root)
            elif additional_properties is not True:
                raise ValueError("Model output contains an unexpected field")
    elif isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for item in value:
                _reject_unexpected_fields(item, item_schema, root)
