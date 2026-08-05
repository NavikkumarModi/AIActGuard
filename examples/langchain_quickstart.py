"""Wrap a LangChain agent with AIActGuard.

Requires: pip install aiactguard[langchain] langchain-openai
"""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from aiactguard.adapters.langchain_adapter import AIActGuardCallbackHandler


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

# essential_services is a high-risk Annex III category by default, so this
# gate requires human approval before the tool call fires.
guard = AIActGuardCallbackHandler(
    category="essential_services",
    approver=lambda ctx: input(f"Approve {ctx['tool']}? [y/N] ").lower() == "y",
)

result = executor.invoke(
    {"input": "Check loan eligibility for applicant A123"},
    config={"callbacks": [guard]},
)
print(result)
