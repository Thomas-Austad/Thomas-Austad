import os

from app.models.schemas import ApplicationPackage, CandidateProfile, JobListing, JobMatch
from app.repositories import create_repository_store


class InMemoryEvidenceRepository:
    def for_candidate(self, candidate_id: str) -> list:
        return []


class InMemoryStore:
    def __init__(self) -> None:
        self.profiles: dict[str, CandidateProfile] = {}
        self.evidence = InMemoryEvidenceRepository()
        self.jobs: dict[str, JobListing] = {}
        self.matches: dict[tuple[str, str], JobMatch] = {}
        self.applications: dict[str, ApplicationPackage] = {}


if os.getenv("APP_ENV") == "test":
    _store = InMemoryStore()
else:
    from app.db import get_engine

    _store = create_repository_store(get_engine())

profiles = _store.profiles
jobs = _store.jobs
matches = _store.matches
applications = _store.applications
