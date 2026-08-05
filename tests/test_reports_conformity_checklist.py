from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.reports.conformity_checklist import generate_conformity_checklist
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_empty_audit_trail_flags_evidence_based_gaps(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    result = generate_conformity_checklist(logger)

    statuses = {item.requirement: item.status for item in result.items}
    assert statuses["Audit trail covers logged actions"] == "gap"
    assert statuses["Human oversight gates configured for high-risk actions"] == "gap"
    # "Override decisions carry a recorded reason" is vacuously met with zero
    # overrides logged — nothing to flag yet — so it's the one item that
    # isn't a gap on a fresh audit trail.
    assert statuses["Override decisions carry a recorded reason"] == "met"
    assert len(result.gaps) == len(result.items) - 1


def test_populated_audit_trail_and_questionnaire_marks_items_met(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="essential_services", risk_tier=RiskTier.HIGH, gated=True, approver_id="x")

    result = generate_conformity_checklist(
        logger,
        questionnaire={
            "system_name": "Loan Assistant",
            "intended_purpose": "Pre-screen applicants.",
            "data_governance_summary": "Retained 90 days.",
            "post_market_monitoring_plan_drafted": "yes",
            "fria_drafted": "yes",
        },
    )

    statuses = {item.requirement: item.status for item in result.items}
    assert statuses["Audit trail covers logged actions"] == "met"
    assert statuses["Human oversight gates configured for high-risk actions"] == "met"
    assert statuses["System description documented"] == "met"
    assert statuses["Post-market monitoring plan drafted"] == "met"


def test_override_without_review_confirmation_is_flagged(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="c", risk_tier=RiskTier.HIGH, gated=True, override=True, reason="r")

    result = generate_conformity_checklist(logger, questionnaire={})
    statuses = {item.requirement: item.status for item in result.items}
    assert statuses["Override decisions carry a recorded reason"] == "gap"


def test_to_markdown_renders_checkboxes(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    result = generate_conformity_checklist(logger)
    md = result.to_markdown()

    assert "- [ ]" in md
    assert "gap(s) found" in md
