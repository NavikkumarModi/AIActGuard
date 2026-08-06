"""Wrap an AutoGen Core tool-executing agent with AIActGuard.

This drives the ToolAgent directly (constructing the FunctionCall by hand)
rather than through a full LLM-driven conversation loop, so it runs with
no API key needed — see AutoGen's own docs for wiring a model client into
the full ToolUseAgent conversation pattern; AIActGuard's integration point
(the intervention handler) is the same either way.

Requires: pip install aiactguard[autogen]
"""

import asyncio
import json

from autogen_core import AgentId, FunctionCall, SingleThreadedAgentRuntime
from autogen_core.tool_agent import ToolAgent, ToolException
from autogen_core.tools import FunctionTool

from aiactguard.adapters.autogen_adapter import AIActGuardInterventionHandler
from aiactguard.core.approval import ApprovalContext, ApprovalDecision


def check_loan_eligibility(applicant_id: str) -> str:
    """Check whether an applicant is eligible for a loan."""
    return f"Applicant {applicant_id}: eligible"


def prompt_approver(ctx: ApprovalContext) -> ApprovalDecision:
    approved = input(f"Approve {ctx.action} ({ctx.risk_tier.value})? [y/N] ").lower() == "y"
    return ApprovalDecision(approved=approved, approver_id="cli-operator")


async def main() -> None:
    # essential_services is a high-risk Annex III category by default, so
    # this gate requires human approval before the tool call fires.
    handler = AIActGuardInterventionHandler(category="essential_services", approvers=[prompt_approver])
    runtime = SingleThreadedAgentRuntime(intervention_handlers=[handler])

    tool = FunctionTool(check_loan_eligibility, description="Check loan eligibility")
    tool_agent_type = await ToolAgent.register(
        runtime, "tool_executor_agent", lambda: ToolAgent(description="Tool executor", tools=[tool])
    )
    runtime.start()

    try:
        fc = FunctionCall(id="1", arguments=json.dumps({"applicant_id": "A123"}), name="check_loan_eligibility")
        result = await runtime.send_message(fc, AgentId(tool_agent_type, "default"))
        print(result)
    except ToolException as exc:
        print(f"Tool call denied: {exc.content}")
    finally:
        await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
