"""Harden persistence constraints and lookup indexes.

Revision ID: 20260709_0004
Revises: 20260709_0003
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260709_0004"
down_revision: str | None = "20260709_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if not context.is_offline_mode():
        _assert_no_nulls("candidate_profiles", "external_id")
        _assert_no_nulls("jobs", "listing")
        _assert_no_nulls("job_matches", "match")
        _assert_no_nulls("applications", "application_key")
        _assert_no_nulls("applications", "candidate_profile_id")
        _assert_no_nulls("applications", "job_id")
        _assert_no_nulls("career_evidence", "candidate_profile_id")
        _assert_no_nulls("career_evidence", "claim_type")
        _assert_no_nulls("career_evidence", "claim_ref")

    op.alter_column("candidate_profiles", "external_id", existing_type=sa.Text(), nullable=False)
    op.alter_column("jobs", "listing", existing_type=postgresql.JSONB(), nullable=False)
    op.alter_column("job_matches", "match", existing_type=postgresql.JSONB(), nullable=False)
    op.alter_column("applications", "application_key", existing_type=sa.Text(), nullable=False)
    op.alter_column(
        "applications",
        "candidate_profile_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.alter_column("applications", "job_id", existing_type=sa.Text(), nullable=False)
    op.alter_column(
        "career_evidence",
        "candidate_profile_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.alter_column("career_evidence", "claim_type", existing_type=sa.Text(), nullable=False)
    op.alter_column("career_evidence", "claim_ref", existing_type=sa.Text(), nullable=False)

    op.create_check_constraint(
        "ck_career_evidence_confidence",
        "career_evidence",
        "confidence >= 0 AND confidence <= 1",
    )
    op.create_check_constraint(
        "ck_jobs_salary_range",
        "jobs",
        "(salary_min IS NULL OR salary_min >= 0) AND "
        "(salary_max IS NULL OR salary_max >= 0) AND "
        "(salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)",
    )
    op.create_check_constraint(
        "ck_job_matches_overall_score",
        "job_matches",
        "overall_score >= 0 AND overall_score <= 100",
    )
    op.create_check_constraint(
        "ck_job_matches_recommendation",
        "job_matches",
        "recommendation IN ('apply', 'consider', 'skip')",
    )
    op.create_check_constraint(
        "ck_applications_status",
        "applications",
        "status IN ('prepared', 'approved', 'submitted', 'failed')",
    )
    op.create_index(
        "ix_candidate_profiles_user_id",
        "candidate_profiles",
        ["user_id"],
    )
    op.create_index(
        "ix_career_evidence_candidate_profile_id",
        "career_evidence",
        ["candidate_profile_id"],
    )
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"])
    op.create_index(
        "ix_applications_candidate_profile_id",
        "applications",
        ["candidate_profile_id"],
    )
    op.create_index("ix_applications_job_id", "applications", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_applications_job_id", table_name="applications")
    op.drop_index("ix_applications_candidate_profile_id", table_name="applications")
    op.drop_index("ix_job_matches_job_id", table_name="job_matches")
    op.drop_index("ix_career_evidence_candidate_profile_id", table_name="career_evidence")
    op.drop_index("ix_candidate_profiles_user_id", table_name="candidate_profiles")
    op.drop_constraint("ck_applications_status", "applications", type_="check")
    op.drop_constraint("ck_job_matches_recommendation", "job_matches", type_="check")
    op.drop_constraint("ck_job_matches_overall_score", "job_matches", type_="check")
    op.drop_constraint("ck_jobs_salary_range", "jobs", type_="check")
    op.drop_constraint("ck_career_evidence_confidence", "career_evidence", type_="check")

    op.alter_column("career_evidence", "claim_ref", existing_type=sa.Text(), nullable=True)
    op.alter_column("career_evidence", "claim_type", existing_type=sa.Text(), nullable=True)
    op.alter_column(
        "career_evidence",
        "candidate_profile_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.alter_column("applications", "job_id", existing_type=sa.Text(), nullable=True)
    op.alter_column(
        "applications",
        "candidate_profile_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.alter_column("applications", "application_key", existing_type=sa.Text(), nullable=True)
    op.alter_column("job_matches", "match", existing_type=postgresql.JSONB(), nullable=True)
    op.alter_column("jobs", "listing", existing_type=postgresql.JSONB(), nullable=True)
    op.alter_column("candidate_profiles", "external_id", existing_type=sa.Text(), nullable=True)


def _assert_no_nulls(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    count = bind.execute(
        sa.text(f"SELECT count(*) FROM {table_name} WHERE {column_name} IS NULL")
    ).scalar_one()
    if count:
        raise RuntimeError(
            f"Cannot harden {table_name}.{column_name}: {count} existing rows contain NULL"
        )
