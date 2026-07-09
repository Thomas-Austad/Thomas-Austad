"""Add evidence claim references.

Revision ID: 20260709_0003
Revises: 20260709_0002
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260709_0003"
down_revision: str | None = "20260709_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("career_evidence", sa.Column("claim_type", sa.Text(), nullable=True))
    op.add_column("career_evidence", sa.Column("claim_ref", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("career_evidence", "claim_ref")
    op.drop_column("career_evidence", "claim_type")
