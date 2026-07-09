from app.models.schemas import CandidateProfile
from app.services.openai_service import OpenAIService

SYSTEM = """You are a senior talent intelligence analyst. Build an evidence-grounded candidate profile.
Never invent qualifications, dates, metrics, credentials, seniority, or scope. Mark ambiguity explicitly.
Use only the supplied resume, LinkedIn text, and user preferences. Return the requested schema."""


class CandidateProfileAgent:
    def __init__(self, ai: OpenAIService | None = None) -> None:
        self.ai = ai or OpenAIService()

    async def run(self, candidate_id: str, resume_text: str, linkedin_text: str, preferences: dict) -> CandidateProfile:
        prompt = f"""Candidate ID: {candidate_id}

RESUME:\n{resume_text}

LINKEDIN:\n{linkedin_text}

PREFERENCES:\n{preferences}

Create a concise, market-ready profile. Every skill must include evidence."""
        return await self.ai.structured(system=SYSTEM, user=prompt, schema=CandidateProfile)
