from datetime import date
from app.models.schemas import CandidateProfile, CompensationEstimate, JobListing
from app.services.openai_service import OpenAIService

SYSTEM = """You are a compensation analyst. Estimate a defensible compensation range using candidate scope,
role family, geography, seniority, industry, and any salary evidence from the provided job set.
Do not imply certainty. Explain assumptions and lower confidence when evidence is thin."""


class CompensationAgent:
    def __init__(self, ai: OpenAIService | None = None) -> None:
        self.ai = ai or OpenAIService()

    async def run(self, profile: CandidateProfile, role_family: str, geography: str, jobs: list[JobListing]) -> CompensationEstimate:
        prompt = f"""AS OF: {date.today().isoformat()}
ROLE FAMILY: {role_family}
GEOGRAPHY: {geography}
PROFILE: {profile.model_dump_json()}
COMPARABLE JOBS: {[j.model_dump() for j in jobs[:25]]}
Return USD annual compensation unless evidence requires otherwise."""
        return await self.ai.structured(system=SYSTEM, user=prompt, schema=CompensationEstimate)
