import sqlalchemy as sa

from app.repositories import create_repository_store, metadata


def test_repository_store_persists_core_entities(
    sample_application,
    sample_job,
    sample_match,
    sample_profile,
) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)

    store.profiles[sample_profile.candidate_id] = sample_profile
    store.jobs[sample_job.job_id] = sample_job
    store.matches[(sample_profile.candidate_id, sample_job.job_id)] = sample_match
    store.applications[sample_application.application_id] = sample_application

    reloaded_store = create_repository_store(engine)

    assert reloaded_store.profiles[sample_profile.candidate_id] == sample_profile
    assert reloaded_store.jobs[sample_job.job_id] == sample_job
    assert reloaded_store.matches[(sample_profile.candidate_id, sample_job.job_id)] == sample_match
    assert reloaded_store.applications[sample_application.application_id] == sample_application


def test_repository_store_updates_application_status(sample_application, sample_profile) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)
    store.profiles[sample_profile.candidate_id] = sample_profile
    store.applications[sample_application.application_id] = sample_application

    package = store.applications[sample_application.application_id]
    package.status = "approved"
    store.applications[sample_application.application_id] = package

    reloaded_store = create_repository_store(engine)

    assert reloaded_store.applications[sample_application.application_id].status == "approved"
