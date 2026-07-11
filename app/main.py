import secrets
import uuid
import io
import json
import zipfile
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import Field
from app.agents.profile_agent import CandidateProfileAgent
from app.agents.compensation_agent import CompensationAgent
from app.agents.match_agent import MatchAgent
from app.agents.application_agent import ApplicationAgent
from app.models.schemas import (
    ConfirmedScreeningAnswer,
    ProfileCorrectionRequest,
    ProfileReview,
)
from app.services.job_service import JobService
from app.services.document_service import (
    MAX_RESUME_UPLOAD_BYTES,
    ResumeExtractionError,
    extract_resume_text,
    markdown_resume_to_docx,
)
from app.services import local_auth_service
from app.services.audit_service import (
    record_approval_audit_event,
    record_profile_correction_audit_event,
    record_profile_data_action_audit_event,
    record_screening_confirmation_audit_event,
)
from app import store
from app.config import settings
from app.rate_limit import client_identifier, rate_limiter, route_rate_limit

app = FastAPI(title="Talent Advisor Platform", version="0.1.0")

ShortText = Annotated[str, Field(min_length=1, max_length=128)]
MediumText = Annotated[str, Field(max_length=2_000)]
LongText = Annotated[str, Field(max_length=50_000)]
ScreeningQuestionText = Annotated[str, Field(min_length=1, max_length=1_000)]


class ProfileRequest(BaseModel):
    candidate_id: ShortText
    resume_text: LongText
    linkedin_text: LongText = ""
    preferences: dict = Field(default_factory=dict)


class JobSearchRequest(BaseModel):
    greenhouse_boards: list[ShortText] = Field(default_factory=list, max_length=25)
    lever_companies: list[ShortText] = Field(default_factory=list, max_length=25)
    title_keywords: list[ShortText] = Field(default_factory=list, max_length=20)


class ApplicationRequest(BaseModel):
    candidate_id: ShortText
    job_id: MediumText
    screening_questions: list[ScreeningQuestionText] = Field(default_factory=list, max_length=50)


class ScreeningQuestionResolutionRequest(BaseModel):
    question: ScreeningQuestionText
    answer: str = Field(min_length=1, max_length=5_000)
    confirmed_by_user: bool = False


class ProfileDataActionRequest(BaseModel):
    confirmed_by_user: bool = False


def get_application_package(application_id: str):
    package = store.applications.get(application_id)
    if not package:
        raise HTTPException(404, "Application not found")
    return package


def approve_prepared_application(
    application_id: str,
    request_id: str,
    actor_id: str,
):
    package = get_application_package(application_id)
    if package.requires_user_input or package.unresolved_screening_questions:
        raise HTTPException(409, "Resolve required user inputs before approval")
    if package.status != "prepared":
        raise HTTPException(409, "Only prepared applications can be approved")
    approved_package = package.model_copy(update={"status": "approved"})
    store.applications[application_id] = approved_package
    try:
        record_approval_audit_event(application_id, "approved", request_id, actor_id)
    except OSError as exc:
        store.applications[application_id] = package
        raise HTTPException(503, "Unable to record required audit receipt") from exc
    return approved_package


def resolve_application_screening_question(
    application_id: str,
    question: str,
    answer: str,
    confirmed_by_user: bool,
    request_id: str,
    actor_id: str,
):
    package = get_application_package(application_id)
    if package.status != "prepared":
        raise HTTPException(409, "Screening questions can only be resolved before approval")
    if not confirmed_by_user:
        raise HTTPException(400, "Sensitive screening answers require direct user confirmation")

    review = next(
        (
            unresolved
            for unresolved in package.unresolved_screening_questions
            if unresolved.question == question
        ),
        None,
    )
    if review is None:
        raise HTTPException(404, "Unresolved screening question not found")

    updated_package = package.model_copy(deep=True)
    updated_package.screening_answers[question] = answer
    updated_package.unresolved_screening_questions = [
        unresolved
        for unresolved in updated_package.unresolved_screening_questions
        if unresolved.question != question
    ]
    updated_package.requires_user_input = [
        required for required in updated_package.requires_user_input if required != question
    ]
    updated_package.confirmed_screening_answers.append(
        ConfirmedScreeningAnswer(
            question=question,
            category=review.category,
            request_id=request_id,
        )
    )
    store.applications[application_id] = updated_package
    try:
        record_screening_confirmation_audit_event(application_id, "confirmed", request_id, actor_id)
    except OSError as exc:
        store.applications[application_id] = package
        raise HTTPException(503, "Unable to record required audit receipt") from exc
    return updated_package


@app.middleware("http")
async def enforce_rate_limits(request: Request, call_next):
    if settings.api_rate_limit_enabled:
        bucket, limit = route_rate_limit(request)
        allowed = rate_limiter.check(
            client_id=client_identifier(request),
            bucket=bucket,
            limit=limit,
            window_seconds=settings.api_rate_limit_window_seconds,
        )
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    return await call_next(request)


@app.middleware("http")
async def require_local_authentication(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)

    authorization = request.headers.get("authorization", "")
    scheme, _, presented_token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not presented_token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Local authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        expected_token = local_auth_service.get_local_access_token()
    except local_auth_service.LocalCredentialUnavailable:
        return JSONResponse(
            status_code=503,
            content={"detail": "Local authentication is temporarily unavailable"},
        )

    if not secrets.compare_digest(presented_token, expected_token):
        return JSONResponse(
            status_code=401,
            content={"detail": "Local authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.actor_id = local_auth_service.LOCAL_ACTOR_ID
    return await call_next(request)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/profiles")
async def create_profile(req: ProfileRequest):
    profile = await CandidateProfileAgent().run(req.candidate_id, req.resume_text, req.linkedin_text, req.preferences)
    store.profiles[profile.candidate_id] = profile
    return profile


def get_profile_review(candidate_id: str) -> ProfileReview:
    profile = store.profiles.get(candidate_id)
    if profile is None:
        raise HTTPException(404, "Candidate profile not found")
    return ProfileReview(
        profile=profile,
        evidence=store.evidence.for_candidate(candidate_id),
        corrections=store.profile_corrections.for_candidate(candidate_id),
    )


def apply_profile_corrections(
    candidate_id: str,
    corrections: ProfileCorrectionRequest,
    request_id: str,
    actor_id: str,
) -> ProfileReview:
    try:
        applied = store.profile_corrections.apply(candidate_id, corrections)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if applied is None:
        raise HTTPException(404, "Candidate profile not found")
    try:
        record_profile_correction_audit_event(candidate_id, "corrected", request_id, actor_id)
    except OSError as exc:
        store.profile_corrections.revert(applied)
        raise HTTPException(503, "Unable to record required audit receipt") from exc
    return ProfileReview(
        profile=applied.updated_profile,
        evidence=store.evidence.for_candidate(candidate_id),
        corrections=store.profile_corrections.for_candidate(candidate_id),
    )


@app.get("/profiles/{candidate_id}/review")
def review_profile(candidate_id: ShortText) -> ProfileReview:
    return get_profile_review(candidate_id)


@app.patch("/profiles/{candidate_id}")
def correct_profile(
    candidate_id: ShortText,
    corrections: ProfileCorrectionRequest,
    request: Request,
) -> ProfileReview:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    return apply_profile_corrections(
        candidate_id,
        corrections,
        request_id,
        request.state.actor_id,
    )


@app.post("/profiles/{candidate_id}/export")
def export_profile(
    candidate_id: ShortText,
    confirmation: ProfileDataActionRequest,
    request: Request,
):
    if not confirmation.confirmed_by_user:
        raise HTTPException(400, "Profile export requires direct user confirmation")
    review = get_profile_review(candidate_id)
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    try:
        record_profile_data_action_audit_event(
            "profile.export",
            candidate_id,
            "exported",
            request_id,
            request.state.actor_id,
        )
    except OSError as exc:
        raise HTTPException(503, "Unable to record required audit receipt") from exc
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(
            "profile-review.json",
            json.dumps(review.model_dump(mode="json"), ensure_ascii=False, indent=2),
        )
    return Response(
        archive.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="talent-advisor-profile-export.zip"'},
    )


@app.delete("/profiles/{candidate_id}")
def delete_profile(
    candidate_id: ShortText,
    confirmation: ProfileDataActionRequest,
    request: Request,
) -> dict[str, str]:
    if not confirmation.confirmed_by_user:
        raise HTTPException(400, "Profile deletion requires direct user confirmation")
    if store.profiles.get(candidate_id) is None:
        raise HTTPException(404, "Candidate profile not found")
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    try:
        record_profile_data_action_audit_event(
            "profile.delete",
            candidate_id,
            "requested",
            request_id,
            request.state.actor_id,
        )
    except OSError as exc:
        raise HTTPException(503, "Unable to record required audit receipt") from exc
    deleted = (
        store._store.delete_profile(candidate_id)
        if hasattr(store._store, "delete_profile")
        else store.profiles.delete(candidate_id)
    )
    if not deleted:
        raise HTTPException(404, "Candidate profile not found")
    try:
        record_profile_data_action_audit_event(
            "profile.delete",
            candidate_id,
            "deleted",
            request_id,
            request.state.actor_id,
        )
    except OSError as exc:
        raise HTTPException(503, "Profile deletion completed but audit finalization failed") from exc
    return {"status": "deleted"}


@app.get("/privacy/retention")
def retention_review() -> dict:
    cutoff = datetime.now(UTC) - timedelta(days=settings.profile_retention_days)
    due_candidate_ids = [
        profile.candidate_id
        for profile in store.profiles.values()
        if profile.generated_at < cutoff
    ]
    return {
        "profile_retention_days": settings.profile_retention_days,
        "due_candidate_ids": due_candidate_ids,
    }


@app.post("/privacy/retention/purge")
def purge_due_profiles(
    confirmation: ProfileDataActionRequest,
    request: Request,
) -> dict:
    if not confirmation.confirmed_by_user:
        raise HTTPException(400, "Retention purge requires direct user confirmation")
    due_candidate_ids = retention_review()["due_candidate_ids"]
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    deleted_candidate_ids: list[str] = []
    for candidate_id in due_candidate_ids:
        record_profile_data_action_audit_event(
            "profile.retention_purge",
            candidate_id,
            "requested",
            request_id,
            request.state.actor_id,
        )
        deleted = (
            store._store.delete_profile(candidate_id)
            if hasattr(store._store, "delete_profile")
            else store.profiles.delete(candidate_id)
        )
        if deleted:
            deleted_candidate_ids.append(candidate_id)
            record_profile_data_action_audit_event(
                "profile.retention_purge",
                candidate_id,
                "deleted",
                request_id,
                request.state.actor_id,
            )
    return {"deleted_candidate_ids": deleted_candidate_ids}


@app.post("/resumes/extract")
async def extract_resume(file: UploadFile = File(...)):
    content = await file.read(MAX_RESUME_UPLOAD_BYTES + 1)
    try:
        return extract_resume_text(content, file.filename)
    except ResumeExtractionError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/jobs/search")
async def search_jobs(req: JobSearchRequest):
    result = await JobService().search_known_boards(req.greenhouse_boards, req.lever_companies)
    found = result.jobs
    if req.title_keywords:
        terms = [t.lower() for t in req.title_keywords]
        found = [j for j in found if any(t in (j.title + " " + j.description).lower() for t in terms)]
    for job in found:
        store.jobs[job.job_id] = job
    return {"count": len(found), "jobs": found, "provider_errors": result.provider_errors}


@app.post("/matches/{candidate_id}/{job_id}")
async def score_match(candidate_id: str, job_id: str):
    profile = store.profiles.get(candidate_id)
    job = store.jobs.get(job_id)
    if not profile or not job:
        raise HTTPException(404, "Candidate or job not found")
    result = await MatchAgent().run(profile, job)
    store.matches[(candidate_id, job_id)] = result
    return result


@app.post("/compensation/{candidate_id}")
async def estimate_compensation(candidate_id: str, role_family: str, geography: str):
    profile = store.profiles.get(candidate_id)
    if not profile:
        raise HTTPException(404, "Candidate not found")
    comparable = list(store.jobs.values())
    return await CompensationAgent().run(profile, role_family, geography, comparable)


@app.post("/applications/prepare")
async def prepare_application(req: ApplicationRequest):
    profile = store.profiles.get(req.candidate_id)
    job = store.jobs.get(req.job_id)
    if not profile or not job:
        raise HTTPException(404, "Candidate or job not found")
    package = await ApplicationAgent().prepare(profile, job, req.screening_questions)
    store.applications[package.application_id] = package
    return package


@app.post("/applications/{application_id}/approve")
def approve_application(application_id: str, request: Request):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    return approve_prepared_application(application_id, request_id, request.state.actor_id)


@app.post("/applications/{application_id}/screening-questions/resolve")
def resolve_screening_question(
    application_id: str,
    req: ScreeningQuestionResolutionRequest,
    request: Request,
):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    return resolve_application_screening_question(
        application_id,
        req.question,
        req.answer,
        req.confirmed_by_user,
        request_id,
        request.state.actor_id,
    )


@app.get("/applications/{application_id}/resume.docx")
def download_resume(application_id: str):
    package = store.applications.get(application_id)
    if not package:
        raise HTTPException(404, "Application not found")
    content = markdown_resume_to_docx(package.tailored_resume_markdown)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="{application_id}-resume.docx"'})
