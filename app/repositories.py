from __future__ import annotations

import uuid
import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.engine import Engine

from app.models.schemas import (
    ApplicationPackage,
    CandidateProfile,
    EvidenceRecord,
    JobListing,
    JobMatch,
    ProfileCorrectionRecord,
    ProfileCorrectionRequest,
)
from app.config import settings
from app.services.data_protection_service import SensitiveDataIntegrityError, protector

metadata = sa.MetaData()

users_table = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("email", sa.Text(), unique=True),
)

candidate_profiles_table = sa.Table(
    "candidate_profiles",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("external_id", sa.Text(), nullable=False, unique=True),
    sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id")),
    sa.Column("profile", sa.JSON(), nullable=False),
    sa.Index("ix_candidate_profiles_user_id", "user_id"),
)

career_evidence_table = sa.Table(
    "career_evidence",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column(
        "candidate_profile_id",
        sa.Uuid(),
        sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("source_type", sa.Text(), nullable=False),
    sa.Column("source_ref", sa.Text()),
    sa.Column("excerpt", sa.Text(), nullable=False),
    sa.Column("confidence", sa.Numeric(), nullable=False),
    sa.Column("claim_type", sa.Text(), nullable=False),
    sa.Column("claim_ref", sa.Text(), nullable=False),
    sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_career_evidence_confidence"),
    sa.Index("ix_career_evidence_candidate_profile_id", "candidate_profile_id"),
)

profile_corrections_table = sa.Table(
    "profile_corrections",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column(
        "candidate_profile_id",
        sa.Uuid(),
        sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("field", sa.Text(), nullable=False),
    sa.Column("value", sa.JSON(), nullable=False),
    sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
    sa.Index("ix_profile_corrections_candidate_profile_id", "candidate_profile_id"),
)

jobs_table = sa.Table(
    "jobs",
    metadata,
    sa.Column("id", sa.Text(), primary_key=True),
    sa.Column("source", sa.Text(), nullable=False),
    sa.Column("source_url", sa.Text(), nullable=False, unique=True),
    sa.Column("company", sa.Text(), nullable=False),
    sa.Column("title", sa.Text(), nullable=False),
    sa.Column("location", sa.Text()),
    sa.Column("description", sa.Text(), nullable=False),
    sa.Column("salary_min", sa.Integer()),
    sa.Column("salary_max", sa.Integer()),
    sa.Column("active", sa.Boolean(), default=True),
    sa.Column("raw", sa.JSON()),
    sa.Column("listing", sa.JSON(), nullable=False),
    sa.CheckConstraint(
        "(salary_min IS NULL OR salary_min >= 0) AND "
        "(salary_max IS NULL OR salary_max >= 0) AND "
        "(salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)",
        name="ck_jobs_salary_range",
    ),
)

job_matches_table = sa.Table(
    "job_matches",
    metadata,
    sa.Column(
        "candidate_profile_id",
        sa.Uuid(),
        sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column("job_id", sa.Text(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("scores", sa.JSON(), nullable=False),
    sa.Column("overall_score", sa.Numeric(), nullable=False),
    sa.Column("recommendation", sa.Text(), nullable=False),
    sa.Column("match", sa.JSON(), nullable=False),
    sa.CheckConstraint("overall_score >= 0 AND overall_score <= 100", name="ck_job_matches_overall_score"),
    sa.CheckConstraint(
        "recommendation IN ('apply', 'consider', 'skip')",
        name="ck_job_matches_recommendation",
    ),
    sa.Index("ix_job_matches_job_id", "job_id"),
)

applications_table = sa.Table(
    "applications",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("application_key", sa.Text(), nullable=False, unique=True),
    sa.Column(
        "candidate_profile_id",
        sa.Uuid(),
        sa.ForeignKey("candidate_profiles.id"),
        nullable=False,
    ),
    sa.Column("job_id", sa.Text(), sa.ForeignKey("jobs.id"), nullable=False),
    sa.Column("package", sa.JSON(), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
    sa.CheckConstraint(
        "status IN ('prepared', 'approved', 'submitted', 'failed')",
        name="ck_applications_status",
    ),
    sa.Index("ix_applications_candidate_profile_id", "candidate_profile_id"),
    sa.Index("ix_applications_job_id", "job_id"),
)

T = TypeVar("T", bound=BaseModel)
K = TypeVar("K")


def _dump_model(model: BaseModel) -> dict:
    return model.model_dump(mode="json")


def _encrypt_payload(payload: dict, purpose: str, record_id: str) -> dict:
    return protector.encrypt_json(payload, purpose=purpose, record_id=record_id)


def _decrypt_payload(payload: object, purpose: str, record_id: str) -> dict:
    if not _is_encrypted(payload):
        if settings.require_encrypted_storage:
            raise SensitiveDataIntegrityError("Sensitive plaintext requires migration")
        if isinstance(payload, dict):
            return payload
        raise SensitiveDataIntegrityError("Sensitive data has an unexpected shape")
    result = protector.decrypt_json(payload, purpose=purpose, record_id=record_id)
    if not isinstance(result, dict):
        raise SensitiveDataIntegrityError("Encrypted data has an unexpected shape")
    return result


def _encrypt_text(value: str, purpose: str, record_id: str) -> str:
    return json.dumps(
        protector.encrypt_json(value, purpose=purpose, record_id=record_id),
        separators=(",", ":"),
        sort_keys=True,
    )


def _decrypt_text(value: str, purpose: str, record_id: str) -> str:
    try:
        envelope = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        if not settings.require_encrypted_storage and isinstance(value, str):
            return value
        raise SensitiveDataIntegrityError("Sensitive plaintext requires migration") from exc
    if not _is_encrypted(envelope):
        if not settings.require_encrypted_storage and isinstance(value, str):
            return value
        raise SensitiveDataIntegrityError("Sensitive plaintext requires migration")
    result = protector.decrypt_json(envelope, purpose=purpose, record_id=record_id)
    if not isinstance(result, str):
        raise SensitiveDataIntegrityError("Encrypted data has an unexpected shape")
    return result


def _is_encrypted(value: object) -> bool:
    return isinstance(value, dict) and set(value) == {"version", "key_version", "nonce", "ciphertext"}


def _profile_evidence_records(profile: CandidateProfile) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    for skill in profile.skills:
        for evidence in skill.evidence:
            records.append(
                EvidenceRecord(
                    candidate_id=profile.candidate_id,
                    claim_type="skill",
                    claim_ref=skill.name,
                    source=evidence.source,
                    text=evidence.text,
                    confidence=evidence.confidence,
                )
            )
    for experience in profile.experience:
        claim_ref = f"{experience.employer}: {experience.title}"
        for evidence in experience.evidence:
            records.append(
                EvidenceRecord(
                    candidate_id=profile.candidate_id,
                    claim_type="experience",
                    claim_ref=claim_ref,
                    source=evidence.source,
                    text=evidence.text,
                    confidence=evidence.confidence,
                )
            )
    for ambiguity in profile.ambiguities:
        records.append(
            EvidenceRecord(
                candidate_id=profile.candidate_id,
                claim_type="ambiguity",
                claim_ref=ambiguity,
                source="profile",
                text=ambiguity,
                confidence=0,
            )
        )
    return records


class ProfileRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def set(self, key: str, value: CandidateProfile) -> None:
        payload = _dump_model(value)
        with self.engine.begin() as connection:
            existing_id = connection.scalar(
                sa.select(candidate_profiles_table.c.id).where(
                    candidate_profiles_table.c.external_id == key
                )
            )
            if existing_id:
                canonical_profile = self._apply_saved_corrections(connection, existing_id, value)
                connection.execute(
                    candidate_profiles_table.update()
                    .where(candidate_profiles_table.c.external_id == key)
                    .values(profile=_encrypt_payload(_dump_model(canonical_profile), "profile", key))
                )
                self._replace_evidence(connection, existing_id, value)
                return
            profile_id = uuid.uuid4()
            connection.execute(
                candidate_profiles_table.insert().values(
                    id=profile_id,
                    external_id=key,
                    profile=_encrypt_payload(payload, "profile", key),
                )
            )
            self._replace_evidence(connection, profile_id, value)

    def _apply_saved_corrections(
        self,
        connection: sa.Connection,
        profile_id: uuid.UUID,
        profile: CandidateProfile,
    ) -> CandidateProfile:
        rows = connection.execute(
            sa.select(
                profile_corrections_table.c.id,
                profile_corrections_table.c.field,
                profile_corrections_table.c.value,
            )
            .where(profile_corrections_table.c.candidate_profile_id == profile_id)
            .order_by(profile_corrections_table.c.corrected_at, profile_corrections_table.c.id)
        ).all()
        updates = {
            row.field: _decrypt_payload(row.value, "profile_correction", str(row.id))["value"]
            for row in rows
        }
        return profile.model_copy(update=updates) if updates else profile

    def _replace_evidence(
        self,
        connection: sa.Connection,
        profile_id: uuid.UUID,
        profile: CandidateProfile,
    ) -> None:
        connection.execute(
            career_evidence_table.delete().where(
                career_evidence_table.c.candidate_profile_id == profile_id
            )
        )
        for record in _profile_evidence_records(profile):
            evidence_id = uuid.uuid4()
            connection.execute(
                career_evidence_table.insert().values(
                    id=evidence_id,
                    candidate_profile_id=profile_id,
                    source_type=record.source,
                    source_ref=(
                        _encrypt_text(record.source_ref, "evidence", str(evidence_id))
                        if record.source_ref is not None
                        else None
                    ),
                    excerpt=_encrypt_text(record.text, "evidence", str(evidence_id)),
                    confidence=record.confidence,
                    claim_type=record.claim_type,
                    claim_ref=_encrypt_text(record.claim_ref, "evidence", str(evidence_id)),
                )
            )

    def get(self, key: str) -> CandidateProfile | None:
        with self.engine.begin() as connection:
            row = connection.execute(
                sa.select(candidate_profiles_table.c.external_id, candidate_profiles_table.c.profile).where(
                    candidate_profiles_table.c.external_id == key
                )
            ).one_or_none()
        return (
            CandidateProfile.model_validate(_decrypt_payload(row.profile, "profile", row.external_id))
            if row
            else None
        )

    def clear(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(profile_corrections_table.delete())
            connection.execute(career_evidence_table.delete())
            connection.execute(candidate_profiles_table.delete())

    def delete(self, key: str) -> bool:
        with self.engine.begin() as connection:
            profile_id = connection.scalar(
                sa.select(candidate_profiles_table.c.id).where(
                    candidate_profiles_table.c.external_id == key
                )
            )
            if profile_id is None:
                return False
            connection.execute(
                applications_table.delete().where(applications_table.c.candidate_profile_id == profile_id)
            )
            connection.execute(
                job_matches_table.delete().where(job_matches_table.c.candidate_profile_id == profile_id)
            )
            connection.execute(
                profile_corrections_table.delete().where(
                    profile_corrections_table.c.candidate_profile_id == profile_id
                )
            )
            connection.execute(
                career_evidence_table.delete().where(
                    career_evidence_table.c.candidate_profile_id == profile_id
                )
            )
            connection.execute(candidate_profiles_table.delete().where(candidate_profiles_table.c.id == profile_id))
        return True

    def values(self) -> list[CandidateProfile]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                sa.select(candidate_profiles_table.c.external_id, candidate_profiles_table.c.profile)
            ).all()
        return [
            CandidateProfile.model_validate(_decrypt_payload(row.profile, "profile", row.external_id))
            for row in rows
        ]


@dataclass(frozen=True)
class AppliedProfileCorrections:
    candidate_id: str
    original_profile: CandidateProfile
    updated_profile: CandidateProfile
    correction_ids: tuple[uuid.UUID, ...]


class ProfileCorrectionRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def apply(
        self,
        candidate_id: str,
        corrections: ProfileCorrectionRequest,
    ) -> AppliedProfileCorrections | None:
        fields = corrections.corrected_fields()
        if not fields:
            raise ValueError("At least one profile correction is required")

        with self.engine.begin() as connection:
            row = connection.execute(
                sa.select(candidate_profiles_table.c.id, candidate_profiles_table.c.profile).where(
                    candidate_profiles_table.c.external_id == candidate_id
                )
            ).one_or_none()
            if row is None:
                return None

            original_profile = CandidateProfile.model_validate(
                _decrypt_payload(row.profile, "profile", candidate_id)
            )
            updates = {field: getattr(corrections, field) for field in fields}
            updated_profile = original_profile.model_copy(update=updates)
            payload = _dump_model(updated_profile)
            connection.execute(
                candidate_profiles_table.update()
                .where(candidate_profiles_table.c.id == row.id)
                .values(profile=_encrypt_payload(payload, "profile", candidate_id))
            )
            correction_ids: list[uuid.UUID] = []
            for field in sorted(fields):
                correction_id = uuid.uuid4()
                correction_ids.append(correction_id)
                connection.execute(
                    profile_corrections_table.insert().values(
                        id=correction_id,
                        candidate_profile_id=row.id,
                        field=field,
                        value=_encrypt_payload(
                            {"value": payload[field]},
                            "profile_correction",
                            str(correction_id),
                        ),
                        corrected_at=updated_profile.generated_at,
                    )
                )
        return AppliedProfileCorrections(
            candidate_id=candidate_id,
            original_profile=original_profile,
            updated_profile=updated_profile,
            correction_ids=tuple(correction_ids),
        )

    def revert(self, applied: AppliedProfileCorrections) -> None:
        with self.engine.begin() as connection:
            profile_id = connection.scalar(
                sa.select(candidate_profiles_table.c.id).where(
                    candidate_profiles_table.c.external_id == applied.candidate_id
                )
            )
            if profile_id is None:
                raise KeyError(f"Candidate profile not found: {applied.candidate_id}")
            connection.execute(
                profile_corrections_table.delete().where(
                    profile_corrections_table.c.candidate_profile_id == profile_id,
                    profile_corrections_table.c.id.in_(applied.correction_ids),
                )
            )
            connection.execute(
                candidate_profiles_table.update()
                .where(candidate_profiles_table.c.id == profile_id)
                .values(
                    profile=_encrypt_payload(
                        _dump_model(applied.original_profile),
                        "profile",
                        applied.candidate_id,
                    )
                )
            )

    def for_candidate(self, candidate_id: str) -> list[ProfileCorrectionRecord]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                sa.select(
                    profile_corrections_table.c.id,
                    profile_corrections_table.c.field,
                    profile_corrections_table.c.value,
                    profile_corrections_table.c.corrected_at,
                )
                .join(
                    candidate_profiles_table,
                    candidate_profiles_table.c.id
                    == profile_corrections_table.c.candidate_profile_id,
                )
                .where(candidate_profiles_table.c.external_id == candidate_id)
                .order_by(profile_corrections_table.c.corrected_at, profile_corrections_table.c.id)
            ).all()
        return [
            ProfileCorrectionRecord(
                correction_id=str(row.id),
                candidate_id=candidate_id,
                field=row.field,
                value=_decrypt_payload(row.value, "profile_correction", str(row.id))["value"],
                corrected_at=row.corrected_at,
            )
            for row in rows
        ]


class EvidenceRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def for_candidate(self, candidate_id: str) -> list[EvidenceRecord]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                sa.select(
                    career_evidence_table.c.id,
                    career_evidence_table.c.source_type,
                    career_evidence_table.c.source_ref,
                    career_evidence_table.c.excerpt,
                    career_evidence_table.c.confidence,
                    career_evidence_table.c.claim_type,
                    career_evidence_table.c.claim_ref,
                )
                .join(
                    candidate_profiles_table,
                    candidate_profiles_table.c.id == career_evidence_table.c.candidate_profile_id,
                )
                .where(candidate_profiles_table.c.external_id == candidate_id)
                .order_by(career_evidence_table.c.id)
            ).all()
        records = [
            EvidenceRecord(
                candidate_id=candidate_id,
                claim_type=row.claim_type,
                claim_ref=_decrypt_text(row.claim_ref, "evidence", str(row.id)),
                source=row.source_type,
                source_ref=(
                    _decrypt_text(row.source_ref, "evidence", str(row.id))
                    if row.source_ref is not None
                    else None
                ),
                text=_decrypt_text(row.excerpt, "evidence", str(row.id)),
                confidence=float(row.confidence),
            )
            for row in rows
        ]
        source_order = {"resume": 0, "linkedin": 1, "user": 2, "job": 3, "profile": 4}
        return sorted(
            records,
            key=lambda record: (record.claim_type, record.claim_ref, source_order[record.source]),
        )


class JobRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def set(self, key: str, value: JobListing) -> None:
        payload = _dump_model(value)
        row = {
            "id": key,
            "source": value.source,
            "source_url": str(value.source_url),
            "company": value.company,
            "title": value.title,
            "location": value.location,
            "description": value.description,
            "salary_min": value.salary_min,
            "salary_max": value.salary_max,
            "active": value.active,
            "raw": value.raw,
            "listing": payload,
        }
        with self.engine.begin() as connection:
            exists = connection.scalar(sa.select(jobs_table.c.id).where(jobs_table.c.id == key))
            if exists:
                connection.execute(jobs_table.update().where(jobs_table.c.id == key).values(**row))
                return
            connection.execute(jobs_table.insert().values(**row))

    def get(self, key: str) -> JobListing | None:
        with self.engine.begin() as connection:
            payload = connection.scalar(sa.select(jobs_table.c.listing).where(jobs_table.c.id == key))
        return JobListing.model_validate(payload) if payload else None

    def clear(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(jobs_table.delete())

    def values(self) -> list[JobListing]:
        with self.engine.begin() as connection:
            rows = connection.scalars(sa.select(jobs_table.c.listing)).all()
        return [JobListing.model_validate(row) for row in rows]


class MatchRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def set(self, key: tuple[str, str], value: JobMatch) -> None:
        candidate_id, job_id = key
        payload = _dump_model(value)
        with self.engine.begin() as connection:
            profile_id = connection.scalar(
                sa.select(candidate_profiles_table.c.id).where(
                    candidate_profiles_table.c.external_id == candidate_id
                )
            )
            if profile_id is None:
                raise KeyError(f"Candidate profile not found: {candidate_id}")
            exists = connection.scalar(
                sa.select(job_matches_table.c.job_id).where(
                    job_matches_table.c.candidate_profile_id == profile_id,
                    job_matches_table.c.job_id == job_id,
                )
            )
            row = {
                "candidate_profile_id": profile_id,
                "job_id": job_id,
                "scores": _encrypt_payload(payload, "match", f"{candidate_id}:{job_id}:scores"),
                "overall_score": value.overall_score,
                "recommendation": value.recommendation,
                "match": _encrypt_payload(payload, "match", f"{candidate_id}:{job_id}:match"),
            }
            if exists:
                connection.execute(
                    job_matches_table.update()
                    .where(
                        job_matches_table.c.candidate_profile_id == profile_id,
                        job_matches_table.c.job_id == job_id,
                    )
                    .values(**row)
                )
                return
            connection.execute(job_matches_table.insert().values(**row))

    def get(self, key: tuple[str, str]) -> JobMatch | None:
        candidate_id, job_id = key
        with self.engine.begin() as connection:
            payload = connection.scalar(
                sa.select(job_matches_table.c.match)
                .join(
                    candidate_profiles_table,
                    candidate_profiles_table.c.id == job_matches_table.c.candidate_profile_id,
                )
                .where(
                    candidate_profiles_table.c.external_id == candidate_id,
                    job_matches_table.c.job_id == job_id,
                )
            )
        return (
            JobMatch.model_validate(
                _decrypt_payload(payload, "match", f"{candidate_id}:{job_id}:match")
            )
            if payload
            else None
        )

    def clear(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(job_matches_table.delete())


class ApplicationRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def set(self, key: str, value: ApplicationPackage) -> None:
        payload = _dump_model(value)
        with self.engine.begin() as connection:
            profile_id = connection.scalar(
                sa.select(candidate_profiles_table.c.id).where(
                    candidate_profiles_table.c.external_id == value.candidate_id
                )
            )
            if profile_id is None:
                raise KeyError(f"Candidate profile not found: {value.candidate_id}")
            job_exists = connection.scalar(sa.select(jobs_table.c.id).where(jobs_table.c.id == value.job_id))
            if job_exists is None:
                raise KeyError(f"Job not found: {value.job_id}")
            exists = connection.scalar(
                sa.select(applications_table.c.id).where(applications_table.c.application_key == key)
            )
            row = {
                "application_key": key,
                "candidate_profile_id": profile_id,
                "job_id": value.job_id,
                "package": _encrypt_payload(payload, "application", key),
                "status": value.status,
            }
            if exists:
                connection.execute(
                    applications_table.update()
                    .where(applications_table.c.application_key == key)
                    .values(**row)
                )
                return
            connection.execute(applications_table.insert().values(id=uuid.uuid4(), **row))

    def get(self, key: str) -> ApplicationPackage | None:
        with self.engine.begin() as connection:
            payload = connection.scalar(
                sa.select(applications_table.c.package).where(
                    applications_table.c.application_key == key
                )
            )
        return (
            ApplicationPackage.model_validate(_decrypt_payload(payload, "application", key))
            if payload
            else None
        )

    def clear(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(applications_table.delete())


class ModelMapping(Generic[K, T]):
    def __init__(self, repository) -> None:
        self.repository = repository

    def __setitem__(self, key: K, value: T) -> None:
        self.repository.set(key, value)

    def __getitem__(self, key: K) -> T:
        value = self.repository.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def get(self, key: K) -> T | None:
        return self.repository.get(key)

    def clear(self) -> None:
        self.repository.clear()

    def delete(self, key: K) -> bool:
        if not hasattr(self.repository, "delete"):
            raise TypeError("Repository does not support deletion")
        return self.repository.delete(key)

    def values(self) -> list[T]:
        if not hasattr(self.repository, "values"):
            raise TypeError("Repository does not support values")
        return self.repository.values()

    def __iter__(self) -> Iterator[K]:
        raise TypeError("Repository mappings do not support key iteration")


class RepositoryStore:
    def __init__(self, engine: Engine) -> None:
        self.profiles = ModelMapping[str, CandidateProfile](ProfileRepository(engine))
        self.evidence = EvidenceRepository(engine)
        self.profile_corrections = ProfileCorrectionRepository(engine)
        self.jobs = ModelMapping[str, JobListing](JobRepository(engine))
        self.matches = ModelMapping[tuple[str, str], JobMatch](MatchRepository(engine))
        self.applications = ModelMapping[str, ApplicationPackage](ApplicationRepository(engine))


def create_repository_store(engine: Engine) -> RepositoryStore:
    return RepositoryStore(engine)
