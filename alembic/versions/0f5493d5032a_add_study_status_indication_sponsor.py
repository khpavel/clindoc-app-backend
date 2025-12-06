"""add_study_status_indication_sponsor

Revision ID: 0f5493d5032a
Revises: b6f382ad0f4f
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f5493d5032a'
down_revision: Union[str, None] = 'b6f382ad0f4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column to studies table with default 'draft'
    op.add_column(
        'studies',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft')
    )
    
    # Add indication column to studies table (nullable)
    op.add_column(
        'studies',
        sa.Column('indication', sa.String(length=255), nullable=True)
    )
    
    # Add sponsor_name column to studies table (nullable)
    op.add_column(
        'studies',
        sa.Column('sponsor_name', sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    # Remove sponsor_name column
    op.drop_column('studies', 'sponsor_name')
    
    # Remove indication column
    op.drop_column('studies', 'indication')
    
    # Remove status column
    op.drop_column('studies', 'status')

