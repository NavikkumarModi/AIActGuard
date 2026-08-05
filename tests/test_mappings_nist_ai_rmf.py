from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.mappings.nist_ai_rmf import generate_nist_ai_rmf_mapping
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_mapping_includes_all_four_functions(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="essential_services", risk_tier=RiskTier.HIGH, gated=True, approver_id="x")

    mapping = generate_nist_ai_rmf_mapping(logger, questionnaire={"policy_owner": "Head of Compliance"})

    assert "## Govern" in mapping
    assert "## Map" in mapping
    assert "## Measure" in mapping
    assert "## Manage" in mapping
    assert "Head of Compliance" in mapping
    assert "essential_services" in mapping


def test_mapping_flags_missing_policy_owner(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    mapping = generate_nist_ai_rmf_mapping(logger)
    assert "NEEDS INPUT: Policy owner" in mapping
