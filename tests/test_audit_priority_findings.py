from aiactguard.audit_priority.findings import AuditFindingStore


def test_record_and_query_round_trip(tmp_path):
    store = AuditFindingStore(tmp_path / "audit.db")
    store.record("r1", True)
    store.record("r2", False)

    outcomes = store.outcomes_by_record_id()
    assert outcomes == {"r1": True, "r2": False}


def test_re_review_of_same_record_uses_most_recent_finding(tmp_path):
    store = AuditFindingStore(tmp_path / "audit.db")
    store.record("r1", True)
    store.record("r1", False)  # a second reviewer overturns the first finding

    outcomes = store.outcomes_by_record_id()
    assert outcomes["r1"] is False


def test_shares_the_db_file_with_the_main_audit_trail(tmp_path):
    from aiactguard.core.audit_logger import AuditLogger
    from aiactguard.core.risk_classifier import RiskTier
    from aiactguard.storage.sqlite_store import SQLiteAuditStore

    db_path = tmp_path / "audit.db"
    logger = AuditLogger(store=SQLiteAuditStore(db_path))
    logger.log(action="a", category="c", risk_tier=RiskTier.HIGH, classifier_confidence=0.9)

    findings = AuditFindingStore(db_path)  # same file, adds its own table
    findings.record("some-record-id", True)

    # both tables coexist in the same file
    records = logger.query(category="c")
    assert len(records) == 1
    assert findings.outcomes_by_record_id() == {"some-record-id": True}
