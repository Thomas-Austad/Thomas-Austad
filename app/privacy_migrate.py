"""Explicit, resumable conversion of legacy sensitive database payloads."""

from __future__ import annotations

import argparse
from collections import Counter

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from app.db import get_engine
from app.repositories import (
    _encrypt_payload,
    _encrypt_text,
    _is_encrypted,
    applications_table,
    candidate_profiles_table,
    career_evidence_table,
    job_matches_table,
    profile_corrections_table,
)


def migrate_sensitive_data(engine: Engine, *, apply: bool) -> dict[str, int]:
    """Encrypt legacy rows. Re-running skips already encrypted values safely."""
    changed: Counter[str] = Counter()
    with engine.begin() as connection:
        for row in connection.execute(
            sa.select(candidate_profiles_table.c.id, candidate_profiles_table.c.external_id, candidate_profiles_table.c.profile)
        ):
            if not _is_encrypted(row.profile):
                changed["profiles"] += 1
                if apply:
                    connection.execute(
                        candidate_profiles_table.update()
                        .where(candidate_profiles_table.c.id == row.id)
                        .values(profile=_encrypt_payload(row.profile, "profile", row.external_id))
                    )
        for row in connection.execute(
            sa.select(
                career_evidence_table.c.id,
                career_evidence_table.c.source_ref,
                career_evidence_table.c.excerpt,
                career_evidence_table.c.claim_ref,
            )
        ):
            values = {}
            if row.source_ref is not None and not _is_encrypted_text(row.source_ref):
                values["source_ref"] = _encrypt_text(row.source_ref, "evidence", str(row.id))
            if not _is_encrypted_text(row.excerpt):
                values["excerpt"] = _encrypt_text(row.excerpt, "evidence", str(row.id))
            if not _is_encrypted_text(row.claim_ref):
                values["claim_ref"] = _encrypt_text(row.claim_ref, "evidence", str(row.id))
            if values:
                changed["evidence_fields"] += len(values)
                if apply:
                    connection.execute(career_evidence_table.update().where(career_evidence_table.c.id == row.id).values(**values))
        for row in connection.execute(sa.select(profile_corrections_table.c.id, profile_corrections_table.c.value)):
            if not _is_encrypted(row.value):
                changed["corrections"] += 1
                if apply:
                    connection.execute(profile_corrections_table.update().where(profile_corrections_table.c.id == row.id).values(value=_encrypt_payload({"value": row.value}, "profile_correction", str(row.id))))
        for row in connection.execute(sa.select(applications_table.c.id, applications_table.c.application_key, applications_table.c.package)):
            if not _is_encrypted(row.package):
                changed["applications"] += 1
                if apply:
                    connection.execute(applications_table.update().where(applications_table.c.id == row.id).values(package=_encrypt_payload(row.package, "application", row.application_key)))
        for row in connection.execute(
            sa.select(
                candidate_profiles_table.c.external_id,
                job_matches_table.c.candidate_profile_id,
                job_matches_table.c.job_id,
                job_matches_table.c.scores,
                job_matches_table.c.match,
            ).join(
                candidate_profiles_table,
                candidate_profiles_table.c.id == job_matches_table.c.candidate_profile_id,
            )
        ):
            values = {}
            base = f"{row.external_id}:{row.job_id}"
            if not _is_encrypted(row.scores):
                values["scores"] = _encrypt_payload(row.scores, "match", f"{base}:scores")
            if not _is_encrypted(row.match):
                values["match"] = _encrypt_payload(row.match, "match", f"{base}:match")
            if values:
                changed["match_payloads"] += len(values)
                if apply:
                    connection.execute(
                        job_matches_table.update()
                        .where(
                            job_matches_table.c.job_id == row.job_id,
                            job_matches_table.c.candidate_profile_id == row.candidate_profile_id,
                        )
                        .values(**values)
                    )
    return dict(changed)


def _is_encrypted_text(value: str) -> bool:
    import json

    try:
        return _is_encrypted(json.loads(value))
    except json.JSONDecodeError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Encrypt legacy sensitive Talent Advisor records")
    parser.add_argument("--apply", action="store_true", help="perform conversion; default is a dry run")
    args = parser.parse_args()
    result = migrate_sensitive_data(get_engine(), apply=args.apply)
    print(result)


if __name__ == "__main__":
    main()
