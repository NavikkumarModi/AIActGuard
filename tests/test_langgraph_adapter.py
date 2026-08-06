"""Framework-independent tests for make_guard() — no langgraph install
needed, since make_guard() itself has zero langgraph dependency (only
interrupt_approver does, and it imports langgraph lazily). See
test_langgraph_adapter_live.py for the real interrupt()/Command round-trip.
"""

import pytest

from aiactguard.adapters.langgraph_adapter import make_guard
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.policy.schema import ApprovalRequired
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def _logger(tmp_path):
    return AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))


def test_guard_step_approved_by_configured_approver(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = _logger(tmp_path)
    guard = make_guard(category="essential_services", logger=logger, approvers=[approve])

    guard("check_loan_eligibility", inputs={"applicant_id": "A123"})

    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"


def test_guard_step_denied_without_approver_raises(tmp_path):
    logger = _logger(tmp_path)
    guard = make_guard(category="essential_services", logger=logger, approvers=[])

    with pytest.raises(ApprovalRequired):
        guard("check_loan_eligibility", inputs={"applicant_id": "A123"})


def test_guard_step_ungated_category_is_a_no_op(tmp_path):
    logger = _logger(tmp_path)
    guard = make_guard(category="general_assistance", logger=logger)

    guard("summarize", inputs={"doc": "x"})

    record = logger.query(category="general_assistance")[0]
    assert record.gated is False
