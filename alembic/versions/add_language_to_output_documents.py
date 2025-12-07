"""add_language_to_output_documents

Revision ID: add_language_output_docs
Revises: 2d798620454d
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'add_language_output_docs'
down_revision: Union[str, None] = '2d798620454d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check existing columns
    columns = [col['name'] for col in inspector.get_columns('output_documents')]
    
    # Add language column if it doesn't exist
    if 'language' not in columns:
        op.add_column(
            'output_documents',
            sa.Column('language', sa.String(length=2), nullable=False, server_default='ru')
        )
        
        # Add check constraint for language values
        constraints = [c['name'] for c in inspector.get_check_constraints('output_documents')]
        if 'ck_output_document_language' not in constraints:
            op.create_check_constraint(
                'ck_output_document_language',
                'output_documents',
                "language IN ('ru', 'en')"
            )


def downgrade() -> None:
    # Drop check constraint
    bind = op.get_bind()
    inspector = inspect(bind)
    constraints = [c['name'] for c in inspector.get_check_constraints('output_documents')]
    
    if 'ck_output_document_language' in constraints:
        op.drop_constraint('ck_output_document_language', 'output_documents', type_='check')
    
    # Drop language column
    columns = [col['name'] for col in inspector.get_columns('output_documents')]
    if 'language' in columns:
        op.drop_column('output_documents', 'language')

