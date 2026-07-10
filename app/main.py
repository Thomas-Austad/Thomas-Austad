import uuid

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
from pydantic import Field
from app.agents.profile_agent import CandidateProfileAgent
from app.agents.compensation_agent import CompensationAgent
from app.agents.match_agent import MatchAgent
from app.agents.application_agent import ApplicationAgent
from app.models.schemas import ConfirmedScreeningAnswer
from app.services.job_service import JobService
from app.services.document_service import (
    MAX_RESUME_UPLOAD_BYTES,
    ResumeExtractionError,
    extract_resume_text,
    markdown_resume_to_docx,
)
from app.services.audit_service import record_approval_audit_event
from app import store

app = FastAPI(title="Talent Advisor Platform", version="0.1.0")


class ProfileRequest(BaseModel):
    candidate_id: str
    resume_text: str
    linkedin_text: str = ""
    preferences: dict = {}


class JobSearchRequest(BaseModel):
    greenhouse_boards: list[str] = []
    lever_companies: list[str] = []
    title_keywords: list[str] = []


class ApplicationRequest(BaseModel):
    candidate_id: str
    job_id: str
    screening_questions: list[str] = []


class ScreeningQuestionResolutionRequest(BaseModel):
    question: str
    answer: str = Field(min_length=1)
    confirmed_by_user: bool = False


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/profiles")
async def create_profile(req: ProfileRequest):
    profile = await CandidateProfileAgent().run(req.candidate_id, req.resume_text, req.linkedin_text, req.preferences)
    store.profiles[profile.candidate_id] = profile
    return profile


@app.post("/resumes/extract")
async def extract_resume(file: UploadFile = File(...)):
    content = await file.read(MAX_RESUME_UPLOAD_BYTES + 1)
    try:
        return extract_resume_text(content, file.filename)
    except ResumeExtractionError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/jobs/search")
async def search_jobs(req: JobSearchRequest):
    found = await JobService().search_known_boards(req.greenhouse_boards, req.lever_companies)
    if req.title_keywords:
        terms = [t.lower() for t in req.title_keywords]
        found = [j for j in found if any(t in (j.title + " " + j.description).lower() for t in terms)]
    for job in found:
        store.jobs[job.job_id] = job
    return {"count": len(found), "jobs": found}


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
    package = store.applications.get(application_id)
    if not package:
        raise HTTPException(404, "Application not found")
    if package.requires_user_input or package.unresolved_screening_questions:
        raise HTTPException(409, "Resolve required user inputs before approval")
    package.status = "approved"
    store.applications[application_id] = package
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    record_approval_audit_event(application_id, "approved", request_id)
    return package


@app.post("/applications/{application_id}/screening-questions/resolve")
def resolve_screening_question(
    application_id: str,
    req: ScreeningQuestionResolutionRequest,
    request: Request,
):
    package = store.applications.get(application_id)
    if not package:
        raise HTTPException(404, "Application not found")
    if package.status != "prepared":
        raise HTTPException(409, "Screening questions can only be resolved before approval")
    if not req.confirmed_by_user:
        raise HTTPException(400, "Sensitive screening answers require direct user confirmation")

    review = next(
        (
            unresolved
            for unresolved in package.unresolved_screening_questions
            if unresolved.question == req.question
        ),
        None,
    )
    if review is None:
        raise HTTPException(404, "Unresolved screening question not found")

    package.screening_answers[req.question] = req.answer
    package.unresolved_screening_questions = [
        unresolved
        for unresolved in package.unresolved_screening_questions
        if unresolved.question != req.question
    ]
    package.requires_user_input = [
        required for required in package.requires_user_input if required != req.question
    ]
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    package.confirmed_screening_answers.append(
        ConfirmedScreeningAnswer(
            question=req.question,
            category=review.category,
            request_id=request_id,
        )
    )
    store.applications[application_id] = package
    return package


@app.get("/applications/{application_id}/resume.docx")
def download_resume(application_id: str):
    package = store.applications.get(application_id)
    if not package:
        raise HTTPException(404, "Application not found")
    content = markdown_resume_to_docx(package.tailored_resume_markdown)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="{application_id}-resume.docx"'})
