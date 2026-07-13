import json

import httpx
import pytest
from pydantic import BaseModel

from app.services.model_service import (
    ModelServiceConfigurationError,
    ModelServiceMalformedOutput,
    ModelServiceOverloaded,
    ModelServiceRequestTooLarge,
    ModelServiceTimeout,
    ModelServiceUnavailable,
)
from app.services.ollama_service import OllamaService


class StructuredReply(BaseModel):
    answer: str


class NestedReply(BaseModel):
    item: StructuredReply


def _service(handler) -> OllamaService:
    return OllamaService(transport=httpx.MockTransport(handler))


def _successful_response(content: str) -> httpx.Response:
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


async def test_structured_request_uses_fixed_local_endpoint_schema_and_bounds(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["payload"] = json.loads(request.content)
        return _successful_response('{"answer":"synthetic"}')

    monkeypatch.setattr("app.config.settings.local_model_name", "qwen3:8b")
    monkeypatch.setattr("app.config.settings.model_context_limit", 8_192)
    monkeypatch.setattr("app.config.settings.model_max_output_tokens", 512)

    result = await _service(handler).structured(system="System", user="Synthetic", schema=StructuredReply)

    assert result == StructuredReply(answer="synthetic")
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["payload"] == {
        "model": "qwen3:8b",
        "stream": False,
        "think": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "System\n\nReturn only a JSON object that strictly conforms to this trusted response schema:\n"
                    '{"properties":{"answer":{"title":"Answer","type":"string"}},'
                    '"required":["answer"],"title":"StructuredReply","type":"object"}'
                ),
            },
            {"role": "user", "content": "Synthetic"},
        ],
        "options": {"temperature": 0, "num_ctx": 8_192, "num_predict": 512},
        "format": StructuredReply.model_json_schema(),
    }


async def test_structured_output_rejects_malformed_partial_and_unexpected_fields() -> None:
    malformed = _service(lambda _request: _successful_response("not json"))
    partial = _service(lambda _request: _successful_response("{}"))
    unexpected = _service(lambda _request: _successful_response('{"answer":"synthetic","extra":"blocked"}'))
    nested_unexpected = _service(
        lambda _request: _successful_response('{"item":{"answer":"synthetic","extra":"blocked"}}')
    )

    with pytest.raises(ModelServiceMalformedOutput):
        await malformed.structured(system="System", user="Synthetic", schema=StructuredReply)
    with pytest.raises(ModelServiceMalformedOutput):
        await partial.structured(system="System", user="Synthetic", schema=StructuredReply)
    with pytest.raises(ModelServiceMalformedOutput):
        await unexpected.structured(system="System", user="Synthetic", schema=StructuredReply)
    with pytest.raises(ModelServiceMalformedOutput):
        await nested_unexpected.structured(system="System", user="Synthetic", schema=NestedReply)


async def test_local_runtime_connection_and_timeout_fail_safely_without_retry_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.model_max_retries", 0)

    def connection_failure(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unavailable", request=request)

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(ModelServiceUnavailable):
        await _service(connection_failure).text(system="System", user="Synthetic")
    with pytest.raises(ModelServiceTimeout):
        await _service(timeout).text(system="System", user="Synthetic")


async def test_overload_retries_only_to_the_configured_bound(monkeypatch) -> None:
    attempts = 0

    def overloaded(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, json={"error": "busy"})

    monkeypatch.setattr("app.config.settings.model_max_retries", 1)

    with pytest.raises(ModelServiceOverloaded):
        await _service(overloaded).text(system="System", user="Synthetic")

    assert attempts == 2


async def test_missing_model_and_oversized_response_fail_safely(monkeypatch) -> None:
    missing_model = _service(lambda _request: httpx.Response(404, json={"error": "missing"}))
    oversized = _service(lambda _request: _successful_response('{"answer":"synthetic"}'))

    with pytest.raises(ModelServiceConfigurationError):
        await missing_model.text(system="System", user="Synthetic")

    monkeypatch.setattr("app.config.settings.model_max_response_bytes", 10)
    with pytest.raises(ModelServiceMalformedOutput):
        await oversized.text(system="System", user="Synthetic")


async def test_oversized_request_is_rejected_before_a_local_request(monkeypatch) -> None:
    requested = False

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal requested
        requested = True
        return _successful_response("synthetic")

    monkeypatch.setattr("app.config.settings.model_max_request_bytes", 10)

    with pytest.raises(ModelServiceRequestTooLarge):
        await _service(handler).text(system="System", user="Synthetic")

    assert requested is False
