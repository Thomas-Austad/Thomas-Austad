import uuid
from pydantic import BaseModel
from app.models.schemas import ApplicationPackage, CandidateProfile, JobListing
from app.services.openai_service import OpenAIService


class DraftPackage(BaseModel):
    tailored_resume_markdown: str
    cover_letter: str
    screening_answers: dict[str, str]
    factual_warnings: list[str]
    requires_user_input: list[str]


SYSTEM = """You prepare truthful job applications. Tailor emphasis and language, never facts.
Do not add skills, credentials, titles, dates, metrics, clearances, work authorization, or experience not supported by the candidate profile.
Flag any question requiring personal, legal, demographic, disability, criminal-history, salary-history, or work-authorization confirmation.
Create an ATS-friendly resume and a specific concise cover letter."""


class ApplicationAgent:
    def __init__(self, ai: OpenAIService | None = None) -> None:
        self.ai = ai or OpenAIService()

    async def prepare(self, profile: CandidateProfile, job: JobListing, screening_questions: list[str]) -> ApplicationPackage:
        prompt = f"PROFILE:\n{profile.model_dump_json()}\n\nJOB:\n{job.model_dump_json()}\n\nQUESTIONS:\n{screening_questions}"
        draft = await self.ai.structured(system=SYSTEM, user=prompt, schema=DraftPackage)
        return ApplicationPackage(
            application_id=str(uuid.uuid4()), candidate_id=profile.candidate_id, job_id=job.job_id,
            **draft.model_dump()
        )
