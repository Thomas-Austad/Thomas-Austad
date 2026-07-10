from __future__ import annotations

import uuid
from pathlib import Path

from pydantic import BaseModel, Field

from app.config import settings
from app.models.schemas import utc_now


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    target_type: str
    target_id: str
    result: str
    request_id: str
    actor_id: str = "local_user"
    occurred_at: str = Field(default_factory=lambda: utc_now().isoformat())


class JsonlAuditLog:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or settings.audit_log_path)

    def record(self, event: AuditEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(event.model_dump_json())
            stream.write("\n")


def record_approval_audit_event(
    application_id: str,
    result: str,
    request_id: str,
    actor_id: str = "local_user",
) -> None:
    JsonlAuditLog().record(
        AuditEvent(
            action="application.approve",
            target_type="application",
            target_id=application_id,
            result=result,
            request_id=request_id,
            actor_id=actor_id,
        )
    )


def record_screening_confirmation_audit_event(
    application_id: str,
    result: str,
    request_id: str,
    actor_id: str = "local_user",
) -> None:
    JsonlAuditLog().record(
        AuditEvent(
            action="application.screening_confirmation",
            target_type="application",
            target_id=application_id,
            result=result,
            request_id=request_id,
            actor_id=actor_id,
        )
    )


def record_profile_correction_audit_event(
    candidate_id: str,
    result: str,
    request_id: str,
    actor_id: str = "local_user",
) -> None:
    JsonlAuditLog().record(
        AuditEvent(
            action="profile.correct",
            target_type="candidate_profile",
            target_id=candidate_id,
            result=result,
            request_id=request_id,
            actor_id=actor_id,
        )
    )


def read_audit_events(path: str | Path) -> list[AuditEvent]:
    audit_path = Path(path)
    if not audit_path.exists():
        return []
    return [
        AuditEvent.model_validate_json(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
