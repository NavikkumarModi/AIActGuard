"""Wrap a LangGraph node with AIActGuard, using LangGraph's own interrupt()
mechanism for human-in-the-loop approval — no LLM/API key needed to run
this example, since the graph node calls the guard directly.

Requires: pip install aiactguard[langgraph]
"""

import uuid
from typing import Optional

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.types import Command
from typing_extensions import TypedDict

from aiactguard.adapters.langgraph_adapter import interrupt_approver, make_guard


class State(TypedDict):
    applicant_id: str
    result: Optional[str]


# essential_services is a high-risk Annex III category by default, so this
# gate pauses the graph via interrupt() until a human resumes it.
guard = make_guard(category="essential_services", approvers=[interrupt_approver])


def check_eligibility_node(state: State) -> dict:
    guard("check_loan_eligibility", inputs={"applicant_id": state["applicant_id"]})
    return {"result": f"Applicant {state['applicant_id']}: eligible"}


builder = StateGraph(State)
builder.add_node("check_eligibility", check_eligibility_node)
builder.add_edge(START, "check_eligibility")
graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

paused = graph.invoke({"applicant_id": "A123", "result": None}, config)
print("Paused for approval:", paused["__interrupt__"])

approved = input("Approve check_loan_eligibility? [y/N] ").lower() == "y"
resumed = graph.invoke(
    Command(resume={"approved": approved, "approver_id": "cli-operator"}),
    config,
)
print(resumed)
