"""add_template_id_to_csr_section_versions

Revision ID: 4fd91a5a7c9c
Revises: d0ef26856a43
Create Date: 2025-12-05 01:47:22.927563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fd91a5a7c9c'
down_revision: Union[str, None] = 'd0ef26856a43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add template_id column to csr_section_versions table
    op.add_column(
        'csr_section_versions',
        sa.Column('template_id', sa.Integer(), nullable=True)
    )
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_csr_section_versions_template_id',
        'csr_section_versions',
        'templates',
        ['template_id'],
        ['id']
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint(
        'fk_csr_section_versions_template_id',
        'csr_section_versions',
        type_='foreignkey'
    )
    # Remove template_id column
    op.drop_column('csr_section_versions', 'template_id')

