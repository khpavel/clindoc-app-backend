from sqlalchemy.orm import Session

from app.models.qc import QCRule, QCIssue, QCRuleSeverity, QCIssueStatus
from app.models.output_document import OutputDocument, OutputSection
from app.services.output_document_defaults import DEFAULT_CSR_SECTIONS
from app.services.qc_config import get_qc_rule_config
from app.i18n import t


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
    study_id: int,
    language: str = "ru",
) -> list[QCIssue]:
    """
    Проверка наличия всех обязательных секций в документе.
    Создаёт QCIssue для каждой отсутствующей обязательной секции.
    
    Uses language-specific QC configuration to determine rule behavior.
    
    Returns:
        Список созданных QCIssue
    """
    # Получить или создать правило
    rule = get_or_create_required_sections_rule(db)
    
    if not rule.is_active:
        return []
    
    # Get language-specific configuration for this rule
    rule_config = get_qc_rule_config("REQUIRED_SECTIONS", language)
    
    # Check if rule is enabled for this language
    if not rule_config.get("enabled", True):
        return []
    
    # Загрузить документ
    document = db.query(OutputDocument).filter(OutputDocument.id == document_id).first()
    if not document:
        return []
    
    # Получить все секции документа
    existing_sections = db.query(OutputSection).filter(
        OutputSection.document_id == document_id
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
    
    # Use language-specific severity if configured, otherwise use rule default
    severity_override = rule_config.get("severity")
    issue_severity = rule.severity
    if severity_override:
        # Map string severity to QCRuleSeverity enum value
        severity_map = {
            "info": QCRuleSeverity.INFO.value,
            "warning": QCRuleSeverity.WARNING.value,
            "error": QCRuleSeverity.ERROR.value,
        }
        issue_severity = severity_map.get(severity_override, rule.severity)
    
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
            severity=issue_severity,
            status=QCIssueStatus.OPEN.value,
            message=t("QC_MISSING_SECTION", language, section_title=section_title, code=code)
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
    study_id: int,
    language: str = "ru",
) -> list[QCIssue]:
    """
    Запустить все активные QC правила для документа.
    
    Args:
        db: Database session
        document_id: ID of the OutputDocument to check
        study_id: ID of the study
        language: Language code ("ru" or "en") for language-specific rule sets
    
    Returns:
        Список всех созданных QCIssue
    """
    all_issues = []
    
    # Запустить проверку обязательных секций
    issues = check_required_sections(db, document_id, study_id, language=language)
    all_issues.extend(issues)
    
    # Здесь можно добавить другие правила в будущем
    
    return all_issues
