from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.reports.technical_documentation import generate_technical_documentation
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def _logger(tmp_path):
    return AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))


def test_generate_flags_missing_questionnaire_fields(tmp_path):
    logger = _logger(tmp_path)
    doc = generate_technical_documentation(logger, questionnaire=None)

    assert "NEEDS INPUT: System name" in doc
    assert "NEEDS INPUT: Intended purpose" in doc


def test_generate_fills_in_provided_fields_and_audit_stats(tmp_path):
    logger = _logger(tmp_path)
    logger.log(action="check_loan_eligibility", category="essential_services", risk_tier=RiskTier.HIGH, gated=True, approver_id="x")

    doc = generate_technical_documentation(
        logger,
        questionnaire={"system_name": "Loan Assistant", "intended_purpose": "Pre-screen applicants."},
    )

    assert "Loan Assistant" in doc
    assert "Pre-screen applicants." in doc
    assert "high: 1" in doc
    assert "NEEDS INPUT: Data governance summary" in doc


def test_generate_includes_explainability_worked_example(tmp_path):
    logger = _logger(tmp_path)
    logger.log(
        action="check_loan_eligibility",
        category="essential_services",
        risk_tier=RiskTier.HIGH,
        gated=True,
        approver_id="compliance_officer",
        rationale=[{"source": "agent_scratchpad", "text": "Applicant matched KYC record."}],
    )

    doc = generate_technical_documentation(logger)

    assert "Applicant matched KYC record." in doc
    assert "compliance_officer" in doc
