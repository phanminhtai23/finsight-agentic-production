"""message tools

Revision ID: 0006_message_tools
Revises: 0005_message_charts
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_message_tools"
down_revision: str | None = "0005_message_charts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("tools", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "tools")
