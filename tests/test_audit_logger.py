from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_log_writes_record_retrievable_by_query(tmp_path):
    store = SQLiteAuditStore(tmp_path / "audit.db")
    logger = AuditLogger(store=store)

    logger.log(
        action="check_loan_eligibility",
        category="essential_services",
        risk_tier=RiskTier.HIGH,
        inputs={"applicant_id": "A123"},
        outputs="eligible",
    )

    records = logger.query(category="essential_services")
    assert len(records) == 1
    assert records[0].action == "check_loan_eligibility"
    assert records[0].risk_tier == "high"
    assert records[0].outputs == "eligible"


def test_query_filters_by_risk_tier(tmp_path):
    store = SQLiteAuditStore(tmp_path / "audit.db")
    logger = AuditLogger(store=store)

    logger.log(action="a", category="c1", risk_tier=RiskTier.MINIMAL)
    logger.log(action="b", category="c2", risk_tier=RiskTier.HIGH)

    high_only = logger.query(risk_tier="high")
    assert len(high_only) == 1
    assert high_only[0].action == "b"


def test_log_persists_override_and_rationale_fields(tmp_path):
    store = SQLiteAuditStore(tmp_path / "audit.db")
    logger = AuditLogger(store=store)

    logger.log(
        action="check_loan_eligibility",
        category="essential_services",
        risk_tier=RiskTier.HIGH,
        approver_id="compliance_officer",
        override=True,
        reason="Manually verified applicant identity via phone call.",
        rationale=[{"source": "agent_scratchpad", "text": "Applicant matched KYC record."}],
    )

    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"
    assert record.override is True
    assert record.reason == "Manually verified applicant identity via phone call."
    assert record.rationale == [{"source": "agent_scratchpad", "text": "Applicant matched KYC record."}]


def test_audit_log_is_append_only_across_instances(tmp_path):
    db_path = tmp_path / "audit.db"
    AuditLogger(store=SQLiteAuditStore(db_path)).log(
        action="a", category="c", risk_tier=RiskTier.LIMITED
    )
    AuditLogger(store=SQLiteAuditStore(db_path)).log(
        action="b", category="c", risk_tier=RiskTier.LIMITED
    )

    records = AuditLogger(store=SQLiteAuditStore(db_path)).query(category="c")
    assert len(records) == 2
