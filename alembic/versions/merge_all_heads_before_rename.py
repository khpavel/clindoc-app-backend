"""merge all heads before rename

Revision ID: merge_all_heads
Revises: ('0f5493d5032a', 'xyz789ghi012')
Create Date: 2025-01-16 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_all_heads'
down_revision: Union[str, tuple[str, ...], None] = ('0f5493d5032a', 'xyz789ghi012')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a merge migration - no changes needed, just merges the branches
    pass


def downgrade() -> None:
    # This is a merge migration - no changes needed
    pass

