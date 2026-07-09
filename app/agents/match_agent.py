from app.models.schemas import CandidateProfile, JobListing, JobMatch
from app.services.openai_service import OpenAIService

SYSTEM = """You are a conservative recruiting and hiring-market evaluator.
Score actual evidence, not title similarity. Identify hard disqualifiers separately.
Use this weighted overall score: qualification 30%, evidence 20%, seniority 15%, compensation 15%, preferences 10%, competitiveness 10%.
Recommend apply only when the candidate can truthfully present a credible case."""


class MatchAgent:
    def __init__(self, ai: OpenAIService | None = None) -> None:
        self.ai = ai or OpenAIService()

    async def run(self, profile: CandidateProfile, job: JobListing) -> JobMatch:
        prompt = f"PROFILE:\n{profile.model_dump_json()}\n\nJOB:\n{job.model_dump_json()}"
        return await self.ai.structured(system=SYSTEM, user=prompt, schema=JobMatch)
