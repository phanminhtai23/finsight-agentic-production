"""message charts

Revision ID: 0005_message_charts
Revises: 0004_user_tier
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_message_charts"
down_revision: str | None = "0004_user_tier"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("charts", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "charts")
