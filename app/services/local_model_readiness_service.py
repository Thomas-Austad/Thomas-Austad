"""Bounded readiness checks for the configured loopback-only Ollama runtime."""

import json
from typing import Any

import httpx

from app.config import settings
from app.models.schemas import LocalModelReadiness


async def check_local_model_readiness(
    *, transport: httpx.AsyncBaseTransport | None = None
) -> LocalModelReadiness:
    """Return a minimal readiness state without exposing runtime details."""
    if settings.model_provider != "ollama" or not settings.local_model_name.strip():
        return LocalModelReadiness(ready=False, status="configuration_invalid")

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
            transport=transport,
        ) as client:
            async with client.stream(
                "GET",
                f"{settings.local_model_base_url}/api/tags",
                headers={"Accept": "application/json"},
            ) as response:
                if response.is_error or response.is_redirect:
                    return LocalModelReadiness(ready=False, status="runtime_unavailable")
                payload = await _read_bounded_json(response)
    except (httpx.HTTPError, ValueError, json.JSONDecodeError):
        return LocalModelReadiness(ready=False, status="runtime_unavailable")

    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return LocalModelReadiness(ready=False, status="runtime_unavailable")
    names = {item.get("name") for item in models if isinstance(item, dict) and isinstance(item.get("name"), str)}
    if settings.local_model_name not in names:
        return LocalModelReadiness(ready=False, status="model_unavailable")
    return LocalModelReadiness(ready=True, status="ready")


async def _read_bounded_json(response: httpx.Response) -> dict[str, Any]:
    content_length = response.headers.get("content-length")
    if content_length and int(content_length) > settings.model_max_response_bytes:
        raise ValueError("local runtime readiness response is too large")
    content = bytearray()
    async for chunk in response.aiter_bytes():
        content.extend(chunk)
        if len(content) > settings.model_max_response_bytes:
            raise ValueError("local runtime readiness response is too large")
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("local runtime readiness response is invalid")
    return payload
