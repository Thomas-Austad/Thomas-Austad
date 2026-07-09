import httpx

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

    jobs = await service.search_known_boards(["example"], ["example"])

    assert jobs == [sample_job]


async def test_job_service_continues_when_connector_fails(sample_job):
    service = JobService()
    service.greenhouse = FakeConnector(error=RuntimeError("provider unavailable"))
    service.lever = FakeConnector([sample_job])

    jobs = await service.search_known_boards(["broken"], ["example"])

    assert jobs == [sample_job]


async def test_job_service_retries_read_only_connector_timeouts(sample_job, monkeypatch):
    monkeypatch.setattr("app.services.job_service.settings.connector_max_attempts", 2)
    service = JobService()
    service.greenhouse = FlakyConnector([sample_job])
    service.lever = FakeConnector([])

    jobs = await service.search_known_boards(["example"], [])

    assert jobs == [sample_job]
    assert service.greenhouse.calls == 2
