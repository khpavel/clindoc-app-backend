"""add_fields_to_source_document

Revision ID: fbdd055efa7e
Revises: a1b2c3d4e5f6
Create Date: 2025-12-06 19:08:01.590321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'fbdd055efa7e'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check existing columns
    columns = [col['name'] for col in inspector.get_columns('source_documents')]
    
    # Add language column
    if 'language' not in columns:
        op.add_column(
            'source_documents',
            sa.Column('language', sa.String(length=2), nullable=False, server_default='ru')
        )
    
    # Add version_label column
    if 'version_label' not in columns:
        op.add_column(
            'source_documents',
            sa.Column('version_label', sa.String(length=100), nullable=True)
        )
    
    # Add status column
    if 'status' not in columns:
        op.add_column(
            'source_documents',
            sa.Column('status', sa.String(length=20), nullable=False, server_default='active')
        )
    
    # Add is_current column
    if 'is_current' not in columns:
        op.add_column(
            'source_documents',
            sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true')
        )
    
    # Add is_rag_enabled column
    if 'is_rag_enabled' not in columns:
        op.add_column(
            'source_documents',
            sa.Column('is_rag_enabled', sa.Boolean(), nullable=False, server_default='true')
        )
    
    # Add index_status column
    if 'index_status' not in columns:
        op.add_column(
            'source_documents',
            sa.Column('index_status', sa.String(length=20), nullable=False, server_default='not_indexed')
        )
    
    # Add check constraints
    constraints = [c['name'] for c in inspector.get_check_constraints('source_documents')]
    
    if 'ck_source_document_language' not in constraints:
        op.create_check_constraint(
            'ck_source_document_language',
            'source_documents',
            "language IN ('ru', 'en')"
        )
    
    if 'ck_source_document_status' not in constraints:
        op.create_check_constraint(
            'ck_source_document_status',
            'source_documents',
            "status IN ('active', 'superseded', 'archived')"
        )
    
    if 'ck_source_document_index_status' not in constraints:
        op.create_check_constraint(
            'ck_source_document_index_status',
            'source_documents',
            "index_status IN ('not_indexed', 'indexed', 'error')"
        )


def downgrade() -> None:
    # Drop check constraints
    op.drop_constraint('ck_source_document_index_status', 'source_documents', type_='check')
    op.drop_constraint('ck_source_document_status', 'source_documents', type_='check')
    op.drop_constraint('ck_source_document_language', 'source_documents', type_='check')
    
    # Drop columns
    op.drop_column('source_documents', 'index_status')
    op.drop_column('source_documents', 'is_rag_enabled')
    op.drop_column('source_documents', 'is_current')
    op.drop_column('source_documents', 'status')
    op.drop_column('source_documents', 'version_label')
    op.drop_column('source_documents', 'language')

