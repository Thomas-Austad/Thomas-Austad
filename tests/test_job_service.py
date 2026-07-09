from app.services.job_service import JobService


class FakeConnector:
    def __init__(self, jobs=None, error: Exception | None = None) -> None:
        self.jobs = jobs or []
        self.error = error

    async def fetch_board(self, board_token: str):
        if self.error:
            raise self.error
        return self.jobs

    async def fetch_company(self, company: str):
        if self.error:
            raise self.error
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
