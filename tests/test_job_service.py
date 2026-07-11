import httpx

from app.models.schemas import JobSearchFilters
from app.services.job_service import JobService


class FakeConnector:
    def __init__(self, jobs=None, error: Exception | None = None) -> None:
        self.jobs = jobs or []
        self.error = error
        self.calls = 0

    async def fetch_board(self, board_token: str):
        self.calls += 1
        if self.error:
            raise self.error
        return self.jobs

    async def fetch_company(self, company: str):
        self.calls += 1
        if self.error:
            raise self.error
        return self.jobs

    async def fetch_job_board(self, job_board: str):
        self.calls += 1
        if self.error:
            raise self.error
        return self.jobs


class FlakyConnector:
    def __init__(self, jobs) -> None:
        self.jobs = jobs
        self.calls = 0

    async def fetch_board(self, board_token: str):
        self.calls += 1
        if self.calls == 1:
            raise httpx.ConnectTimeout("temporary timeout")
        return self.jobs


async def test_job_service_deduplicates_by_source_url(sample_job):
    duplicate = sample_job.model_copy(update={"job_id": "greenhouse:example:duplicate"})
    service = JobService()
    service.greenhouse = FakeConnector([sample_job])
    service.lever = FakeConnector([duplicate])

    result = await service.search_known_boards(["example"], ["example"])

    assert result.jobs == [sample_job]
    assert result.provider_errors == []


async def test_job_service_continues_when_connector_fails(sample_job):
    service = JobService()
    service.greenhouse = FakeConnector(error=RuntimeError("provider unavailable"))
    service.lever = FakeConnector([sample_job])

    result = await service.search_known_boards(["broken"], ["example"])

    assert result.jobs == [sample_job]
    assert [error.provider for error in result.provider_errors] == ["greenhouse"]


async def test_job_service_retries_read_only_connector_timeouts(sample_job, monkeypatch):
    monkeypatch.setattr("app.services.job_service.settings.connector_max_attempts", 2)
    service = JobService()
    service.greenhouse = FlakyConnector([sample_job])
    service.lever = FakeConnector([])

    result = await service.search_known_boards(["example"], [])

    assert result.jobs == [sample_job]
    assert service.greenhouse.calls == 2


async def test_job_service_includes_ashby_and_isolates_its_failures(sample_job):
    service = JobService()
    service.greenhouse = FakeConnector([])
    service.lever = FakeConnector([])
    service.ashby = FakeConnector(error=ValueError("malformed provider payload"))

    result = await service.search_known_boards([], [], ["example"])

    assert result.jobs == []
    assert [error.provider for error in result.provider_errors] == ["ashby"]


async def test_job_service_excludes_jobs_missing_filtered_provider_data(sample_job):
    service = JobService()
    service.greenhouse = FakeConnector([sample_job.model_copy(update={"location": None, "remote_type": None,
                                                                       "salary_max": None, "employment_type": None,
                                                                       "posted_at": None})])
    service.lever = FakeConnector([])

    filters = [
        JobSearchFilters(location_keywords=["remote"]),
        JobSearchFilters(remote_mode="remote"),
        JobSearchFilters(minimum_salary=100_000, compensation_currency="USD"),
        JobSearchFilters(employment_types=["full-time"]),
        JobSearchFilters(freshness_days=7),
    ]
    for job_filters in filters:
        result = await service.search_known_boards(["example"], [], filters=job_filters)
        assert result.jobs == []
