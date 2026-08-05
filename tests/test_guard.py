import pytest

from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.guard import GuardCore
from aiactguard.policy.schema import ApprovalRequired
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def _guard(tmp_path, approvers=None, category="essential_services"):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    return GuardCore(category=category, logger=logger, approvers=approvers), logger


def test_ungated_action_is_approved_without_a_gate_rule(tmp_path):
    # general_assistance classifies as "limited" tier, which the default
    # policy has no gate rule for.
    guard, logger = _guard(tmp_path, category="general_assistance")

    outcome = guard.evaluate_and_log(action="summarize", text_for_classification="chatbot summary")

    assert outcome.approved is True
    assert outcome.gated is False


def test_gated_action_denied_when_no_approver_configured(tmp_path):
    guard, logger = _guard(tmp_path, approvers=[])

    with pytest.raises(ApprovalRequired):
        guard.evaluate_and_log(action="check_loan_eligibility")

    record = logger.query(category="essential_services")[0]
    assert record.approved is False
    assert record.gated is True
    assert record.approver_id == "none"


def test_gated_action_approved_by_configured_approver(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    guard, logger = _guard(tmp_path, approvers=[approve])
    outcome = guard.evaluate_and_log(action="check_loan_eligibility", outputs="eligible")

    assert outcome.approved is True
    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"
    assert record.outputs == "eligible"


def test_override_without_reason_is_rejected_by_default_policy(tmp_path):
    def override_no_reason(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer", override=True)

    guard, logger = _guard(tmp_path, approvers=[override_no_reason])

    with pytest.raises(ApprovalRequired):
        guard.evaluate_and_log(action="check_loan_eligibility")

    record = logger.query(category="essential_services")[0]
    assert record.approved is False
    assert record.override is True
    assert "reason is required" in record.reason


def test_override_with_reason_is_approved_and_logged(tmp_path):
    def override_with_reason(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(
            approved=True,
            approver_id="compliance_officer",
            override=True,
            reason="Manually verified applicant identity via phone call.",
        )

    guard, logger = _guard(tmp_path, approvers=[override_with_reason])
    outcome = guard.evaluate_and_log(action="check_loan_eligibility")

    assert outcome.approved is True
    record = logger.query(category="essential_services")[0]
    assert record.override is True
    assert record.reason == "Manually verified applicant identity via phone call."
