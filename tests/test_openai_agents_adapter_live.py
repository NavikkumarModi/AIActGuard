"""Validates AIActGuardRunHooks against a real Runner.run() call — using a
hand-built fake Model (no OpenAI API key needed) that returns a function-
call response on the first turn and a final message on the second. This
is what caught the real behavior worth knowing here: raising inside
on_tool_start does stop the tool from executing, but the SDK's tool-
execution machinery catches it and re-raises wrapped in
agents.exceptions.UserError rather than letting ApprovalRequired through
unchanged — confirmed empirically, not assumed from the docs.
"""

import json

import pytest

agents_pkg = pytest.importorskip("agents")

from agents import Agent, Runner, function_tool  # noqa: E402
from agents.exceptions import UserError  # noqa: E402
from agents.models.interface import Model, ModelResponse  # noqa: E402
from agents.usage import Usage  # noqa: E402
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText  # noqa: E402

from aiactguard.adapters.openai_agents_adapter import AIActGuardRunHooks  # noqa: E402
from aiactguard.core.approval import ApprovalContext, ApprovalDecision  # noqa: E402
from aiactguard.core.audit_logger import AuditLogger  # noqa: E402
from aiactguard.storage.sqlite_store import SQLiteAuditStore  # noqa: E402


@function_tool
def check_loan_eligibility(applicant_id: str) -> str:
    """Check whether an applicant is eligible for a loan."""
    return f"Applicant {applicant_id}: eligible"


class _FakeModel(Model):
    """Returns a single function-call turn, then a final message — enough
    to drive Runner.run() through exactly one tool invocation with no
    network/API key involved."""

    def __init__(self):
        self.call_count = 0

    async def get_response(
        self,
        system_instructions,
        input,
        model_settings,
        tools,
        output_schema,
        handoffs,
        tracing,
        *,
        previous_response_id,
        conversation_id,
        prompt,
    ) -> ModelResponse:
        self.call_count += 1
        if self.call_count == 1:
            item = ResponseFunctionToolCall(
                id="fc1",
                call_id="call1",
                name="check_loan_eligibility",
                arguments=json.dumps({"applicant_id": "A123"}),
                type="function_call",
            )
            return ModelResponse(output=[item], usage=Usage(), response_id="r1")
        item = ResponseOutputMessage(
            id="m1",
            role="assistant",
            status="completed",
            type="message",
            content=[ResponseOutputText(text="Done", type="output_text", annotations=[])],
        )
        return ModelResponse(output=[item], usage=Usage(), response_id="r2")

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError

    async def close(self):
        pass


def _agent() -> Agent:
    return Agent(
        name="LoanAgent",
        instructions="You check loan eligibility.",
        tools=[check_loan_eligibility],
        model=_FakeModel(),
    )


def test_real_runner_allows_approved_tool_call(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    hooks = AIActGuardRunHooks(category="essential_services", logger=logger, approvers=[approve])

    import asyncio

    result = asyncio.run(Runner.run(_agent(), "Check eligibility for A123", hooks=hooks))

    assert result.final_output == "Done"
    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"


def test_real_runner_wraps_denial_in_user_error(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    hooks = AIActGuardRunHooks(category="essential_services", logger=logger, approvers=[])

    import asyncio

    with pytest.raises(UserError):
        asyncio.run(Runner.run(_agent(), "Check eligibility for A123", hooks=hooks))

    record = logger.query(category="essential_services")[0]
    assert record.approved is False
