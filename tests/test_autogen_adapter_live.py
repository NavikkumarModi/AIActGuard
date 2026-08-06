"""Validates AIActGuardInterventionHandler against a real
SingleThreadedAgentRuntime + registered ToolAgent, sending a real
FunctionCall through runtime.send_message() — confirming the intervention
handler actually intercepts and that a raised ToolException genuinely
propagates back to the caller (AutoGen doesn't swallow it the way
LangChain's default callback manager did), not just that the handler
object's methods behave correctly in isolation.
"""

import asyncio

import pytest

autogen_core = pytest.importorskip("autogen_core")

from autogen_core import AgentId, FunctionCall, SingleThreadedAgentRuntime  # noqa: E402
from autogen_core.tool_agent import ToolAgent, ToolException  # noqa: E402
from autogen_core.tools import FunctionTool  # noqa: E402

from aiactguard.adapters.autogen_adapter import AIActGuardInterventionHandler  # noqa: E402
from aiactguard.core.approval import ApprovalContext, ApprovalDecision  # noqa: E402
from aiactguard.core.audit_logger import AuditLogger  # noqa: E402
from aiactguard.storage.sqlite_store import SQLiteAuditStore  # noqa: E402


def check_eligibility(applicant_id: str) -> str:
    return f"Applicant {applicant_id}: eligible"


async def _run_with_handler(handler) -> tuple:
    runtime = SingleThreadedAgentRuntime(intervention_handlers=[handler])
    tool = FunctionTool(check_eligibility, description="Check loan eligibility")
    tool_agent_type = await ToolAgent.register(
        runtime, "tool_executor_agent", lambda: ToolAgent(description="t", tools=[tool])
    )
    runtime.start()
    try:
        fc = FunctionCall(id="1", arguments='{"applicant_id": "A123"}', name="check_eligibility")
        result = await runtime.send_message(fc, AgentId(tool_agent_type, "default"))
        return "ok", result
    except ToolException as exc:
        return "denied", exc
    finally:
        await runtime.stop()


def test_real_runtime_allows_approved_tool_call(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    handler = AIActGuardInterventionHandler(category="essential_services", logger=logger, approvers=[approve])

    outcome, result = asyncio.run(_run_with_handler(handler))

    assert outcome == "ok"
    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"


def test_real_runtime_propagates_tool_exception_on_denial(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    handler = AIActGuardInterventionHandler(category="essential_services", logger=logger, approvers=[])

    outcome, exc = asyncio.run(_run_with_handler(handler))

    assert outcome == "denied"
    assert exc.name == "check_eligibility"
    record = logger.query(category="essential_services")[0]
    assert record.approved is False
