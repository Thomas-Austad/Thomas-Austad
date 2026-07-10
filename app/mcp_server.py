"""Minimal MCP tool surface for ChatGPT. Run separately from FastAPI during development."""
import uuid

from mcp.server.fastmcp import FastMCP
from app.main import (
    apply_profile_corrections,
    create_profile,
    estimate_compensation,
    get_profile_review,
    prepare_application,
    score_match,
    search_jobs,
)
from app.main import ProfileRequest, JobSearchRequest, ApplicationRequest
from app.models.schemas import ProfileCorrectionRequest

mcp = FastMCP("Talent Advisor")


@mcp.tool()
async def create_candidate_profile(candidate_id: str, resume_text: str, linkedin_text: str = "", preferences: dict | None = None):
    """Create an evidence-grounded candidate profile from resume and LinkedIn text."""
    return (await create_profile(ProfileRequest(candidate_id=candidate_id, resume_text=resume_text,
                                                linkedin_text=linkedin_text, preferences=preferences or {}))).model_dump()


@mcp.tool()
async def review_candidate_profile(candidate_id: str):
    """Read a profile with its source evidence and prior user-provided corrections."""
    return get_profile_review(candidate_id).model_dump(mode="json")


@mcp.tool()
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


@mcp.tool()
async def find_jobs(greenhouse_boards: list[str], lever_companies: list[str], title_keywords: list[str] | None = None):
    """Retrieve active jobs from supported ATS boards."""
    return await search_jobs(JobSearchRequest(greenhouse_boards=greenhouse_boards,
                                              lever_companies=lever_companies,
                                              title_keywords=title_keywords or []))


@mcp.tool()
async def evaluate_job_match(candidate_id: str, job_id: str):
    """Score a candidate against a job and explain gaps and disqualifiers."""
    return (await score_match(candidate_id, job_id)).model_dump()


@mcp.tool()
async def estimate_market_compensation(candidate_id: str, role_family: str, geography: str):
    """Estimate a current compensation range using profile and collected jobs."""
    return (await estimate_compensation(candidate_id, role_family, geography)).model_dump()


@mcp.tool()
async def prepare_job_application(candidate_id: str, job_id: str, screening_questions: list[str] | None = None):
    """Prepare a truthful tailored resume, cover letter, and screening answers for user review."""
    return (await prepare_application(ApplicationRequest(candidate_id=candidate_id, job_id=job_id,
                                                         screening_questions=screening_questions or []))).model_dump()


if __name__ == "__main__":
    mcp.run(transport="stdio")
