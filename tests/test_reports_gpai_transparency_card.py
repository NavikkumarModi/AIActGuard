from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.reports.gpai_transparency_card import generate_gpai_transparency_card
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_flags_missing_model_version_usage(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="c", risk_tier=RiskTier.MINIMAL)

    card = generate_gpai_transparency_card(logger)
    assert "No `model_version` recorded" in card
    assert "NEEDS INPUT: Model name" in card


def test_reports_usage_counts_by_model_version(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="c", risk_tier=RiskTier.MINIMAL, model_version="gpt-4o")
    logger.log(action="b", category="c", risk_tier=RiskTier.MINIMAL, model_version="gpt-4o")
    logger.log(action="c", category="c", risk_tier=RiskTier.MINIMAL, model_version="claude-sonnet-5")

    card = generate_gpai_transparency_card(
        logger,
        questionnaire={
            "model_name": "gpt-4o",
            "provider": "OpenAI",
            "capabilities": "General chat.",
            "known_limitations": "None noted.",
            "known_risks": "None noted.",
        },
    )

    assert "gpt-4o: 2 logged call(s)" in card
    assert "claude-sonnet-5: 1 logged call(s)" in card
    assert "OpenAI" in card
