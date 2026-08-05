from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.reports._audit_summary import summarize
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_summarize_empty_records_returns_zeroed_summary():
    summary = summarize([])
    assert summary.total_actions == 0
    assert summary.by_risk_tier == {}
    assert summary.earliest_timestamp is None


def test_summarize_counts_gated_approved_denied_override(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="c", risk_tier=RiskTier.MINIMAL, approved=True, gated=False)
    logger.log(action="b", category="c", risk_tier=RiskTier.HIGH, approved=True, gated=True, approver_id="x")
    logger.log(action="c", category="c", risk_tier=RiskTier.HIGH, approved=False, gated=True)
    logger.log(action="d", category="c", risk_tier=RiskTier.HIGH, approved=True, gated=True, override=True, reason="r")

    records = logger.query(limit=10)
    summary = summarize(records)

    assert summary.total_actions == 4
    assert summary.gated_count == 3
    assert summary.approved_count == 3
    assert summary.denied_count == 1
    assert summary.override_count == 1
    assert summary.by_risk_tier == {"minimal": 1, "high": 3}
    assert summary.earliest_timestamp is not None
    assert summary.latest_timestamp is not None
