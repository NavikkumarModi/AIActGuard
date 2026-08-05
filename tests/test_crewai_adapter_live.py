"""Validates make_step_callback against crewai's real
crewai.agents.parser.AgentAction/AgentFinish dataclasses — the actual types
CrewAI's step_callback receives (verified against crew_agent_executor.py's
_invoke_step_callback) — instead of the hand-rolled _StubStep used in
tests/test_crewai_adapter.py.
"""

import pytest

crewai = pytest.importorskip("crewai")

from crewai.agents.parser import AgentAction, AgentFinish  # noqa: E402

from aiactguard.adapters.crewai_adapter import make_step_callback  # noqa: E402
from aiactguard.core.approval import ApprovalContext, ApprovalDecision  # noqa: E402
from aiactguard.core.audit_logger import AuditLogger  # noqa: E402
from aiactguard.policy.schema import ApprovalRequired  # noqa: E402
from aiactguard.storage.sqlite_store import SQLiteAuditStore  # noqa: E402


def _logger(tmp_path):
    return AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))


def test_real_agent_action_is_gated_and_logged(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = _logger(tmp_path)
    callback = make_step_callback(category="essential_services", logger=logger, approvers=[approve])

    action = AgentAction(
        thought="I should check eligibility for A123.",
        tool="check_loan_eligibility",
        tool_input="A123",
        text="...",
    )
    callback(action)

    record = logger.query(category="essential_services")[0]
    assert record.action == "check_loan_eligibility"
    assert record.approver_id == "compliance_officer"


def test_real_agent_action_denied_without_approver_raises(tmp_path):
    logger = _logger(tmp_path)
    callback = make_step_callback(category="essential_services", logger=logger, approvers=[])

    action = AgentAction(thought="...", tool="check_loan_eligibility", tool_input="A123", text="...")

    with pytest.raises(ApprovalRequired):
        callback(action)


def test_real_agent_finish_is_ignored():
    callback = make_step_callback(category="essential_services", approvers=[])
    finish = AgentFinish(thought="Done.", output="Final answer.", text="...")
    callback(finish)  # should be a no-op, not raise
