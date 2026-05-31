"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # create_type=False: we create the types explicitly below; create_table must not re-emit them.
    document_status = postgresql.ENUM(
        "processing", "ready", "failed", name="document_status", create_type=False
    )
    task_type = postgresql.ENUM("ingestion", "research", name="task_type", create_type=False)
    task_status = postgresql.ENUM(
        "queued", "running", "succeeded", "failed", name="task_status", create_type=False
    )
    bind = op.get_bind()
    document_status.create(bind, checkfirst=True)
    task_type.create(bind, checkfirst=True)
    task_status.create(bind, checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("fiscal_period", sa.String(), nullable=True),
        sa.Column("cloudinary_public_id", sa.String(), nullable=True),
        sa.Column("cloudinary_url", sa.String(), nullable=True),
        sa.Column("status", document_status, nullable=False, server_default="processing"),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])
    op.create_index("ix_documents_company", "documents", ["company"])

    # NOTE: chunks + embeddings are stored in Qdrant, not Postgres.

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("citations", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("type", task_type, nullable=False),
        sa.Column("status", task_status, nullable=False, server_default="queued"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input", postgresql.JSONB(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
    )
    op.create_index("ix_tasks_conversation_id", "tasks", ["conversation_id"])


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("documents")
    for enum_name in ("task_status", "task_type", "document_status"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
