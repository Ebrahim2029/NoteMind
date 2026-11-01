"""add performance indexes

Revision ID: 9133eaca5a5e
Revises: 71c00196e276
Create Date: 2025-08-16 13:07:39.703619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9133eaca5a5e'
down_revision: Union[str, Sequence[str], None] = '71c00196e276'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
