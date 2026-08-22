from aiactguard.audit_priority.findings import AuditFindingStore
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.reports.drift_diagnostic import generate_drift_diagnostic
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_hand_computed_silent_risk_mass(tmp_path):
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(store=SQLiteAuditStore(db_path))
    findings = AuditFindingStore(db_path)

    # Bin 8 (confidence 0.85): 5 records total, all reviewed.
    # 4/5 true violations -> true_risk_rate = 0.8
    # of those 4, 2 were gated (caught) and 2 weren't (missed) -> miss_rate = 0.5
    # 3/5 records are high-exposure -> p_high_exposure = 0.6
    # p_bin = 5/10 = 0.5
    # silent_risk_mass = 0.5 * 0.8 * 0.5 * 0.6 = 0.12
    exposure_classes = ["irreversible_financial", "irreversible_financial", "irreversible_data", "reversible_read", "reversible_read"]
    gated_flags = [True, True, False, False, True]  # 2 of the 4 true violations below are gated
    true_violation_flags = [True, True, True, True, False]
    for i in range(5):
        record = logger.log(
            action=f"risky_{i}",
            category="essential_services",
            risk_tier=RiskTier.HIGH,
            classifier_confidence=0.85,
            action_exposure_class=exposure_classes[i],
            gated=gated_flags[i],
        )
        findings.record(record.record_id, is_true_violation=true_violation_flags[i])

    # Bin 1 (confidence 0.15): 5 records, only 3 reviewed -> insufficient data
    for i in range(5):
        record = logger.log(
            action=f"safe_{i}",
            category="essential_services",
            risk_tier=RiskTier.MINIMAL,
            classifier_confidence=0.15,
        )
        if i < 3:
            findings.record(record.record_id, is_true_violation=False)

    report = generate_drift_diagnostic(logger, findings)

    assert "silent_risk_mass=0.1200" in report
    assert "true_risk_rate=80%" in report
    assert "miss_rate=50%" in report
    assert "insufficient data" in report


def test_no_findings_at_all_reports_insufficient_data_everywhere(tmp_path):
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(store=SQLiteAuditStore(db_path))
    findings = AuditFindingStore(db_path)

    logger.log(action="a", category="c", risk_tier=RiskTier.HIGH, classifier_confidence=0.9)

    report = generate_drift_diagnostic(logger, findings)
    assert "No bins have enough ground-truth findings yet" in report


def test_no_records_at_all(tmp_path):
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(store=SQLiteAuditStore(db_path))
    findings = AuditFindingStore(db_path)

    report = generate_drift_diagnostic(logger, findings)
    assert "No audit records with classifier_confidence found yet." in report
