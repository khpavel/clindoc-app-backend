from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.qc import QCIssue, QCIssueStatus
from app.models.csr import CsrDocument
from app.models.study import Study
from app.models.user import User
from app.schemas.qc import QCIssueRead, QCIssueListResponse, QCRunResponse
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403, verify_study_access
from app.services.qc_rules import run_qc_rules_for_document

router = APIRouter(prefix="/qc", tags=["qc"])


@router.post("/documents/{document_id}/run", response_model=QCRunResponse)
def run_qc_for_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Запустить набор базовых правил QC на документ и создать Issues.
    
    Требует доступ к исследованию, к которому принадлежит документ.
    """
    # Загрузить документ
    document = db.query(CsrDocument).filter(CsrDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Проверить доступ к исследованию
    verify_study_access(document.study_id, current_user.id, db)
    
    # Запустить QC правила
    issues = run_qc_rules_for_document(db, document_id, document.study_id)
    
    return QCRunResponse(
        document_id=document_id,
        issues_created=len(issues),
        message=f"QC check completed. Created {len(issues)} issue(s)."
    )


@router.get("/issues/{study_id}", response_model=QCIssueListResponse)
def get_qc_issues(
    study_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: open, resolved, wont_fix"),
    severity_filter: Optional[str] = Query(None, alias="severity", description="Filter by severity: info, warning, error"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Получить список QC issues для исследования с фильтрами по статусу и серьёзности.
    
    Доступны фильтры:
    - status: open, resolved, wont_fix
    - severity: info, warning, error
    """
    # Построить запрос
    query = db.query(QCIssue).filter(QCIssue.study_id == study_id)
    
    # Применить фильтры
    if status_filter:
        if status_filter not in ["open", "resolved", "wont_fix"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status filter. Must be one of: open, resolved, wont_fix"
            )
        query = query.filter(QCIssue.status == status_filter)
    
    if severity_filter:
        if severity_filter not in ["info", "warning", "error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid severity filter. Must be one of: info, warning, error"
            )
        query = query.filter(QCIssue.severity == severity_filter)
    
    # Получить все issues
    issues = query.order_by(QCIssue.created_at.desc()).all()
    
    return QCIssueListResponse(
        issues=issues,
        total=len(issues)
    )


@router.get("/studies/{study_id}/issues", response_model=QCIssueListResponse)
def get_qc_issues_for_study(
    study_id: int,
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: open, resolved, wont_fix"),
    severity_filter: Optional[str] = Query(None, alias="severity", description="Filter by severity: info, warning, error"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Получить список QC issues для исследования с фильтрами по документу, статусу и серьёзности.
    
    Доступны фильтры:
    - document_id: фильтр по ID документа
    - status: open, resolved, wont_fix
    - severity: info, warning, error
    """
    # Построить запрос
    query = db.query(QCIssue).filter(QCIssue.study_id == study_id)
    
    # Фильтр по document_id
    if document_id is not None:
        query = query.filter(QCIssue.document_id == document_id)
    
    # Применить фильтры
    if status_filter:
        if status_filter not in ["open", "resolved", "wont_fix"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status filter. Must be one of: open, resolved, wont_fix"
            )
        query = query.filter(QCIssue.status == status_filter)
    
    if severity_filter:
        if severity_filter not in ["info", "warning", "error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid severity filter. Must be one of: info, warning, error"
            )
        query = query.filter(QCIssue.severity == severity_filter)
    
    # Получить все issues
    issues = query.order_by(QCIssue.created_at.desc()).all()
    
    return QCIssueListResponse(
        issues=issues,
        total=len(issues)
    )