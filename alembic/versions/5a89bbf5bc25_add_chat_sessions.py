"""add chat sessions

Revision ID: 5a89bbf5bc25
Revises: 1727ee774550
Create Date: 2025-09-01 23:26:32.512556
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5a89bbf5bc25"
down_revision: Union[str, Sequence[str], None] = "1727ee774550"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create chat_sessions + chat_interactions tables."""

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("notebook_id", sa.String(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "chat_interactions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),  # user | assistant
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("notes", sa.JSON(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema: drop chat tables."""
    op.drop_table("chat_interactions")
    op.drop_table("chat_sessions")
