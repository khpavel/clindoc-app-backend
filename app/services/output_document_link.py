"""
OutputDocument service aliases.

These functions are semantic aliases for the CSR document link services. They provide
a new domain name "OutputDocument" as a first-class concept while keeping existing CSR
code and endpoints fully functional. This is a naming/alias refactor only; no behavior
changes yet.

Future refactors will rename the underlying functions from CSR* to OutputDocument*.
"""

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.user import User
from app.services.output_document_document_link import (
    get_or_create_output_document_for_document,
    get_or_create_output_document_for_study,
)

# Re-export OutputDocument services (these are the primary names now)
# The CSR* names are now backward-compatible aliases

__all__ = [
    "get_or_create_output_document_for_document",
    "get_or_create_output_document_for_study",
]

