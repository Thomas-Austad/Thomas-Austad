import httpx
from datetime import UTC, datetime, timedelta
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.connectors.ashby import AshbyConnector
from app.connectors.greenhouse import GreenhouseConnector
from app.connectors.lever import LeverConnector
from app.models.schemas import JobListing, JobSearchFilters, JobSearchResult, ProviderSearchError
from app.observability import log_event, record_metric


class JobService:
    def __init__(self) -> None:
        self.greenhouse = GreenhouseConnector()
        self.lever = LeverConnector()
        self.ashby = AshbyConnector()

    async def search_known_boards(
        self,
        greenhouse_boards: list[str],
        lever_companies: list[str],
        ashby_job_boards: list[str] | None = None,
        filters: JobSearchFilters | None = None,
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
        for job_board in ashby_job_boards or []:
            try:
                jobs.extend(await self._fetch_with_retry("ashby", job_board, self.ashby.fetch_job_board))
            except Exception as exc:
                record_metric("connector.ashby.failure")
                log_event("connector.fetch_failed", provider="ashby", error=type(exc).__name__)
                provider_errors.append(ProviderSearchError(provider="ashby"))
                continue
        seen: set[str] = set()
        unique: list[JobListing] = []
        for job in jobs:
            key = str(job.source_url)
            if key not in seen:
                seen.add(key)
                unique.append(job)
        found = [job for job in unique if _matches_filters(job, filters or JobSearchFilters())]
        record_metric("jobs.search.completed")
        log_event("jobs.search_completed", providers=3, returned=len(found))
        unique_errors = list({error.provider: error for error in provider_errors}.values())
        return JobSearchResult(jobs=found, provider_errors=unique_errors)

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


def _matches_filters(job: JobListing, filters: JobSearchFilters) -> bool:
    if filters.title_keywords and not any(term.lower() in job.title.lower() for term in filters.title_keywords):
        return False
    if filters.company_keywords and not any(
        term.lower() in job.company.lower() for term in filters.company_keywords
    ):
        return False
    if filters.location_keywords and (
        job.location is None
        or not any(term.lower() in job.location.lower() for term in filters.location_keywords)
    ):
        return False
    if filters.remote_mode and job.remote_type != filters.remote_mode:
        return False
    if filters.minimum_salary is not None and (
        job.salary_max is None
        or job.currency != filters.compensation_currency
        or job.salary_max < filters.minimum_salary
    ):
        return False
    if filters.employment_types and (
        job.employment_type is None
        or job.employment_type.lower() not in {value.lower() for value in filters.employment_types}
    ):
        return False
    if filters.freshness_days is not None:
        posted_at = _parse_utc_timestamp(job.posted_at)
        now = datetime.now(UTC)
        if posted_at is None or posted_at > now or posted_at < now - timedelta(days=filters.freshness_days):
            return False
    return True


def _parse_utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None
