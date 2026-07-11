import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.connectors.greenhouse import GreenhouseConnector
from app.connectors.lever import LeverConnector
from app.models.schemas import JobListing, JobSearchResult, ProviderSearchError
from app.observability import log_event, record_metric


class JobService:
    def __init__(self) -> None:
        self.greenhouse = GreenhouseConnector()
        self.lever = LeverConnector()

    async def search_known_boards(
        self, greenhouse_boards: list[str], lever_companies: list[str]
    ) -> JobSearchResult:
        jobs: list[JobListing] = []
        provider_errors: list[ProviderSearchError] = []
        for board in greenhouse_boards:
            try:
                jobs.extend(await self._fetch_with_retry("greenhouse", board, self.greenhouse.fetch_board))
            except Exception as exc:
                record_metric("connector.greenhouse.failure")
                log_event("connector.fetch_failed", provider="greenhouse", error=type(exc).__name__)
                provider_errors.append(ProviderSearchError(provider="greenhouse"))
                continue
        for company in lever_companies:
            try:
                jobs.extend(await self._fetch_with_retry("lever", company, self.lever.fetch_company))
            except Exception as exc:
                record_metric("connector.lever.failure")
                log_event("connector.fetch_failed", provider="lever", error=type(exc).__name__)
                provider_errors.append(ProviderSearchError(provider="lever"))
                continue
        seen: set[str] = set()
        unique: list[JobListing] = []
        for job in jobs:
            key = str(job.source_url)
            if key not in seen:
                seen.add(key)
                unique.append(job)
        record_metric("jobs.search.completed")
        log_event("jobs.search_completed", providers=2, returned=len(unique))
        unique_errors = list({error.provider: error for error in provider_errors}.values())
        return JobSearchResult(jobs=unique, provider_errors=unique_errors)

    async def _fetch_with_retry(self, provider: str, target: str, fetch):
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(settings.connector_max_attempts),
            wait=wait_exponential(multiplier=0.2, max=2),
            retry=retry_if_exception_type((httpx.HTTPError, TimeoutError)),
            reraise=True,
        ):
            with attempt:
                result = await fetch(target)
                record_metric(f"connector.{provider}.success")
                return result
        return []
