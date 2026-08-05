import pytest

from aiactguard.adapters.crewai_adapter import make_step_callback
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.policy.schema import ApprovalRequired
from aiactguard.storage.sqlite_store import SQLiteAuditStore


class _StubStep:
    def __init__(self, tool, tool_input):
        self.tool = tool
        self.tool_input = tool_input


def test_step_callback_logs_ungated_tool_call(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    callback = make_step_callback(category="general_assistance", logger=logger)

    callback(_StubStep(tool="summarize", tool_input="doc.txt"))

    records = logger.query(category="general_assistance")
    assert len(records) == 1
    assert records[0].action == "summarize"


def test_step_callback_raises_and_logs_denial_for_gated_call_without_approver(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    callback = make_step_callback(category="essential_services", logger=logger, approvers=[])

    with pytest.raises(ApprovalRequired):
        callback(_StubStep(tool="check_loan_eligibility", tool_input="A123"))

    record = logger.query(category="essential_services")[0]
    assert record.approved is False
    assert record.gated is True


def test_step_callback_approves_via_configured_approver(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    callback = make_step_callback(category="essential_services", logger=logger, approvers=[approve])

    callback(_StubStep(tool="check_loan_eligibility", tool_input="A123"))

    record = logger.query(category="essential_services")[0]
    assert record.approved is True
    assert record.approver_id == "compliance_officer"


def test_step_callback_ignores_non_tool_step():
    callback = make_step_callback(category="essential_services", approvers=[])
    # An AgentFinish-like step with neither `tool` nor `tool_input` attrs
    # should be a no-op, not raise.
    callback(object())
