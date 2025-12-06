"""add_document_id_to_csr_documents

Revision ID: xyz789ghi012
Revises: abc123def456
Create Date: 2025-01-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'xyz789ghi012'
down_revision: Union[str, None] = 'abc123def456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add document_id column to csr_documents table
    op.add_column('csr_documents', sa.Column('document_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_csr_documents_document_id',
        'csr_documents',
        'documents',
        ['document_id'],
        ['id']
    )
    op.create_index(op.f('ix_csr_documents_document_id'), 'csr_documents', ['document_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_csr_documents_document_id'), table_name='csr_documents')
    op.drop_constraint('fk_csr_documents_document_id', 'csr_documents', type_='foreignkey')
    op.drop_column('csr_documents', 'document_id')

