from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.storage.sqlite_store import SQLiteAuditStore
from aiactguard.testing.fairness_scan import GroupOutcome, compute_disparate_impact, scan_audit_trail


def test_equal_selection_rates_are_not_flagged():
    outcomes = [GroupOutcome(group="a", approved=True), GroupOutcome(group="a", approved=False)] * 5
    outcomes += [GroupOutcome(group="b", approved=True), GroupOutcome(group="b", approved=False)] * 5

    result = compute_disparate_impact(outcomes, threshold=0.8)
    assert result.disparate_impact_ratio == 1.0
    assert result.flagged is False


def test_disparate_selection_rates_are_flagged():
    outcomes = [GroupOutcome(group="a", approved=True) for _ in range(9)] + [GroupOutcome(group="a", approved=False)]
    outcomes += [GroupOutcome(group="b", approved=True) for _ in range(4)] + [GroupOutcome(group="b", approved=False) for _ in range(6)]

    result = compute_disparate_impact(outcomes, threshold=0.8)
    assert result.disparate_impact_ratio == 0.4 / 0.9
    assert result.flagged is True


def test_single_group_yields_no_ratio():
    outcomes = [GroupOutcome(group="a", approved=True), GroupOutcome(group="a", approved=False)]
    result = compute_disparate_impact(outcomes)
    assert result.disparate_impact_ratio is None
    assert result.flagged is False


def test_empty_outcomes_returns_empty_result():
    result = compute_disparate_impact([])
    assert result.selection_rates == {}
    assert result.disparate_impact_ratio is None


def test_scan_audit_trail_groups_via_group_key(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="c", risk_tier=RiskTier.HIGH, approved=True, inputs={"region": "eu"})
    logger.log(action="b", category="c", risk_tier=RiskTier.HIGH, approved=False, inputs={"region": "eu"})
    logger.log(action="c", category="c", risk_tier=RiskTier.HIGH, approved=True, inputs={"region": "us"})

    result = scan_audit_trail(logger, group_key=lambda r: r.inputs.get("region"))

    assert result.counts == {"eu": 2, "us": 1}
    assert result.selection_rates["eu"] == 0.5
    assert result.selection_rates["us"] == 1.0
