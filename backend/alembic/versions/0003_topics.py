"""topics + topic/source columns

Revision ID: 0003_topics
Revises: 0002_users
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_topics"
down_revision: str | None = "0002_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("qdrant_collection", sa.String(), nullable=False, unique=True),
    )
    op.create_index("ix_topics_user_id", "topics", ["user_id"])

    op.add_column(
        "documents",
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_documents_topic_id", "documents", ["topic_id"])
    op.add_column(
        "documents",
        sa.Column("source_type", sa.String(), nullable=False, server_default="file"),
    )
    op.add_column("documents", sa.Column("source_url", sa.String(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
    )

    op.add_column(
        "conversations",
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_conversations_topic_id", "conversations", ["topic_id"])


def downgrade() -> None:
    op.drop_index("ix_conversations_topic_id", "conversations")
    op.drop_column("conversations", "topic_id")
    op.drop_column("documents", "size_bytes")
    op.drop_column("documents", "source_url")
    op.drop_column("documents", "source_type")
    op.drop_index("ix_documents_topic_id", "documents")
    op.drop_column("documents", "topic_id")
    op.drop_table("topics")
