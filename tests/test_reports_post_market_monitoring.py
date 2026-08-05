from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.reports.post_market_monitoring import generate_post_market_monitoring_plan
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_plan_includes_audit_derived_signals(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="c", risk_tier=RiskTier.HIGH, gated=True, approved=False)
    logger.log(action="b", category="c", risk_tier=RiskTier.HIGH, gated=True, override=True, reason="r")

    plan = generate_post_market_monitoring_plan(logger)

    assert "Denials:** 1" in plan
    assert "Overrides of a gate decision:** 1" in plan


def test_plan_flags_missing_cadence_and_owner(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    plan = generate_post_market_monitoring_plan(logger)

    assert "NEEDS INPUT: Review cadence" in plan
    assert "NEEDS INPUT: Monitoring plan owner" in plan
