from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from fastapi import Request

from app.config import settings


@dataclass
class Window:
    started_at: float
    count: int = 0


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._windows: dict[tuple[str, str], Window] = {}

    def check(self, *, client_id: str, bucket: str, limit: int, window_seconds: int) -> bool:
        if limit <= 0:
            return False
        now = monotonic()
        key = (client_id, bucket)
        window = self._windows.get(key)
        if window is None or now - window.started_at >= window_seconds:
            self._windows[key] = Window(started_at=now, count=1)
            return True
        if window.count >= limit:
            return False
        window.count += 1
        return True

    def clear(self) -> None:
        self._windows.clear()


rate_limiter = InMemoryRateLimiter()


def client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    if request.client:
        return request.client.host
    return "unknown"


def route_rate_limit(request: Request) -> tuple[str, int]:
    path = request.url.path
    method = request.method.upper()
    if method == "POST" and path == "/resumes/extract":
        return "upload", settings.api_upload_rate_limit
    if method == "POST" and path == "/jobs/search":
        return "job_search", settings.api_job_search_rate_limit
    if method == "GET" and path.endswith("/resume.docx"):
        return "document_generation", settings.api_document_rate_limit
    if method == "POST" and (
        path == "/profiles"
        or path.startswith("/matches/")
        or path.startswith("/compensation/")
        or path == "/applications/prepare"
    ):
        return "model_backed", settings.api_model_rate_limit
    if method == "POST" and path.startswith("/applications/"):
        return "write", settings.api_write_rate_limit
    return "default", settings.api_default_rate_limit
