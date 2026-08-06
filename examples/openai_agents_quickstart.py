"""Wrap an OpenAI Agents SDK agent with AIActGuard.

Requires: pip install aiactguard[openai-agents]
Requires: OPENAI_API_KEY set in the environment
"""

import asyncio

from agents import Agent, Runner, function_tool
from agents.exceptions import UserError

from aiactguard.adapters.openai_agents_adapter import AIActGuardRunHooks
from aiactguard.core.approval import ApprovalContext, ApprovalDecision


@function_tool
def check_loan_eligibility(applicant_id: str) -> str:
    """Check whether an applicant is eligible for a loan."""
    return f"Applicant {applicant_id}: eligible"


def prompt_approver(ctx: ApprovalContext) -> ApprovalDecision:
    approved = input(f"Approve {ctx.action} ({ctx.risk_tier.value})? [y/N] ").lower() == "y"
    return ApprovalDecision(approved=approved, approver_id="cli-operator")


async def main() -> None:
    agent = Agent(
        name="LoanAssistant",
        instructions="You check loan eligibility using the check_loan_eligibility tool.",
        tools=[check_loan_eligibility],
    )

    # essential_services is a high-risk Annex III category by default, so
    # this gate requires human approval before the tool call fires. A
    # denial surfaces as agents.exceptions.UserError, not ApprovalRequired
    # directly — see AIActGuardRunHooks' docstring for why.
    hooks = AIActGuardRunHooks(category="essential_services", approvers=[prompt_approver])

    try:
        result = await Runner.run(agent, "Check loan eligibility for applicant A123", hooks=hooks)
        print(result.final_output)
    except UserError as exc:
        print(f"Tool call denied: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
