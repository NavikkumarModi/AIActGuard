from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.reports.eu_registration import compile_registration_data
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_missing_fields_are_tracked_and_rendered(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    data = compile_registration_data(logger, questionnaire={"provider_name": "Example Bank"})

    assert "System name" in data.missing_fields
    assert "_missing_" in data.to_markdown()


def test_complete_questionnaire_yields_no_missing_fields(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="essential_services", risk_tier=RiskTier.HIGH)

    data = compile_registration_data(
        logger,
        questionnaire={
            "provider_name": "Example Bank",
            "system_name": "Loan Assistant",
            "intended_purpose": "Pre-screen applicants.",
            "contact_email": "compliance@example.test",
        },
    )

    assert data.missing_fields == []
    assert data.risk_categories == ["essential_services"]
    assert "essential_services" in data.to_markdown()
