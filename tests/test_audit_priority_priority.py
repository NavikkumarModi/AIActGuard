"""The core validation pattern: a bin with a true violation rate clearly
above a safety target should end up ranked for review ahead of a bin
clearly below it, once enough ground-truth evidence has accumulated — and
before any evidence exists, everything should be flagged as uncertain
rather than quietly assumed safe.
"""

from aiactguard.audit_priority.findings import AuditFindingStore
from aiactguard.audit_priority.priority import compute_bin_ucb, prioritize_for_review
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.storage.sqlite_store import SQLiteAuditStore

_RISKY_CONFIDENCE = 0.85  # bin 8 of 10
_SAFE_CONFIDENCE = 0.15  # bin 1 of 10


def _seed_records(logger, *, confidence: float, n: int, action_prefix: str) -> list[str]:
    record_ids = []
    for i in range(n):
        record = logger.log(
            action=f"{action_prefix}_{i}",
            category="essential_services",
            risk_tier=RiskTier.HIGH,
            classifier_confidence=confidence,
        )
        record_ids.append(record.record_id)
    return record_ids


def test_bins_start_at_maximal_uncertainty_with_no_findings():
    assert compute_bin_ucb([]) == 1.0
    assert compute_bin_ucb([True, False, True]) == 1.0  # only 3 findings, below the 5-finding floor


def test_risky_bin_ranks_above_safe_bin_once_evidence_accumulates(tmp_path):
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(store=SQLiteAuditStore(db_path))
    findings = AuditFindingStore(db_path)

    risky_ids = _seed_records(logger, confidence=_RISKY_CONFIDENCE, n=20, action_prefix="risky")
    safe_ids = _seed_records(logger, confidence=_SAFE_CONFIDENCE, n=20, action_prefix="safe")

    # 16/20 (80%) true violations in the risky bin, 1/20 (5%) in the safe bin
    for i, record_id in enumerate(risky_ids):
        findings.record(record_id, is_true_violation=i < 16)
    for i, record_id in enumerate(safe_ids):
        findings.record(record_id, is_true_violation=i < 1)

    all_records = logger.query(limit=100)
    ranked = prioritize_for_review(all_records, findings, alpha=0.1)

    risky_ucb = next(item.ucb for item in ranked if item.record.action.startswith("risky"))
    safe_ucb = next(item.ucb for item in ranked if item.record.action.startswith("safe"))

    assert risky_ucb > safe_ucb
    assert safe_ucb < 1.0  # enough evidence has actually tightened the bound, not left at the default

    # every risky-bin item ranks above every safe-bin item in the final order
    ranked_actions = [item.record.action for item in ranked]
    last_risky_position = max(i for i, a in enumerate(ranked_actions) if a.startswith("risky"))
    first_safe_position = min(i for i, a in enumerate(ranked_actions) if a.startswith("safe"))
    assert last_risky_position < first_safe_position


def test_unreviewed_records_are_flagged_and_ranked_first_by_default(tmp_path):
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(store=SQLiteAuditStore(db_path))
    findings = AuditFindingStore(db_path)

    _seed_records(logger, confidence=0.5, n=3, action_prefix="unreviewed")

    ranked = prioritize_for_review(logger.query(limit=10), findings)

    assert all(item.ucb == 1.0 for item in ranked)
    assert all(item.already_reviewed is False for item in ranked)


def test_records_without_classifier_confidence_are_skipped(tmp_path):
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(store=SQLiteAuditStore(db_path))
    findings = AuditFindingStore(db_path)

    logger.log(action="legacy_row", category="c", risk_tier=RiskTier.HIGH)  # no classifier_confidence
    logger.log(action="modern_row", category="c", risk_tier=RiskTier.HIGH, classifier_confidence=0.5)

    ranked = prioritize_for_review(logger.query(limit=10), findings)

    assert len(ranked) == 1
    assert ranked[0].record.action == "modern_row"
