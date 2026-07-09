"""Add repository lookup and payload columns.

Revision ID: 20260709_0002
Revises: 20260709_0001
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260709_0002"
down_revision: str | None = "20260709_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidate_profiles", sa.Column("external_id", sa.Text(), nullable=True))
    op.create_unique_constraint(
        "uq_candidate_profiles_external_id",
        "candidate_profiles",
        ["external_id"],
    )
    op.add_column("jobs", sa.Column("listing", postgresql.JSONB(), nullable=True))
    op.add_column("job_matches", sa.Column("match", postgresql.JSONB(), nullable=True))
    op.add_column("applications", sa.Column("application_key", sa.Text(), nullable=True))
    op.create_unique_constraint(
        "uq_applications_application_key",
        "applications",
        ["application_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_applications_application_key", "applications", type_="unique")
    op.drop_column("applications", "application_key")
    op.drop_column("job_matches", "match")
    op.drop_column("jobs", "listing")
    op.drop_constraint("uq_candidate_profiles_external_id", "candidate_profiles", type_="unique")
    op.drop_column("candidate_profiles", "external_id")
