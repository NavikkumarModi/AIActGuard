"""Tests AIActGuardRunHooks.on_tool_start directly with simple stand-in
context/tool objects, without spinning up a real Runner — requires
`agents` installed since AIActGuardRunHooks subclasses the SDK's RunHooks
(a hard import, same as the LangChain/AutoGen adapters, for the same
reason: it needs the SDK's real base class/attribute shapes, not
something duck-typeable). See test_openai_agents_adapter_live.py for the
full Runner.run() round-trip against a fake Model.
"""

import asyncio

import pytest

agents = pytest.importorskip("agents")

from aiactguard.adapters.openai_agents_adapter import AIActGuardRunHooks  # noqa: E402
from aiactguard.core.approval import ApprovalContext, ApprovalDecision  # noqa: E402
from aiactguard.core.audit_logger import AuditLogger  # noqa: E402
from aiactguard.policy.schema import ApprovalRequired  # noqa: E402
from aiactguard.storage.sqlite_store import SQLiteAuditStore  # noqa: E402


class _StubTool:
    name = "check_loan_eligibility"


class _StubContext:
    tool_name = "check_loan_eligibility"
    tool_arguments = '{"applicant_id": "A123"}'
    tool_call_id = "call_1"


def _logger(tmp_path):
    return AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))


def test_on_tool_start_logs_approved_call(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = _logger(tmp_path)
    hooks = AIActGuardRunHooks(category="essential_services", logger=logger, approvers=[approve])

    asyncio.run(hooks.on_tool_start(_StubContext(), agent=None, tool=_StubTool()))

    record = logger.query(category="essential_services")[0]
    assert record.action == "check_loan_eligibility"
    assert record.approver_id == "compliance_officer"


def test_on_tool_start_raises_when_denied(tmp_path):
    logger = _logger(tmp_path)
    hooks = AIActGuardRunHooks(category="essential_services", logger=logger, approvers=[])

    with pytest.raises(ApprovalRequired):
        asyncio.run(hooks.on_tool_start(_StubContext(), agent=None, tool=_StubTool()))

    record = logger.query(category="essential_services")[0]
    assert record.approved is False
