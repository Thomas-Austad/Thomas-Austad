"""Initial application schema.

Revision ID: 20260709_0001
Revises:
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260709_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.Text(), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("profile", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "career_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id"),
        ),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text()),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(), nullable=False),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), unique=True, nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("location", sa.Text()),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("salary_min", sa.Integer()),
        sa.Column("salary_max", sa.Integer()),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("raw", postgresql.JSONB()),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "job_matches",
        sa.Column(
            "candidate_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id"),
            primary_key=True,
        ),
        sa.Column("job_id", sa.Text(), sa.ForeignKey("jobs.id"), primary_key=True),
        sa.Column("scores", postgresql.JSONB(), nullable=False),
        sa.Column("overall_score", sa.Numeric(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id"),
        ),
        sa.Column("job_id", sa.Text(), sa.ForeignKey("jobs.id")),
        sa.Column("package", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id")),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB()),
    )


def downgrade() -> None:
    op.drop_table("consent_records")
    op.drop_table("applications")
    op.drop_table("job_matches")
    op.drop_table("jobs")
    op.drop_table("career_evidence")
    op.drop_table("candidate_profiles")
    op.drop_table("users")
