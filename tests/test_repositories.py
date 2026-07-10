import pytest
import sqlalchemy as sa

from app.models.schemas import Evidence, EvidenceRecord, Skill, WorkExperience
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


def test_repository_store_updates_application_status(
    sample_application,
    sample_job,
    sample_profile,
) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)
    store.profiles[sample_profile.candidate_id] = sample_profile
    store.jobs[sample_job.job_id] = sample_job
    store.applications[sample_application.application_id] = sample_application

    package = store.applications[sample_application.application_id]
    package.status = "approved"
    store.applications[sample_application.application_id] = package

    reloaded_store = create_repository_store(engine)

    assert reloaded_store.applications[sample_application.application_id].status == "approved"


def test_repository_store_persists_profile_evidence(sample_profile) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)
    profile = sample_profile.model_copy(
        update={
            "skills": [
                Skill(
                    name="Python",
                    proficiency=0.9,
                    years=6,
                    evidence=[
                        Evidence(
                            source="resume",
                            text="Built Python APIs for internal platforms.",
                            confidence=0.92,
                        ),
                        Evidence(
                            source="linkedin",
                            text="Listed Python platform engineering experience.",
                            confidence=0.45,
                        ),
                    ],
                )
            ],
            "experience": [
                WorkExperience(
                    employer="Example Co",
                    title="Backend Engineer",
                    evidence=[
                        Evidence(
                            source="resume",
                            text="Backend Engineer at Example Co.",
                            confidence=0.85,
                        )
                    ],
                )
            ],
            "ambiguities": ["Exact team scope is unclear."],
        }
    )

    store.profiles[profile.candidate_id] = profile

    evidence = store.evidence.for_candidate(profile.candidate_id)

    assert [record.claim_type for record in evidence] == [
        "ambiguity",
        "experience",
        "skill",
        "skill",
    ]
    assert [record.claim_ref for record in evidence] == [
        "Exact team scope is unclear.",
        "Example Co: Backend Engineer",
        "Python",
        "Python",
    ]
    assert evidence[0].text == "Exact team scope is unclear."
    assert evidence[0].confidence == 0
    assert evidence[1].text == "Backend Engineer at Example Co."
    assert evidence[2].confidence == 0.92
    assert evidence[3].confidence == 0.45


def test_repository_store_replaces_stale_profile_evidence(sample_profile) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)
    first_profile = sample_profile.model_copy(
        update={
            "skills": [
                Skill(
                    name="Python",
                    proficiency=0.9,
                    evidence=[
                        Evidence(source="resume", text="Old Python evidence.", confidence=0.8),
                    ],
                )
            ]
        }
    )
    updated_profile = sample_profile.model_copy(
        update={
            "skills": [
                Skill(
                    name="FastAPI",
                    proficiency=0.8,
                    evidence=[
                        Evidence(source="resume", text="New FastAPI evidence.", confidence=0.7),
                    ],
                )
            ]
        }
    )

    store.profiles[sample_profile.candidate_id] = first_profile
    store.profiles[sample_profile.candidate_id] = updated_profile

    evidence = store.evidence.for_candidate(sample_profile.candidate_id)

    assert len(evidence) == 1
    assert evidence[0].claim_ref == "FastAPI"
    assert evidence[0].text == "New FastAPI evidence."


def test_application_repository_rejects_missing_candidate(sample_application, sample_job) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)
    store.jobs[sample_job.job_id] = sample_job

    with pytest.raises(KeyError, match="Candidate profile not found"):
        store.applications[sample_application.application_id] = sample_application


def test_application_repository_rejects_missing_job(sample_application, sample_profile) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)
    store.profiles[sample_profile.candidate_id] = sample_profile

    with pytest.raises(KeyError, match="Job not found"):
        store.applications[sample_application.application_id] = sample_application


def test_application_status_constraint_rejects_invalid_status(
    sample_application,
    sample_job,
    sample_profile,
) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)
    store.profiles[sample_profile.candidate_id] = sample_profile
    store.jobs[sample_job.job_id] = sample_job
    sample_application.status = "started"

    with pytest.raises(sa.exc.IntegrityError):
        store.applications[sample_application.application_id] = sample_application


def test_profile_evidence_replacement_rolls_back_on_constraint_failure(
    monkeypatch,
    sample_profile,
) -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    store = create_repository_store(engine)
    initial_profile = sample_profile.model_copy(
        update={
            "headline": "Initial headline",
            "skills": [
                Skill(
                    name="Python",
                    proficiency=0.9,
                    evidence=[Evidence(source="resume", text="Stable evidence.", confidence=0.8)],
                )
            ],
        }
    )
    updated_profile = initial_profile.model_copy(update={"headline": "Updated headline"})
    store.profiles[sample_profile.candidate_id] = initial_profile

    def invalid_records(profile):
        return [
            EvidenceRecord.model_construct(
                candidate_id=profile.candidate_id,
                claim_type="skill",
                claim_ref="Python",
                source="resume",
                text="Invalid confidence.",
                confidence=2,
            )
        ]

    monkeypatch.setattr("app.repositories._profile_evidence_records", invalid_records)

    with pytest.raises(sa.exc.IntegrityError):
        store.profiles[sample_profile.candidate_id] = updated_profile

    assert store.profiles[sample_profile.candidate_id].headline == "Initial headline"
    evidence = store.evidence.for_candidate(sample_profile.candidate_id)
    assert len(evidence) == 1
    assert evidence[0].text == "Stable evidence."
