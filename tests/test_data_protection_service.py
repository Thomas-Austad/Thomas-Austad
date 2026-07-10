import pytest
import sqlalchemy as sa
import uuid

from app.privacy_migrate import migrate_sensitive_data
from app.repositories import candidate_profiles_table, metadata
from app.services.data_protection_service import SensitiveDataIntegrityError, protector


def test_sensitive_json_round_trip_and_tamper_detection() -> None:
    envelope = protector.encrypt_json(
        {"resume": "Synthetic private content"},
        purpose="test",
        record_id="record-123",
    )

    assert "Synthetic private content" not in str(envelope)
    assert protector.decrypt_json(envelope, purpose="test", record_id="record-123") == {
        "resume": "Synthetic private content"
    }

    envelope["ciphertext"] = "AA=="
    with pytest.raises(SensitiveDataIntegrityError):
        protector.decrypt_json(envelope, purpose="test", record_id="record-123")


def test_legacy_profile_migration_is_idempotent() -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    plaintext = {
        "candidate_id": "candidate-123",
        "headline": "Legacy private profile",
        "current_level": "Senior",
        "primary_functions": [],
        "skills": [],
        "experience": [],
    }
    with engine.begin() as connection:
        connection.execute(
            candidate_profiles_table.insert().values(
                id=uuid.UUID("00000000-0000-0000-0000-000000000123"),
                external_id="candidate-123",
                profile=plaintext,
            )
        )

    assert migrate_sensitive_data(engine, apply=False) == {"profiles": 1}
    assert migrate_sensitive_data(engine, apply=True) == {"profiles": 1}
    assert migrate_sensitive_data(engine, apply=False) == {}

    with engine.begin() as connection:
        stored = connection.scalar(sa.select(candidate_profiles_table.c.profile))
    assert "Legacy private profile" not in str(stored)
