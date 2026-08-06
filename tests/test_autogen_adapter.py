"""Unlike the CrewAI/Claude Agent SDK adapters, this one can't be
duck-typed against a hand-built stub: it needs a real `isinstance(message,
FunctionCall)` check, so `autogen_core.FunctionCall` is a hard import.
These tests exercise the handler directly (no runtime needed) with a real
FunctionCall instance; see test_autogen_adapter_live.py for the full
SingleThreadedAgentRuntime + ToolAgent round-trip.
"""

import asyncio

import pytest

autogen_core = pytest.importorskip("autogen_core")

from autogen_core import FunctionCall  # noqa: E402
from autogen_core.tool_agent import ToolException  # noqa: E402

from aiactguard.adapters.autogen_adapter import AIActGuardInterventionHandler  # noqa: E402
from aiactguard.core.approval import ApprovalContext, ApprovalDecision  # noqa: E402
from aiactguard.core.audit_logger import AuditLogger  # noqa: E402
from aiactguard.storage.sqlite_store import SQLiteAuditStore  # noqa: E402


def _logger(tmp_path):
    return AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))


def test_on_send_passes_through_non_function_call_messages(tmp_path):
    handler = AIActGuardInterventionHandler(category="essential_services", logger=_logger(tmp_path), approvers=[])
    result = asyncio.run(handler.on_send("not a function call", message_context=None, recipient=None))
    assert result == "not a function call"


def test_on_send_allows_approved_function_call(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = _logger(tmp_path)
    handler = AIActGuardInterventionHandler(category="essential_services", logger=logger, approvers=[approve])
    fc = FunctionCall(id="1", arguments="{}", name="check_loan_eligibility")

    result = asyncio.run(handler.on_send(fc, message_context=None, recipient=None))

    assert result is fc
    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"


def test_on_send_raises_tool_exception_when_denied(tmp_path):
    logger = _logger(tmp_path)
    handler = AIActGuardInterventionHandler(category="essential_services", logger=logger, approvers=[])
    fc = FunctionCall(id="1", arguments="{}", name="check_loan_eligibility")

    with pytest.raises(ToolException):
        asyncio.run(handler.on_send(fc, message_context=None, recipient=None))

    record = logger.query(category="essential_services")[0]
    assert record.approved is False
