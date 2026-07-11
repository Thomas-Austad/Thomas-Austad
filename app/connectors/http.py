import json
from collections.abc import Mapping

import httpx

from app.config import settings


async def fetch_provider_json(url: str, *, params: Mapping[str, str] | None = None) -> object:
    """Fetch a bounded JSON response from a fixed, provider-owned HTTPS endpoint."""
    async with httpx.AsyncClient(
        timeout=settings.connector_timeout_seconds,
        follow_redirects=False,
    ) as client:
        async with client.stream(
            "GET",
            url,
            params=params,
            headers={"Accept": "application/json"},
        ) as response:
            if response.is_redirect:
                raise httpx.HTTPStatusError(
                    "Provider redirects are not permitted",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > settings.connector_max_response_bytes:
                raise ValueError("Provider response exceeds the configured size limit")
            content = bytearray()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > settings.connector_max_response_bytes:
                    raise ValueError("Provider response exceeds the configured size limit")
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Provider response is not valid JSON") from exc
