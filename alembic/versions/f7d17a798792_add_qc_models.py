"""add_qc_models

Revision ID: f7d17a798792
Revises: fbdd055efa7e
Create Date: 2025-12-06 22:35:44.857953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'f7d17a798792'
down_revision: Union[str, None] = 'fbdd055efa7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # Create qc_rules table
    if 'qc_rules' not in tables:
        op.create_table(
            'qc_rules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(length=100), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('severity', sa.String(length=20), nullable=False, server_default='info'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.CheckConstraint("severity IN ('info', 'warning', 'error')", name='check_qc_rule_severity'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_qc_rules_id', 'qc_rules', ['id'])
        op.create_index('ix_qc_rules_code', 'qc_rules', ['code'])

    # Create qc_issues table
    if 'qc_issues' not in tables:
        op.create_table(
            'qc_issues',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('study_id', sa.Integer(), nullable=False),
            sa.Column('document_id', sa.Integer(), nullable=True),
            sa.Column('section_id', sa.Integer(), nullable=True),
            sa.Column('rule_id', sa.Integer(), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_by', sa.String(length=100), nullable=True),
            sa.CheckConstraint("severity IN ('info', 'warning', 'error')", name='check_qc_issue_severity'),
            sa.CheckConstraint("status IN ('open', 'resolved', 'wont_fix')", name='check_qc_issue_status'),
            sa.ForeignKeyConstraint(['study_id'], ['studies.id']),
            sa.ForeignKeyConstraint(['document_id'], ['csr_documents.id']),
            sa.ForeignKeyConstraint(['section_id'], ['csr_sections.id']),
            sa.ForeignKeyConstraint(['rule_id'], ['qc_rules.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_qc_issues_id', 'qc_issues', ['id'])
        op.create_index('ix_qc_issues_study_id', 'qc_issues', ['study_id'])
        op.create_index('ix_qc_issues_document_id', 'qc_issues', ['document_id'])
        op.create_index('ix_qc_issues_section_id', 'qc_issues', ['section_id'])
        op.create_index('ix_qc_issues_rule_id', 'qc_issues', ['rule_id'])


def downgrade() -> None:
    # Drop qc_issues table
    op.drop_index('ix_qc_issues_rule_id', table_name='qc_issues')
    op.drop_index('ix_qc_issues_section_id', table_name='qc_issues')
    op.drop_index('ix_qc_issues_document_id', table_name='qc_issues')
    op.drop_index('ix_qc_issues_study_id', table_name='qc_issues')
    op.drop_index('ix_qc_issues_id', table_name='qc_issues')
    op.drop_table('qc_issues')
    
    # Drop qc_rules table
    op.drop_index('ix_qc_rules_code', table_name='qc_rules')
    op.drop_index('ix_qc_rules_id', table_name='qc_rules')
    op.drop_table('qc_rules')

