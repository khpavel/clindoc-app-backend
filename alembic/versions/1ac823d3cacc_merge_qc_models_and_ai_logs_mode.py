"""merge_qc_models_and_ai_logs_mode

Revision ID: 1ac823d3cacc
Revises: add_mode_ai_logs, f7d17a798792
Create Date: 2025-12-06 22:39:52.018130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ac823d3cacc'
down_revision: Union[str, None] = ('add_mode_ai_logs', 'f7d17a798792')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

