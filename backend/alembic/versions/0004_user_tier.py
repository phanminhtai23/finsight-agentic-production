"""user tier

Revision ID: 0004_user_tier
Revises: 0003_topics
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_user_tier"
down_revision: str | None = "0003_topics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("tier", sa.String(), nullable=False, server_default="free"))


def downgrade() -> None:
    op.drop_column("users", "tier")
