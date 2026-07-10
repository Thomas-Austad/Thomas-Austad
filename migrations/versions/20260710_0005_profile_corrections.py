"""Persist immutable candidate-profile correction records.

Revision ID: 20260710_0005
Revises: 20260709_0004
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0005"
down_revision: str | None = "20260709_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profile_corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_profile_corrections_candidate_profile_id",
        "profile_corrections",
        ["candidate_profile_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_profile_corrections_candidate_profile_id", table_name="profile_corrections")
    op.drop_table("profile_corrections")
