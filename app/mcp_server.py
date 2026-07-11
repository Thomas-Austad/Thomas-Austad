"""Minimal MCP tool surface for ChatGPT. Run separately from FastAPI during development."""
import uuid
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from app.main import (
    apply_profile_corrections,
    approve_prepared_application,
    create_profile,
    estimate_compensation,
    get_application_package,
    get_profile_review,
    prepare_application,
    resolve_application_screening_question,
    score_match,
    search_jobs,
)
from app.main import ApplicationRequest, JobSearchRequest, ProfileRequest, ScreeningQuestionText, ShortText
from pydantic import Field
from typing import Annotated
from app.models.schemas import ProfileCorrectionRequest

mcp = FastMCP("Talent Advisor")

WIDGET_RESOURCE_URI = "ui://talent-advisor/widget.html"
WIDGET_DIST_DIR = Path(__file__).resolve().parents[1] / "widget" / "dist"
WIDGET_TEMPLATE_META = {"openai/outputTemplate": WIDGET_RESOURCE_URI}
WIDGET_RESOURCE_META = {
    "ui": {
        "csp": {
            "connectDomains": [],
            "frameDomains": [],
            "resourceDomains": [],
        }
    }
}


def load_widget_resource() -> str:
    """Return the self-contained local widget without exposing any credential."""
    script = WIDGET_DIST_DIR / "talent-advisor-widget.js"
    stylesheet = WIDGET_DIST_DIR / "talent-advisor-widget.css"
    if not script.is_file() or not stylesheet.is_file():
        raise RuntimeError("Widget assets are unavailable; run the widget build first")
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><style>""" + stylesheet.read_text(
        encoding="utf-8"
    ) + """</style></head><body><talent-advisor-widget></talent-advisor-widget>
<script type="module">""" + script.read_text(encoding="utf-8") + """</script></body></html>"""


@mcp.resource(
    WIDGET_RESOURCE_URI,
    name="Talent Advisor widget",
    description="Local review workspace UI for Talent Advisor MCP tools.",
    mime_type="text/html;profile=mcp-app",
    meta=WIDGET_RESOURCE_META,
)
def talent_advisor_widget() -> str:
    return load_widget_resource()


@mcp.tool()
async def create_candidate_profile(candidate_id: str, resume_text: str, linkedin_text: str = "", preferences: dict | None = None):
    """Create an evidence-grounded candidate profile from resume and LinkedIn text."""
    return (await create_profile(ProfileRequest(candidate_id=candidate_id, resume_text=resume_text,
                                                linkedin_text=linkedin_text, preferences=preferences or {}))).model_dump()


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def review_candidate_profile(candidate_id: str):
    """Read a profile with its source evidence and prior user-provided corrections."""
    return get_profile_review(candidate_id).model_dump(mode="json")


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def correct_candidate_profile(
    candidate_id: str,
    corrections: ProfileCorrectionRequest,
    confirmed_by_user: bool,
):
    """Save explicitly confirmed user corrections; this changes only the local profile."""
    if not confirmed_by_user:
        raise ValueError("Profile corrections require direct user confirmation")
    return apply_profile_corrections(
        candidate_id,
        corrections,
        str(uuid.uuid4()),
        "local_user",
    ).model_dump(mode="json")


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def find_jobs(greenhouse_boards: list[str], lever_companies: list[str], title_keywords: list[str] | None = None):
    """Retrieve active jobs from supported ATS boards."""
    return await search_jobs(JobSearchRequest(greenhouse_boards=greenhouse_boards,
                                              lever_companies=lever_companies,
                                              title_keywords=title_keywords or []))


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def evaluate_job_match(candidate_id: str, job_id: str):
    """Score a candidate against a job and explain gaps and disqualifiers."""
    return (await score_match(candidate_id, job_id)).model_dump()


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def estimate_market_compensation(candidate_id: str, role_family: str, geography: str):
    """Estimate a current compensation range using profile and collected jobs."""
    return (await estimate_compensation(candidate_id, role_family, geography)).model_dump()


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def prepare_job_application(candidate_id: str, job_id: str, screening_questions: list[str] | None = None):
    """Prepare a truthful tailored resume, cover letter, and screening answers for user review."""
    return (await prepare_application(ApplicationRequest(candidate_id=candidate_id, job_id=job_id,
                                                         screening_questions=screening_questions or []))).model_dump(mode="json")


IdempotencyKey = Annotated[str, Field(min_length=16, max_length=128)]
ScreeningAnswer = Annotated[str, Field(min_length=1, max_length=5_000)]


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def get_application_review(application_id: ShortText):
    """Read one local application package for review. This tool has no external effect."""
    return get_application_package(application_id).model_dump(mode="json")


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def resolve_application_screening_answer(
    application_id: ShortText,
    question: ScreeningQuestionText,
    answer: ScreeningAnswer,
    confirmed_by_user: bool,
    idempotency_key: IdempotencyKey,
):
    """Save one directly confirmed screening answer; it never submits an application."""
    if not confirmed_by_user:
        raise ValueError("Sensitive screening answers require direct user confirmation")
    return resolve_application_screening_question(
        application_id,
        question,
        answer,
        confirmed_by_user,
        idempotency_key,
        "local_user",
    ).model_dump(mode="json")


@mcp.tool(meta=WIDGET_TEMPLATE_META)
async def approve_prepared_application_review(
    application_id: ShortText,
    confirmed_by_user: bool,
    idempotency_key: IdempotencyKey,
):
    """Approve a fully resolved local package after direct confirmation; it never submits it."""
    if not confirmed_by_user:
        raise ValueError("Application approval requires direct user confirmation")
    return approve_prepared_application(application_id, idempotency_key, "local_user").model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
