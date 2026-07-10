import os

import pytest

os.environ["APP_ENV"] = "test"
os.environ["LOCAL_ACCESS_TOKEN"] = "test-local-access-token-that-is-at-least-32-characters"

from app import store
from app.rate_limit import rate_limiter
from app.models.schemas import (
    ApplicationPackage,
    CandidateProfile,
    CompensationEstimate,
    JobListing,
    JobMatch,
    ScoreDetail,
    Skill,
)


@pytest.fixture(autouse=True)
def clear_store():
    rate_limiter.clear()
    store.profiles.clear()
    store.jobs.clear()
    store.matches.clear()
    store.applications.clear()
    yield
    rate_limiter.clear()
    store.profiles.clear()
    store.jobs.clear()
    store.matches.clear()
    store.applications.clear()


@pytest.fixture
def sample_profile() -> CandidateProfile:
    return CandidateProfile(
        candidate_id="candidate-123",
        name="Synthetic Candidate",
        headline="Backend platform engineer",
        current_level="Senior",
        primary_functions=["backend", "platform"],
        skills=[Skill(name="Python", proficiency=0.9, years=6)],
        experience=[],
    )


@pytest.fixture
def sample_job() -> JobListing:
    return JobListing(
        job_id="greenhouse:example:1",
        source="greenhouse",
        source_url="https://example.com/jobs/1",
        company="Example Co",
        title="Senior Backend Engineer",
        location="Remote",
        remote_type="remote",
        description="Build Python APIs and reliable platform services.",
        salary_min=150000,
        salary_max=190000,
    )


@pytest.fixture
def sample_match(sample_profile: CandidateProfile, sample_job: JobListing) -> JobMatch:
    detail = ScoreDetail(score=85, reasons=["Strong Python platform evidence."])
    return JobMatch(
        candidate_id=sample_profile.candidate_id,
        job_id=sample_job.job_id,
        qualification_fit=detail,
        evidence_strength=detail,
        seniority_alignment=detail,
        compensation_alignment=detail,
        preference_fit=detail,
        competitiveness=detail,
        overall_score=85,
        recommendation="apply",
    )


@pytest.fixture
def sample_compensation() -> CompensationEstimate:
    return CompensationEstimate(
        role_family="Backend Engineering",
        geography="Remote US",
        base_low=150000,
        base_mid=170000,
        base_high=190000,
        confidence=0.7,
        rationale=["Comparable postings support this range."],
        as_of="2026-07-08",
    )


@pytest.fixture
def sample_application(sample_profile: CandidateProfile, sample_job: JobListing) -> ApplicationPackage:
    return ApplicationPackage(
        application_id="application-123",
        candidate_id=sample_profile.candidate_id,
        job_id=sample_job.job_id,
        tailored_resume_markdown="# Synthetic Candidate\n## Experience\n- Built Python APIs",
        cover_letter="I am interested in this backend platform role.",
        screening_answers={},
        factual_warnings=[],
        requires_user_input=[],
    )
