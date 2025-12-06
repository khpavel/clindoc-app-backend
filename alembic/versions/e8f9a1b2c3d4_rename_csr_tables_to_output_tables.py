"""rename csr tables to output tables

Revision ID: e8f9a1b2c3d4
Revises: 4fd91a5a7c9c
Create Date: 2025-01-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f9a1b2c3d4'
down_revision: Union[str, None] = 'merge_all_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename sequences first (before renaming tables)
    # PostgreSQL auto-creates sequences for SERIAL/BIGSERIAL columns
    # Only rename if source exists and target doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'csr_documents_id_seq')
               AND NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'output_documents_id_seq') THEN
                ALTER SEQUENCE csr_documents_id_seq RENAME TO output_documents_id_seq;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'csr_sections_id_seq')
               AND NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'output_sections_id_seq') THEN
                ALTER SEQUENCE csr_sections_id_seq RENAME TO output_sections_id_seq;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'csr_section_versions_id_seq')
               AND NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'output_section_versions_id_seq') THEN
                ALTER SEQUENCE csr_section_versions_id_seq RENAME TO output_section_versions_id_seq;
            END IF;
        END $$;
    """)
    
    # Rename tables (PostgreSQL will automatically update FK references)
    # Only rename if source table exists and target doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'csr_documents')
               AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'output_documents') THEN
                ALTER TABLE csr_documents RENAME TO output_documents;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'csr_sections')
               AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'output_sections') THEN
                ALTER TABLE csr_sections RENAME TO output_sections;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'csr_section_versions')
               AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'output_section_versions') THEN
                ALTER TABLE csr_section_versions RENAME TO output_section_versions;
            END IF;
        END $$;
    """)
    
    # Rename foreign key constraint names that explicitly reference old table names
    # Use exception handling to safely attempt renames
    op.execute("""
        DO $$
        BEGIN
            -- Try to rename FK constraint for document_id in output_documents if it exists with old name
            BEGIN
                ALTER TABLE output_documents RENAME CONSTRAINT fk_csr_documents_document_id TO fk_output_documents_document_id;
            EXCEPTION
                WHEN undefined_object THEN
                    -- Constraint doesn't exist with that name, skip
                    NULL;
            END;
            
            -- Try to rename FK constraint for template_id in output_section_versions if it exists with old name
            BEGIN
                ALTER TABLE output_section_versions RENAME CONSTRAINT fk_csr_section_versions_template_id TO fk_output_section_versions_template_id;
            EXCEPTION
                WHEN undefined_object THEN
                    -- Constraint doesn't exist with that name, skip
                    NULL;
            END;
        END $$;
    """)


def downgrade() -> None:
    # Rename tables back first (only if they exist and targets don't exist)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'output_documents')
               AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'csr_documents') THEN
                ALTER TABLE output_documents RENAME TO csr_documents;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'output_sections')
               AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'csr_sections') THEN
                ALTER TABLE output_sections RENAME TO csr_sections;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'output_section_versions')
               AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'csr_section_versions') THEN
                ALTER TABLE output_section_versions RENAME TO csr_section_versions;
            END IF;
        END $$;
    """)
    
    # Restore FK constraint names
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_output_section_versions_template_id') THEN
                ALTER TABLE csr_section_versions RENAME CONSTRAINT fk_output_section_versions_template_id TO fk_csr_section_versions_template_id;
            END IF;
            
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_output_documents_document_id') THEN
                ALTER TABLE csr_documents RENAME CONSTRAINT fk_output_documents_document_id TO fk_csr_documents_document_id;
            END IF;
        END $$;
    """)
    
    # Restore sequences (only if source exists and target doesn't exist)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'output_documents_id_seq')
               AND NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'csr_documents_id_seq') THEN
                ALTER SEQUENCE output_documents_id_seq RENAME TO csr_documents_id_seq;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'output_sections_id_seq')
               AND NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'csr_sections_id_seq') THEN
                ALTER SEQUENCE output_sections_id_seq RENAME TO csr_sections_id_seq;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'output_section_versions_id_seq')
               AND NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'csr_section_versions_id_seq') THEN
                ALTER SEQUENCE output_section_versions_id_seq RENAME TO csr_section_versions_id_seq;
            END IF;
        END $$;
    """)

