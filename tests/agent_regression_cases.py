from dataclasses import dataclass

from app.models.schemas import (
    CandidateProfile,
    Evidence,
    JobListing,
    JobMatch,
    ScoreDetail,
    Skill,
)


@dataclass(frozen=True)
class MatchRegressionCase:
    name: str
    profile: CandidateProfile
    job: JobListing
    match: JobMatch
    min_overall: float
    max_overall: float
    expected_recommendation: str
    min_evidence_strength: float | None = None
    max_evidence_strength: float | None = None
    min_compensation_alignment: float | None = None
    max_compensation_alignment: float | None = None
    required_disqualifier_terms: tuple[str, ...] = ()


def _detail(score: float, reason: str) -> ScoreDetail:
    return ScoreDetail(score=score, reasons=[reason])


def _profile(candidate_id: str, skills: list[Skill], level: str = "Senior") -> CandidateProfile:
    return CandidateProfile(
        candidate_id=candidate_id,
        name="Synthetic Candidate",
        headline=f"{level} backend engineer",
        current_level=level,
        primary_functions=["backend", "platform"],
        skills=skills,
        experience=[],
    )


def _job(job_id: str, title: str, salary_min: int = 150000, salary_max: int = 190000) -> JobListing:
    return JobListing(
        job_id=job_id,
        source="synthetic",
        source_url=f"https://example.com/jobs/{job_id}",
        company="Example Co",
        title=title,
        location="Remote",
        remote_type="remote",
        description="Build Python APIs, FastAPI services, and reliable platform systems.",
        salary_min=salary_min,
        salary_max=salary_max,
    )


def _match(
    candidate_id: str,
    job_id: str,
    overall: float,
    recommendation: str,
    evidence: float,
    compensation: float = 80,
    seniority: float = 80,
    disqualifiers: list[str] | None = None,
) -> JobMatch:
    return JobMatch(
        candidate_id=candidate_id,
        job_id=job_id,
        qualification_fit=_detail(overall, "Synthetic qualification assessment."),
        evidence_strength=_detail(evidence, "Synthetic evidence assessment."),
        seniority_alignment=_detail(seniority, "Synthetic seniority assessment."),
        compensation_alignment=_detail(compensation, "Synthetic compensation assessment."),
        preference_fit=_detail(80, "Synthetic preference assessment."),
        competitiveness=_detail(overall, "Synthetic competitiveness assessment."),
        overall_score=overall,
        hard_disqualifiers=disqualifiers or [],
        gaps=[],
        recommendation=recommendation,
    )


def match_regression_cases() -> list[MatchRegressionCase]:
    strong_profile = _profile(
        "case-strong-fit",
        [
            Skill(
                name="Python",
                proficiency=0.95,
                years=7,
                evidence=[Evidence(source="resume", text="Built Python APIs.", confidence=0.92)],
            ),
            Skill(
                name="FastAPI",
                proficiency=0.85,
                years=4,
                evidence=[Evidence(source="resume", text="Owned FastAPI services.", confidence=0.88)],
            ),
        ],
    )
    weak_profile = _profile(
        "case-weak-fit",
        [Skill(name="Content Strategy", proficiency=0.8, years=5)],
        level="Mid",
    )
    missing_evidence_profile = _profile(
        "case-missing-evidence",
        [Skill(name="Python", proficiency=0.8, years=4)],
    )
    over_level_profile = _profile(
        "case-over-level",
        [Skill(name="Python", proficiency=0.9, years=8)],
        level="Staff",
    )
    salary_profile = _profile(
        "case-salary-mismatch",
        [Skill(name="Python", proficiency=0.9, years=6)],
    )
    salary_profile.preferences.minimum_base_salary = 210000

    return [
        MatchRegressionCase(
            name="strong_fit",
            profile=strong_profile,
            job=_job("strong-fit", "Senior Backend Engineer"),
            match=_match("case-strong-fit", "strong-fit", 88, "apply", evidence=90),
            min_overall=80,
            max_overall=100,
            expected_recommendation="apply",
            min_evidence_strength=80,
        ),
        MatchRegressionCase(
            name="weak_fit",
            profile=weak_profile,
            job=_job("weak-fit", "Senior Backend Engineer"),
            match=_match("case-weak-fit", "weak-fit", 38, "skip", evidence=25),
            min_overall=0,
            max_overall=50,
            expected_recommendation="skip",
            max_evidence_strength=50,
        ),
        MatchRegressionCase(
            name="missing_evidence",
            profile=missing_evidence_profile,
            job=_job("missing-evidence", "Senior Backend Engineer"),
            match=_match("case-missing-evidence", "missing-evidence", 55, "consider", evidence=35),
            min_overall=35,
            max_overall=70,
            expected_recommendation="consider",
            max_evidence_strength=50,
        ),
        MatchRegressionCase(
            name="over_level",
            profile=over_level_profile,
            job=_job("over-level", "Junior Backend Engineer", 90000, 120000),
            match=_match("case-over-level", "over-level", 45, "skip", evidence=80, seniority=25),
            min_overall=0,
            max_overall=60,
            expected_recommendation="skip",
            required_disqualifier_terms=(),
        ),
        MatchRegressionCase(
            name="salary_mismatch",
            profile=salary_profile,
            job=_job("salary-mismatch", "Senior Backend Engineer", 150000, 170000),
            match=_match(
                "case-salary-mismatch",
                "salary-mismatch",
                58,
                "consider",
                evidence=80,
                compensation=30,
            ),
            min_overall=40,
            max_overall=70,
            expected_recommendation="consider",
            max_compensation_alignment=50,
        ),
    ]
