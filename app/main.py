import secrets
import uuid
import io
import json
import re
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator
from pydantic import Field
from app.agents.profile_agent import CandidateProfileAgent
from app.agents.compensation_agent import CompensationAgent
from app.agents.match_agent import MatchAgent
from app.agents.application_agent import ApplicationAgent
from app.models.schemas import (
    BrowserHandoff,
    BrowserHandoffPreview,
    BrowserHandoffProvider,
    BrowserHandoffReceipt,
    ConfirmedScreeningAnswer,
    JobSearchFilters,
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
from app.services.browser_session_service import BrowserSessionStore
from app.services.audit_service import (
    record_approval_audit_event,
    record_browser_handoff_audit_event,
    record_profile_correction_audit_event,
    record_profile_data_action_audit_event,
    record_screening_confirmation_audit_event,
)
from app import store
from app.config import settings
from app.rate_limit import client_identifier, rate_limiter, route_rate_limit

app = FastAPI(title="Talent Advisor Platform", version="0.1.0")
BROWSER_SESSION_COOKIE = "talent_advisor_browser_session"
BROWSER_UI_DIST_DIR = Path(__file__).resolve().parents[1] / "browser_ui_dist"
browser_sessions = BrowserSessionStore(
    bootstrap_ttl_seconds=settings.browser_bootstrap_ttl_seconds,
    session_ttl_seconds=settings.browser_session_ttl_seconds,
)

ShortText = Annotated[str, Field(min_length=1, max_length=128)]
MediumText = Annotated[str, Field(max_length=2_000)]
LongText = Annotated[str, Field(max_length=50_000)]
ScreeningQuestionText = Annotated[str, Field(min_length=1, max_length=1_000)]


class ProfileRequest(BaseModel):
    candidate_id: ShortText
    resume_text: LongText
    linkedin_text: LongText = ""
    preferences: dict = Field(default_factory=dict)


class JobSearchRequest(JobSearchFilters):
    greenhouse_boards: list[ShortText] = Field(default_factory=list, max_length=25)
    lever_companies: list[ShortText] = Field(default_factory=list, max_length=25)
    ashby_job_boards: list[ShortText] = Field(default_factory=list, max_length=25)
    public_job_board_urls: list[str] = Field(default_factory=list, max_length=25)

    @model_validator(mode="after")
    def require_currency_for_compensation_filter(self) -> "JobSearchRequest":
        if self.minimum_salary is not None and self.compensation_currency is None:
            raise ValueError("compensation_currency is required with minimum_salary")
        parsed_boards: dict[str, list[str]] = {"greenhouse": [], "lever": [], "ashby": []}
        for board_url in self.public_job_board_urls:
            provider, board_key = _parse_public_job_board_url(board_url)
            parsed_boards[provider].append(board_key)
        self.greenhouse_boards = list(dict.fromkeys([*self.greenhouse_boards, *parsed_boards["greenhouse"]]))
        self.lever_companies = list(dict.fromkeys([*self.lever_companies, *parsed_boards["lever"]]))
        self.ashby_job_boards = list(dict.fromkeys([*self.ashby_job_boards, *parsed_boards["ashby"]]))
        if any(len(boards) > 25 for boards in (self.greenhouse_boards, self.lever_companies, self.ashby_job_boards)):
            raise ValueError("No more than 25 boards per provider may be searched")
        return self


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


class BrowserHandoffRequest(BaseModel):
    confirmed_by_user: bool = False
    expected_destination_url: str = Field(min_length=1, max_length=2_000)
    idempotency_key: str = Field(min_length=16, max_length=128)


class BrowserBootstrapRequest(BaseModel):
    bootstrap_token: str = Field(min_length=32, max_length=256)


_PUBLIC_JOB_BOARD_HOSTS = {
    "boards.greenhouse.io": "greenhouse",
    "job-boards.greenhouse.io": "greenhouse",
    "jobs.lever.co": "lever",
    "jobs.ashbyhq.com": "ashby",
}
_PUBLIC_JOB_BOARD_KEY = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _parse_public_job_board_url(board_url: str) -> tuple[str, str]:
    """Reduce an untrusted public careers URL to a supported connector board key."""
    parsed = urlsplit(board_url)
    provider = _PUBLIC_JOB_BOARD_HOSTS.get(parsed.hostname or "")
    path_segments = [segment for segment in parsed.path.split("/") if segment]
    if (
        parsed.scheme != "https"
        or provider is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or len(path_segments) != 1
        or not _PUBLIC_JOB_BOARD_KEY.fullmatch(path_segments[0])
    ):
        raise ValueError("Use a supported public careers-board link")
    return provider, path_segments[0]


def _is_public_browser_path(path: str) -> bool:
    return path == "/health" or path == "/app" or path.startswith("/app/") or path == "/browser-session/bootstrap"


def _browser_origin_is_valid(request: Request) -> bool:
    if request.headers.get("origin") != settings.public_base_url.rstrip("/"):
        return False
    fetch_site = request.headers.get("sec-fetch-site")
    return fetch_site in {None, "same-origin", "none"}


def _require_browser_confirmation(request: Request, action: str) -> None:
    if getattr(request.state, "browser_session", False) and request.headers.get("x-user-confirmed") != "true":
        raise HTTPException(400, f"{action} requires direct user confirmation")


_BROWSER_HANDOFF_HOSTS: dict[BrowserHandoffProvider, set[str]] = {
    "ashby": {"jobs.ashbyhq.com"},
    "greenhouse": {"boards.greenhouse.io", "job-boards.greenhouse.io"},
    "lever": {"jobs.lever.co"},
}


def get_application_package(application_id: str):
    package = store.applications.get(application_id)
    if not package:
        raise HTTPException(404, "Application not found")
    return package


def _browser_handoff_preview(application_id: str) -> BrowserHandoffPreview:
    package = get_application_package(application_id)
    if package.status != "approved":
        raise HTTPException(409, "Only locally approved applications can start browser handoff")
    job = store.jobs.get(package.job_id)
    if job is None:
        raise HTTPException(409, "Browser handoff is unavailable for this application")
    if job.source not in _BROWSER_HANDOFF_HOSTS:
        raise HTTPException(409, "Browser handoff is unavailable for this application")

    destination_url = str(job.source_url)
    parsed = urlsplit(destination_url)
    allowed_hosts = _BROWSER_HANDOFF_HOSTS[job.source]
    if (
        parsed.scheme != "https"
        or parsed.hostname not in allowed_hosts
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise HTTPException(409, "Browser handoff is unavailable for this application")

    return BrowserHandoffPreview(
        application_id=package.application_id,
        job_id=job.job_id,
        provider=job.source,
        company=job.company,
        title=job.title,
        destination_url=destination_url,
    )


def get_browser_handoff_preview(application_id: str) -> BrowserHandoffPreview:
    """Return the validated employer destination without opening or submitting anything."""
    return _browser_handoff_preview(application_id)


def begin_browser_handoff(
    application_id: str,
    expected_destination_url: str,
    confirmed_by_user: bool,
    request_id: str,
    actor_id: str,
) -> BrowserHandoff:
    if not confirmed_by_user:
        raise HTTPException(400, "Browser handoff requires direct user confirmation")
    preview = _browser_handoff_preview(application_id)
    if expected_destination_url != str(preview.destination_url):
        raise HTTPException(409, "Browser handoff destination changed; review it again")

    package = get_application_package(application_id)
    existing = next(
        (receipt for receipt in package.browser_handoff_receipts if receipt.request_id == request_id),
        None,
    )
    if existing is not None:
        if str(existing.destination_url) != str(preview.destination_url):
            raise HTTPException(409, "Browser handoff request cannot be reused for a different destination")
        return BrowserHandoff(
            application_id=package.application_id,
            job_id=package.job_id,
            provider=preview.provider,
            destination_url=existing.destination_url,
            request_id=request_id,
        )

    updated_package = package.model_copy(deep=True)
    updated_package.browser_handoff_receipts.append(
        BrowserHandoffReceipt(request_id=request_id, destination_url=preview.destination_url)
    )
    store.applications[application_id] = updated_package
    try:
        record_browser_handoff_audit_event(application_id, "ready", request_id, actor_id)
    except OSError as exc:
        store.applications[application_id] = package
        raise HTTPException(503, "Unable to record required audit receipt") from exc
    return BrowserHandoff(
        application_id=package.application_id,
        job_id=package.job_id,
        provider=preview.provider,
        destination_url=preview.destination_url,
        request_id=request_id,
    )


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
    if _is_public_browser_path(request.url.path):
        response = await call_next(request)
        if request.url.path == "/app" or request.url.path.startswith("/app/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; "
                "form-action 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'"
            )
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    session_id = request.cookies.get(BROWSER_SESSION_COOKIE)
    if session_id:
        if request.headers.get("authorization"):
            return JSONResponse(status_code=400, content={"detail": "Choose one local authentication method"})
        session = browser_sessions.get_session(session_id)
        if session is None:
            return JSONResponse(status_code=401, content={"detail": "Browser session expired"})
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            csrf_token = request.headers.get("x-csrf-token", "")
            if not _browser_origin_is_valid(request) or not browser_sessions.validate_csrf(session, csrf_token):
                return JSONResponse(status_code=403, content={"detail": "Browser request could not be verified"})
        request.state.actor_id = local_auth_service.LOCAL_ACTOR_ID
        request.state.browser_session = True
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


@app.post("/browser-session/launch")
def create_browser_launch() -> dict[str, str]:
    """Create one short-lived launcher URL without returning the bearer credential."""
    bootstrap_token = browser_sessions.create_bootstrap()
    return {"browser_url": f"{settings.public_base_url.rstrip('/')}/app#bootstrap={bootstrap_token}"}


@app.post("/browser-session/bootstrap")
def bootstrap_browser_session(payload: BrowserBootstrapRequest, response: Response) -> dict[str, str]:
    """Exchange a launcher-only value for an opaque, HttpOnly browser session."""
    session = browser_sessions.redeem_bootstrap(payload.bootstrap_token)
    if session is None:
        raise HTTPException(401, "Browser startup link is invalid or expired")
    response.set_cookie(
        BROWSER_SESSION_COOKIE,
        session.session_id,
        max_age=settings.browser_session_ttl_seconds,
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"csrf_token": session.csrf_token}


@app.post("/browser-session/logout")
def logout_browser_session(request: Request, response: Response) -> dict[str, str]:
    session_id = request.cookies.get(BROWSER_SESSION_COOKIE)
    if session_id:
        browser_sessions.revoke(session_id)
    response.delete_cookie(BROWSER_SESSION_COOKIE, path="/")
    return {"status": "signed_out"}


@app.get("/app", include_in_schema=False)
@app.get("/app/", include_in_schema=False)
def browser_application() -> FileResponse:
    index = BROWSER_UI_DIST_DIR / "browser.html"
    if not index.is_file():
        raise HTTPException(503, "Browser workspace assets are unavailable")
    return FileResponse(index)


app.mount("/app", StaticFiles(directory=BROWSER_UI_DIST_DIR, check_dir=False), name="browser-ui")


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
    _require_browser_confirmation(request, "Profile correction")
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
    result = await JobService().search_known_boards(
        req.greenhouse_boards,
        req.lever_companies,
        req.ashby_job_boards,
        req,
    )
    for job in result.jobs:
        store.jobs[job.job_id] = job
    return {"count": len(result.jobs), "jobs": result.jobs, "provider_errors": result.provider_errors}


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


@app.get("/applications/{application_id}")
def review_application(application_id: ShortText):
    return get_application_package(application_id)


@app.post("/applications/{application_id}/approve")
def approve_application(application_id: str, request: Request):
    _require_browser_confirmation(request, "Application approval")
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    return approve_prepared_application(application_id, request_id, request.state.actor_id)


@app.get("/applications/{application_id}/browser-handoff")
def preview_browser_handoff(application_id: str):
    return get_browser_handoff_preview(application_id)


@app.post("/applications/{application_id}/browser-handoff")
def create_browser_handoff(
    application_id: str,
    handoff: BrowserHandoffRequest,
    request: Request,
) -> BrowserHandoff:
    return begin_browser_handoff(
        application_id,
        handoff.expected_destination_url,
        handoff.confirmed_by_user,
        handoff.idempotency_key,
        request.state.actor_id,
    )


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
def download_resume(application_id: str, request: Request):
    _require_browser_confirmation(request, "DOCX export")
    package = store.applications.get(application_id)
    if not package:
        raise HTTPException(404, "Application not found")
    content = markdown_resume_to_docx(package.tailored_resume_markdown)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="{application_id}-resume.docx"'})
