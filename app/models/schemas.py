from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


def utc_now() -> datetime:
    return datetime.now(UTC)


class Evidence(BaseModel):
    source: Literal["resume", "linkedin", "user", "job"]
    text: str
    confidence: float = Field(ge=0, le=1)


class EvidenceRecord(BaseModel):
    candidate_id: str
    claim_type: Literal["skill", "experience", "ambiguity"]
    claim_ref: str
    source: Literal["resume", "linkedin", "user", "job", "profile"]
    text: str
    confidence: float = Field(ge=0, le=1)
    source_ref: str | None = None


class Skill(BaseModel):
    name: str
    proficiency: float = Field(ge=0, le=1)
    years: float | None = None
    evidence: list[Evidence] = []


class WorkExperience(BaseModel):
    employer: str
    title: str
    start_date: str | None = None
    end_date: str | None = None
    achievements: list[str] = []
    evidence: list[Evidence] = []


class CandidatePreferences(BaseModel):
    target_titles: list[str] = []
    target_locations: list[str] = []
    remote_preference: Literal["remote", "hybrid", "onsite", "any"] = "any"
    minimum_base_salary: int | None = None
    industries: list[str] = []
    excluded_companies: list[str] = []
    work_authorization: str | None = None


class CandidateProfile(BaseModel):
    candidate_id: str
    name: str | None = None
    headline: str
    current_level: str
    primary_functions: list[str]
    skills: list[Skill]
    experience: list[WorkExperience]
    education: list[str] = []
    certifications: list[str] = []
    preferences: CandidatePreferences = CandidatePreferences()
    ambiguities: list[str] = []
    generated_at: datetime = Field(default_factory=utc_now)


class CompensationEstimate(BaseModel):
    role_family: str
    geography: str
    base_low: int
    base_mid: int
    base_high: int
    total_comp_low: int | None = None
    total_comp_high: int | None = None
    confidence: float = Field(ge=0, le=1)
    rationale: list[str]
    as_of: str


class JobListing(BaseModel):
    job_id: str
    source: str
    source_url: HttpUrl
    company: str
    title: str
    location: str | None = None
    remote_type: str | None = None
    description: str
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str = "USD"
    employment_type: str | None = None
    posted_at: str | None = None
    active: bool = True
    raw: dict = {}


class ScoreDetail(BaseModel):
    score: float = Field(ge=0, le=100)
    reasons: list[str] = []


class JobMatch(BaseModel):
    candidate_id: str
    job_id: str
    qualification_fit: ScoreDetail
    evidence_strength: ScoreDetail
    seniority_alignment: ScoreDetail
    compensation_alignment: ScoreDetail
    preference_fit: ScoreDetail
    competitiveness: ScoreDetail
    overall_score: float = Field(ge=0, le=100)
    hard_disqualifiers: list[str] = []
    gaps: list[str] = []
    recommendation: Literal["apply", "consider", "skip"]


class ScreeningQuestionReview(BaseModel):
    question: str
    category: Literal[
        "personal",
        "legal",
        "demographic",
        "disability",
        "criminal_history",
        "salary_history",
        "work_authorization",
    ]
    reason: str


class ApplicationPackage(BaseModel):
    application_id: str
    candidate_id: str
    job_id: str
    tailored_resume_markdown: str
    cover_letter: str
    screening_answers: dict[str, str] = {}
    factual_warnings: list[str] = []
    requires_user_input: list[str] = []
    unresolved_screening_questions: list[ScreeningQuestionReview] = []
    status: Literal["prepared", "approved", "submitted", "failed"] = "prepared"


class ExtractedResume(BaseModel):
    filename: str | None = None
    content_type: Literal["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    text: str
    character_count: int
