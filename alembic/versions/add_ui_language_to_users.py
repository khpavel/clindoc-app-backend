"""add_ui_language_to_users

Revision ID: add_ui_language
Revises: e8f9a1b2c3d4
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'add_ui_language'
down_revision: Union[str, None] = 'e8f9a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if ui_language column exists in users table
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'ui_language' not in users_columns:
        # Add ui_language column to users table with default 'en'
        op.add_column(
            'users',
            sa.Column('ui_language', sa.String(length=2), nullable=False, server_default='en')
        )


def downgrade() -> None:
    # Remove ui_language column from users table
    op.drop_column('users', 'ui_language')

