from app.connectors.greenhouse import GreenhouseConnector
from app.connectors.lever import LeverConnector
from app.models.schemas import JobListing


class JobService:
    def __init__(self) -> None:
        self.greenhouse = GreenhouseConnector()
        self.lever = LeverConnector()

    async def search_known_boards(self, greenhouse_boards: list[str], lever_companies: list[str]) -> list[JobListing]:
        jobs: list[JobListing] = []
        for board in greenhouse_boards:
            try:
                jobs.extend(await self.greenhouse.fetch_board(board))
            except Exception:
                continue
        for company in lever_companies:
            try:
                jobs.extend(await self.lever.fetch_company(company))
            except Exception:
                continue
        seen: set[str] = set()
        unique: list[JobListing] = []
        for job in jobs:
            key = str(job.source_url)
            if key not in seen:
                seen.add(key)
                unique.append(job)
        return unique
