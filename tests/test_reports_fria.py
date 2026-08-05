from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.reports.fria import generate_fria
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_missing_required_fields_are_flagged(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    draft = generate_fria(logger, questionnaire={})

    assert "required field(s) missing" in draft
    assert "Deployer name" in draft


def test_provided_fields_and_risk_data_are_included(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="essential_services", risk_tier=RiskTier.HIGH, gated=True)

    draft = generate_fria(
        logger,
        questionnaire={
            "deployer_name": "Example Bank",
            "deployment_context": "Retail banking",
            "affected_groups": "Loan applicants",
            "fundamental_rights_at_stake": "Non-discrimination",
        },
        category="essential_services",
    )

    assert "Example Bank" in draft
    assert "Loan applicants" in draft
    assert "high: 1 action(s) logged" in draft
    assert "Human approval gate at risk tier >= high" in draft
