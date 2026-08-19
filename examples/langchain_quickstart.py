"""Wrap a LangChain agent with AIActGuard.

Requires: pip install aiactguard[langchain] langchain-openai
"""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from aiactguard.adapters.langchain_adapter import AIActGuardCallbackHandler
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.policy.schema import PolicyConfig


@tool
def check_loan_eligibility(applicant_id: str) -> str:
    """Check whether an applicant is eligible for a loan."""
    return f"Applicant {applicant_id}: eligible"


llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_messages(
    [("system", "You are a loan assistant."), ("human", "{input}"), ("placeholder", "{agent_scratchpad}")]
)
agent = create_tool_calling_agent(llm, tools=[check_loan_eligibility], prompt=prompt)
executor = AgentExecutor(agent=agent, tools=[check_loan_eligibility])


def prompt_approver(ctx: ApprovalContext) -> ApprovalDecision:
    approved = input(f"Approve {ctx.action} ({ctx.risk_tier.value})? [y/N] ").lower() == "y"
    return ApprovalDecision(approved=approved, approver_id="cli-operator")


# Register the tool's exposure class for retrospective audit — how bad it
# is if this specific action turns out to have been wrong. There's no
# default; an unregistered action just logs action_exposure_class=None.
policy = PolicyConfig.default()
policy.register_action("check_loan_eligibility", "irreversible_financial")

# essential_services is a high-risk Annex III category by default, so this
# gate requires human approval before the tool call fires. `approvers` is
# an escalation chain — add a second approver here to route to a fallback
# if the first declines to decide (returns None).
guard = AIActGuardCallbackHandler(
    category="essential_services",
    policy=policy,
    approvers=[prompt_approver],
)

result = executor.invoke(
    {"input": "Check loan eligibility for applicant A123"},
    config={"callbacks": [guard]},
)
print(result)
