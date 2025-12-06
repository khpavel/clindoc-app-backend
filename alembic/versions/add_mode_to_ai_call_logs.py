"""add_mode_to_ai_call_logs

Revision ID: add_mode_ai_logs
Revises: fbdd055efa7e
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'add_mode_ai_logs'
down_revision: Union[str, None] = 'fbdd055efa7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check existing columns
    columns = [col['name'] for col in inspector.get_columns('ai_call_logs')]
    
    # Add mode column
    if 'mode' not in columns:
        op.add_column(
            'ai_call_logs',
            sa.Column('mode', sa.String(length=20), nullable=True)
        )


def downgrade() -> None:
    # Drop mode column
    op.drop_column('ai_call_logs', 'mode')

