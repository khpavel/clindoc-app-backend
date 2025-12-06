"""add_study_members_and_owner_id

Revision ID: b6f382ad0f4f
Revises: 4fd91a5a7c9c
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'b6f382ad0f4f'
down_revision: Union[str, None] = '4fd91a5a7c9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if owner_id column exists in studies table
    studies_columns = [col['name'] for col in inspector.get_columns('studies')]
    
    if 'owner_id' not in studies_columns:
        # Add owner_id column to studies table (nullable initially for data migration)
        op.add_column(
            'studies',
            sa.Column('owner_id', sa.Integer(), nullable=True)
        )
    
    # Check for existing foreign key constraint
    fk_constraints = inspector.get_foreign_keys('studies')
    fk_exists = any(fk['name'] == 'fk_studies_owner_id' for fk in fk_constraints)
    
    if not fk_exists:
        # Add foreign key constraint for owner_id
        op.create_foreign_key(
            'fk_studies_owner_id',
            'studies',
            'users',
            ['owner_id'],
            ['id']
        )
    
    # Check for existing index
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('studies')]
    if 'ix_studies_owner_id' not in existing_indexes:
        # Create index for owner_id
        op.create_index('ix_studies_owner_id', 'studies', ['owner_id'])
    
    # Create study_members table (only if it doesn't exist)
    tables = inspector.get_table_names()
    
    if 'study_members' not in tables:
        op.create_table(
            'study_members',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('study_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        # Create indexes for study_members
        op.create_index('ix_study_members_id', 'study_members', ['id'])
        op.create_index('ix_study_members_user_id', 'study_members', ['user_id'])
        op.create_index('ix_study_members_study_id', 'study_members', ['study_id'])
    else:
        # Table already exists, just ensure indexes exist
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('study_members')]
        if 'ix_study_members_id' not in existing_indexes:
            op.create_index('ix_study_members_id', 'study_members', ['id'])
        if 'ix_study_members_user_id' not in existing_indexes:
            op.create_index('ix_study_members_user_id', 'study_members', ['user_id'])
        if 'ix_study_members_study_id' not in existing_indexes:
            op.create_index('ix_study_members_study_id', 'study_members', ['study_id'])


def downgrade() -> None:
    # Drop study_members table
    op.drop_index('ix_study_members_study_id', table_name='study_members')
    op.drop_index('ix_study_members_user_id', table_name='study_members')
    op.drop_index('ix_study_members_id', table_name='study_members')
    op.drop_table('study_members')
    
    # Remove owner_id from studies table
    op.drop_index('ix_studies_owner_id', table_name='studies')
    op.drop_constraint('fk_studies_owner_id', 'studies', type_='foreignkey')
    op.drop_column('studies', 'owner_id')

