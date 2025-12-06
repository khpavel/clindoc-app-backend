"""add_unique_constraint_study_members

Revision ID: a1b2c3d4e5f6
Revises: 0f5493d5032a
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '0f5493d5032a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if unique constraint already exists
    constraints = inspector.get_unique_constraints('study_members')
    constraint_exists = any(
        constraint['name'] == 'uq_study_members_study_user' 
        for constraint in constraints
    )
    
    if not constraint_exists:
        # Add unique constraint on (study_id, user_id)
        op.create_unique_constraint(
            'uq_study_members_study_user',
            'study_members',
            ['study_id', 'user_id']
        )


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint('uq_study_members_study_user', 'study_members', type_='unique')

