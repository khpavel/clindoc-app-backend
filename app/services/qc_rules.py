from sqlalchemy.orm import Session

from app.models.qc import QCRule, QCIssue, QCRuleSeverity, QCIssueStatus
from app.models.csr import CsrDocument, CsrSection
from app.services.csr_defaults import DEFAULT_CSR_SECTIONS


def get_or_create_required_sections_rule(db: Session) -> QCRule:
    """
    Получить или создать правило для проверки наличия обязательных секций.
    """
    rule = db.query(QCRule).filter(QCRule.code == "REQUIRED_SECTIONS").first()
    
    if not rule:
        rule = QCRule(
            code="REQUIRED_SECTIONS",
            name="Required Sections Check",
            description="Проверка наличия всех обязательных секций согласно CSR-шаблону",
            severity=QCRuleSeverity.WARNING.value,
            is_active=True
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
    
    return rule


def check_required_sections(
    db: Session,
    document_id: int,
    study_id: int
) -> list[QCIssue]:
    """
    Проверка наличия всех обязательных секций в документе.
    Создаёт QCIssue для каждой отсутствующей обязательной секции.
    
    Returns:
        Список созданных QCIssue
    """
    # Получить или создать правило
    rule = get_or_create_required_sections_rule(db)
    
    if not rule.is_active:
        return []
    
    # Загрузить документ
    document = db.query(CsrDocument).filter(CsrDocument.id == document_id).first()
    if not document:
        return []
    
    # Получить все секции документа
    existing_sections = db.query(CsrSection).filter(
        CsrSection.document_id == document_id
    ).all()
    existing_codes = {section.code for section in existing_sections}
    
    # Получить список обязательных секций из DEFAULT_CSR_SECTIONS
    required_codes = {section["code"] for section in DEFAULT_CSR_SECTIONS}
    
    # Найти отсутствующие секции
    missing_codes = required_codes - existing_codes
    
    # Удалить существующие issues для этого документа и правила
    db.query(QCIssue).filter(
        QCIssue.document_id == document_id,
        QCIssue.rule_id == rule.id,
        QCIssue.status == QCIssueStatus.OPEN.value
    ).delete()
    
    # Создать issues для каждой отсутствующей секции
    issues = []
    for code in missing_codes:
        section_info = next((s for s in DEFAULT_CSR_SECTIONS if s["code"] == code), None)
        section_title = section_info["title"] if section_info else code
        
        issue = QCIssue(
            study_id=study_id,
            document_id=document_id,
            section_id=None,
            rule_id=rule.id,
            severity=rule.severity,
            status=QCIssueStatus.OPEN.value,
            message=f"Отсутствует обязательная секция: {section_title} ({code})"
        )
        db.add(issue)
        issues.append(issue)
    
    db.commit()
    
    # Refresh issues to get IDs
    for issue in issues:
        db.refresh(issue)
    
    return issues


def run_qc_rules_for_document(
    db: Session,
    document_id: int,
    study_id: int
) -> list[QCIssue]:
    """
    Запустить все активные QC правила для документа.
    
    Returns:
        Список всех созданных QCIssue
    """
    all_issues = []
    
    # Запустить проверку обязательных секций
    issues = check_required_sections(db, document_id, study_id)
    all_issues.extend(issues)
    
    # Здесь можно добавить другие правила в будущем
    
    return all_issues
