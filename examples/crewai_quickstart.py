"""Wrap a CrewAI agent with AIActGuard.

Requires: pip install aiactguard crewai
"""

from crewai import Agent, Crew, Task
from crewai.tools import tool

from aiactguard.adapters.crewai_adapter import make_step_callback
from aiactguard.core.approval import ApprovalContext, ApprovalDecision


@tool("check_loan_eligibility")
def check_loan_eligibility(applicant_id: str) -> str:
    """Check whether an applicant is eligible for a loan."""
    return f"Applicant {applicant_id}: eligible"


def prompt_approver(ctx: ApprovalContext) -> ApprovalDecision:
    approved = input(f"Approve {ctx.action} ({ctx.risk_tier.value})? [y/N] ").lower() == "y"
    return ApprovalDecision(approved=approved, approver_id="cli-operator")


# essential_services is a high-risk Annex III category by default, so this
# gate requires human approval before the tool call fires.
guard_callback = make_step_callback(
    category="essential_services",
    approvers=[prompt_approver],
)

loan_agent = Agent(
    role="Loan Officer",
    goal="Check loan eligibility for applicants",
    backstory="An assistant that checks eligibility before a human signs off.",
    tools=[check_loan_eligibility],
    step_callback=guard_callback,
)

task = Task(
    description="Check loan eligibility for applicant A123",
    expected_output="Eligibility result for applicant A123",
    agent=loan_agent,
)

crew = Crew(agents=[loan_agent], tasks=[task])
result = crew.kickoff()
print(result)
