from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.mappings.iso_42001 import generate_iso_42001_mapping
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_mapping_includes_representative_clauses(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="essential_services", risk_tier=RiskTier.HIGH, gated=True, override=True, reason="r")

    mapping = generate_iso_42001_mapping(logger, questionnaire={"system_name": "Loan Assistant"})

    assert "Clause 4" in mapping
    assert "Clause 5" in mapping
    assert "Clause 6" in mapping
    assert "Clause 8" in mapping
    assert "Clause 9" in mapping
    assert "Clause 10" in mapping
    assert "Loan Assistant" in mapping


def test_mapping_flags_missing_system_name(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    mapping = generate_iso_42001_mapping(logger)
    assert "NEEDS INPUT: System name" in mapping
