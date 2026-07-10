import os
import uuid

from app.models.schemas import (
    ApplicationPackage,
    CandidateProfile,
    EvidenceRecord,
    JobListing,
    JobMatch,
    ProfileCorrectionRecord,
    ProfileCorrectionRequest,
)
from app.repositories import AppliedProfileCorrections, _profile_evidence_records, create_repository_store


class InMemoryEvidenceRepository:
    def __init__(self, profiles: dict[str, CandidateProfile]) -> None:
        self.profiles = profiles
        self.records: dict[str, list[EvidenceRecord]] = {}

    def capture(self, profile: CandidateProfile) -> None:
        self.records[profile.candidate_id] = _profile_evidence_records(profile)

    def for_candidate(self, candidate_id: str) -> list[EvidenceRecord]:
        if candidate_id in self.records:
            return list(self.records[candidate_id])
        profile = self.profiles.get(candidate_id)
        return _profile_evidence_records(profile) if profile else []

    def clear(self) -> None:
        self.records.clear()


class InMemoryProfileCorrectionRepository:
    def __init__(
        self,
        profiles: dict[str, CandidateProfile],
        evidence: InMemoryEvidenceRepository,
    ) -> None:
        self.profiles = profiles
        self.evidence = evidence
        self.corrections: dict[str, list[ProfileCorrectionRecord]] = {}

    def apply(
        self,
        candidate_id: str,
        corrections: ProfileCorrectionRequest,
    ) -> AppliedProfileCorrections | None:
        fields = corrections.corrected_fields()
        if not fields:
            raise ValueError("At least one profile correction is required")
        original_profile = self.profiles.get(candidate_id)
        if original_profile is None:
            return None
        self.evidence.capture(original_profile)
        updates = {field: getattr(corrections, field) for field in fields}
        updated_profile = original_profile.model_copy(update=updates)
        self.profiles[candidate_id] = updated_profile
        payload = updated_profile.model_dump(mode="json")
        records: list[ProfileCorrectionRecord] = []
        for field in sorted(fields):
            records.append(
                ProfileCorrectionRecord(
                    correction_id=str(uuid.uuid4()),
                    candidate_id=candidate_id,
                    field=field,
                    value=payload[field],
                    corrected_at=updated_profile.generated_at,
                )
            )
        self.corrections.setdefault(candidate_id, []).extend(records)
        return AppliedProfileCorrections(
            candidate_id=candidate_id,
            original_profile=original_profile,
            updated_profile=updated_profile,
            correction_ids=tuple(uuid.UUID(record.correction_id) for record in records),
        )

    def revert(self, applied: AppliedProfileCorrections) -> None:
        self.profiles[applied.candidate_id] = applied.original_profile
        correction_ids = {str(correction_id) for correction_id in applied.correction_ids}
        self.corrections[applied.candidate_id] = [
            record
            for record in self.corrections.get(applied.candidate_id, [])
            if record.correction_id not in correction_ids
        ]

    def for_candidate(self, candidate_id: str) -> list[ProfileCorrectionRecord]:
        return list(self.corrections.get(candidate_id, []))

    def clear(self) -> None:
        self.corrections.clear()


class InMemoryStore:
    def __init__(self) -> None:
        self.profiles: dict[str, CandidateProfile] = {}
        self.evidence = InMemoryEvidenceRepository(self.profiles)
        self.profile_corrections = InMemoryProfileCorrectionRepository(self.profiles, self.evidence)
        self.jobs: dict[str, JobListing] = {}
        self.matches: dict[tuple[str, str], JobMatch] = {}
        self.applications: dict[str, ApplicationPackage] = {}


if os.getenv("APP_ENV") == "test":
    _store = InMemoryStore()
else:
    from app.db import get_engine

    _store = create_repository_store(get_engine())

profiles = _store.profiles
evidence = _store.evidence
profile_corrections = _store.profile_corrections
jobs = _store.jobs
matches = _store.matches
applications = _store.applications
