"""add quoted_note_id to chat_interactions

Revision ID: 37f832a13271
Revises: 5a89bbf5bc25
Create Date: 2025-09-02 20:25:06.376508
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "37f832a13271"
down_revision: Union[str, Sequence[str], None] = "5a89bbf5bc25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("chat_interactions") as batch_op:
        batch_op.add_column(sa.Column("quoted_note_id", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("chat_interactions") as batch_op:
        batch_op.drop_column("quoted_note_id")
