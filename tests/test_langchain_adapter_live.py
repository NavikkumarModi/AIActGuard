"""Validates AIActGuardCallbackHandler against real langchain_core objects
and real callback dispatch — not the hand-written stubs used elsewhere in
the suite. No LLM call involved: a real @tool-decorated function and a
real AgentAction are driven through langchain_core's actual callback
manager, which is what exercises the exact method signatures/attributes
(BaseCallbackHandler.on_tool_start/on_agent_action, AgentAction.log) the
adapter assumes rather than a hand-rolled approximation of them.
"""

import pytest

langchain_core = pytest.importorskip("langchain_core")

from langchain_core.agents import AgentAction  # noqa: E402
from langchain_core.tools import tool  # noqa: E402

from aiactguard.adapters.langchain_adapter import AIActGuardCallbackHandler  # noqa: E402
from aiactguard.core.approval import ApprovalContext, ApprovalDecision  # noqa: E402
from aiactguard.core.audit_logger import AuditLogger  # noqa: E402
from aiactguard.policy.schema import ApprovalRequired  # noqa: E402
from aiactguard.storage.sqlite_store import SQLiteAuditStore  # noqa: E402


@tool
def check_loan_eligibility(applicant_id: str) -> str:
    """Check whether an applicant is eligible for a loan."""
    return f"Applicant {applicant_id}: eligible"


def _logger(tmp_path):
    return AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))


def test_real_tool_call_through_real_callback_dispatch_is_gated_and_logged(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = _logger(tmp_path)
    handler = AIActGuardCallbackHandler(category="essential_services", logger=logger, approvers=[approve])

    result = check_loan_eligibility.run("A123", callbacks=[handler])

    assert result == "Applicant A123: eligible"
    record = logger.query(category="essential_services")[0]
    assert record.action == "check_loan_eligibility"
    assert record.approver_id == "compliance_officer"
    assert record.gated is True


def test_real_agent_action_log_is_captured_as_rationale(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = _logger(tmp_path)
    handler = AIActGuardCallbackHandler(category="essential_services", logger=logger, approvers=[approve])

    action = AgentAction(
        tool="check_loan_eligibility",
        tool_input="A123",
        log="I should check eligibility for A123.",
    )
    handler.on_agent_action(action)
    check_loan_eligibility.run("A123", callbacks=[handler])

    record = logger.query(category="essential_services")[0]
    assert record.rationale == [{"source": "agent_scratchpad", "text": "I should check eligibility for A123."}]


def test_real_tool_call_denied_when_no_approver_raises_through_real_dispatch(tmp_path):
    logger = _logger(tmp_path)
    handler = AIActGuardCallbackHandler(category="essential_services", logger=logger, approvers=[])

    with pytest.raises(ApprovalRequired):
        check_loan_eligibility.run("A123", callbacks=[handler])

    record = logger.query(category="essential_services")[0]
    assert record.approved is False
