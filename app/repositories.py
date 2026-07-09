from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Generic, TypeVar

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.engine import Engine

from app.models.schemas import ApplicationPackage, CandidateProfile, JobListing, JobMatch

metadata = sa.MetaData()

candidate_profiles_table = sa.Table(
    "candidate_profiles",
    metadata,
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("external_id", sa.Text(), nullable=False, unique=True),
    sa.Column("profile", sa.JSON(), nullable=False),
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
                return
            connection.execute(
                candidate_profiles_table.insert().values(
                    id=uuid.uuid4(),
                    external_id=key,
                    profile=payload,
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
            connection.execute(candidate_profiles_table.delete())

    def values(self) -> list[CandidateProfile]:
        with self.engine.begin() as connection:
            rows = connection.scalars(sa.select(candidate_profiles_table.c.profile)).all()
        return [CandidateProfile.model_validate(row) for row in rows]


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
        self.jobs = ModelMapping[str, JobListing](JobRepository(engine))
        self.matches = ModelMapping[tuple[str, str], JobMatch](MatchRepository(engine))
        self.applications = ModelMapping[str, ApplicationPackage](ApplicationRepository(engine))


def create_repository_store(engine: Engine) -> RepositoryStore:
    return RepositoryStore(engine)
