from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, JsonValue


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


ProfileCorrectionField = Literal[
    "name",
    "headline",
    "current_level",
    "primary_functions",
    "skills",
    "experience",
    "education",
    "certifications",
    "preferences",
    "ambiguities",
]


class ProfileCorrectionRequest(BaseModel):
    """User-supplied replacements for selected candidate-profile fields."""

    name: str | None = Field(default=None, min_length=1, max_length=256)
    headline: str | None = Field(default=None, min_length=1, max_length=2_000)
    current_level: str | None = Field(default=None, min_length=1, max_length=256)
    primary_functions: list[str] | None = Field(default=None, max_length=50)
    skills: list[Skill] | None = Field(default=None, max_length=200)
    experience: list[WorkExperience] | None = Field(default=None, max_length=100)
    education: list[str] | None = Field(default=None, max_length=100)
    certifications: list[str] | None = Field(default=None, max_length=100)
    preferences: CandidatePreferences | None = None
    ambiguities: list[str] | None = Field(default=None, max_length=100)

    def corrected_fields(self) -> set[ProfileCorrectionField]:
        return set(self.model_fields_set)


class ProfileCorrectionRecord(BaseModel):
    correction_id: str
    candidate_id: str
    field: ProfileCorrectionField
    value: JsonValue
    corrected_at: datetime = Field(default_factory=utc_now)


class ProfileReview(BaseModel):
    profile: CandidateProfile
    evidence: list[EvidenceRecord]
    corrections: list[ProfileCorrectionRecord]


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


class ProviderSearchError(BaseModel):
    """Safe provider-level failure disclosure for a completed job search."""

    provider: Literal["ashby", "greenhouse", "lever"]


class LocalModelReadiness(BaseModel):
    """Safe local-runtime readiness state; never includes runtime payloads or settings."""

    ready: bool
    status: Literal["ready", "runtime_unavailable", "model_unavailable", "configuration_invalid"]


class JobSearchResult(BaseModel):
    jobs: list[JobListing]
    provider_errors: list[ProviderSearchError] = []


JobSearchFilterText = Annotated[str, Field(min_length=1, max_length=128)]
EmploymentTypeFilterText = Annotated[str, Field(min_length=1, max_length=64)]


class JobSearchFilters(BaseModel):
    title_keywords: list[JobSearchFilterText] = Field(default_factory=list, max_length=20)
    company_keywords: list[JobSearchFilterText] = Field(default_factory=list, max_length=20)
    location_keywords: list[JobSearchFilterText] = Field(default_factory=list, max_length=20)
    remote_mode: Literal["remote", "hybrid", "onsite"] | None = None
    minimum_salary: int | None = Field(default=None, ge=0)
    compensation_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    employment_types: list[EmploymentTypeFilterText] = Field(default_factory=list, max_length=10)
    freshness_days: int | None = Field(default=None, ge=1, le=365)


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


ScreeningQuestionCategory = Literal[
    "personal",
    "legal",
    "demographic",
    "disability",
    "criminal_history",
    "salary_history",
    "work_authorization",
]


class ScreeningQuestionReview(BaseModel):
    question: str
    category: ScreeningQuestionCategory
    reason: str


class ConfirmedScreeningAnswer(BaseModel):
    question: str
    category: ScreeningQuestionCategory
    confirmed_at: datetime = Field(default_factory=utc_now)
    request_id: str


BrowserHandoffProvider = Literal["ashby", "greenhouse", "lever"]


class BrowserHandoffPreview(BaseModel):
    application_id: str
    job_id: str
    provider: BrowserHandoffProvider
    company: str
    title: str
    destination_url: HttpUrl


class BrowserHandoffReceipt(BaseModel):
    request_id: str
    destination_url: HttpUrl
    issued_at: datetime = Field(default_factory=utc_now)


class BrowserHandoff(BaseModel):
    application_id: str
    job_id: str
    provider: BrowserHandoffProvider
    destination_url: HttpUrl
    status: Literal["ready"] = "ready"
    request_id: str


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
    confirmed_screening_answers: list[ConfirmedScreeningAnswer] = []
    browser_handoff_receipts: list[BrowserHandoffReceipt] = []
    status: Literal["prepared", "approved", "submitted", "failed"] = "prepared"


class ExtractedResume(BaseModel):
    filename: str | None = None
    content_type: Literal["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    text: str
    character_count: int
