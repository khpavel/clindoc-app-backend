"""add_language_to_documents

Revision ID: 2d798620454d
Revises: add_ui_language
Create Date: 2025-12-07 03:17:08.323660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '2d798620454d'
down_revision: Union[str, None] = 'add_ui_language'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check existing columns
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    # Add language column if it doesn't exist
    if 'language' not in columns:
        op.add_column(
            'documents',
            sa.Column('language', sa.String(length=2), nullable=False, server_default='ru')
        )
        
        # Add check constraint for language values
        constraints = [c['name'] for c in inspector.get_check_constraints('documents')]
        if 'ck_document_language' not in constraints:
            op.create_check_constraint(
                'ck_document_language',
                'documents',
                "language IN ('ru', 'en')"
            )


def downgrade() -> None:
    # Drop check constraint
    bind = op.get_bind()
    inspector = inspect(bind)
    constraints = [c['name'] for c in inspector.get_check_constraints('documents')]
    
    if 'ck_document_language' in constraints:
        op.drop_constraint('ck_document_language', 'documents', type_='check')
    
    # Drop language column
    columns = [col['name'] for col in inspector.get_columns('documents')]
    if 'language' in columns:
        op.drop_column('documents', 'language')

