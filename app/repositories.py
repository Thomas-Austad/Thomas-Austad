from __future__ import annotations

import uuid
from collections.abc import Iterator
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
)

metadata = sa.MetaData()

candidate_profiles_table = sa.Table(
    "candidate_profiles",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("external_id", sa.Text(), nullable=False, unique=True),
    sa.Column("profile", sa.JSON(), nullable=False),
)

career_evidence_table = sa.Table(
    "career_evidence",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("candidate_profile_id", sa.Uuid(), nullable=False),
    sa.Column("source_type", sa.Text(), nullable=False),
    sa.Column("source_ref", sa.Text()),
    sa.Column("excerpt", sa.Text(), nullable=False),
    sa.Column("confidence", sa.Numeric(), nullable=False),
    sa.Column("claim_type", sa.Text(), nullable=False),
    sa.Column("claim_ref", sa.Text(), nullable=False),
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
)

job_matches_table = sa.Table(
    "job_matches",
    metadata,
    sa.Column("candidate_profile_id", sa.Uuid(), primary_key=True),
    sa.Column("job_id", sa.Text(), primary_key=True),
    sa.Column("scores", sa.JSON(), nullable=False),
    sa.Column("overall_score", sa.Numeric(), nullable=False),
    sa.Column("recommendation", sa.Text(), nullable=False),
    sa.Column("match", sa.JSON(), nullable=False),
)

applications_table = sa.Table(
    "applications",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("application_key", sa.Text(), nullable=False, unique=True),
    sa.Column("candidate_profile_id", sa.Uuid()),
    sa.Column("job_id", sa.Text()),
    sa.Column("package", sa.JSON(), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
)

T = TypeVar("T", bound=BaseModel)
K = TypeVar("K")


def _dump_model(model: BaseModel) -> dict:
    return model.model_dump(mode="json")


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
                connection.execute(
                    candidate_profiles_table.update()
                    .where(candidate_profiles_table.c.external_id == key)
                    .values(profile=payload)
                )
                self._replace_evidence(connection, existing_id, value)
                return
            profile_id = uuid.uuid4()
            connection.execute(
                candidate_profiles_table.insert().values(
                    id=profile_id,
                    external_id=key,
                    profile=payload,
                )
            )
            self._replace_evidence(connection, profile_id, value)

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
            connection.execute(
                career_evidence_table.insert().values(
                    id=uuid.uuid4(),
                    candidate_profile_id=profile_id,
                    source_type=record.source,
                    source_ref=record.source_ref,
                    excerpt=record.text,
                    confidence=record.confidence,
                    claim_type=record.claim_type,
                    claim_ref=record.claim_ref,
                )
            )

    def get(self, key: str) -> CandidateProfile | None:
        with self.engine.begin() as connection:
            payload = connection.scalar(
                sa.select(candidate_profiles_table.c.profile).where(
                    candidate_profiles_table.c.external_id == key
                )
            )
        return CandidateProfile.model_validate(payload) if payload else None

    def clear(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(career_evidence_table.delete())
            connection.execute(candidate_profiles_table.delete())

    def values(self) -> list[CandidateProfile]:
        with self.engine.begin() as connection:
            rows = connection.scalars(sa.select(candidate_profiles_table.c.profile)).all()
        return [CandidateProfile.model_validate(row) for row in rows]


class EvidenceRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def for_candidate(self, candidate_id: str) -> list[EvidenceRecord]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                sa.select(
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
                .order_by(career_evidence_table.c.claim_type, career_evidence_table.c.claim_ref)
            ).all()
        return [
            EvidenceRecord(
                candidate_id=candidate_id,
                claim_type=row.claim_type,
                claim_ref=row.claim_ref,
                source=row.source_type,
                source_ref=row.source_ref,
                text=row.excerpt,
                confidence=float(row.confidence),
            )
            for row in rows
        ]


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
                "scores": payload,
                "overall_score": value.overall_score,
                "recommendation": value.recommendation,
                "match": payload,
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
        return JobMatch.model_validate(payload) if payload else None

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
            exists = connection.scalar(
                sa.select(applications_table.c.id).where(applications_table.c.application_key == key)
            )
            row = {
                "application_key": key,
                "candidate_profile_id": profile_id,
                "job_id": value.job_id,
                "package": payload,
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
        return ApplicationPackage.model_validate(payload) if payload else None

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
        self.jobs = ModelMapping[str, JobListing](JobRepository(engine))
        self.matches = ModelMapping[tuple[str, str], JobMatch](MatchRepository(engine))
        self.applications = ModelMapping[str, ApplicationPackage](ApplicationRepository(engine))


def create_repository_store(engine: Engine) -> RepositoryStore:
    return RepositoryStore(engine)
