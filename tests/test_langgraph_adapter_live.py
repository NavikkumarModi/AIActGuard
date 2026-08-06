"""Validates interrupt_approver against a real compiled LangGraph
StateGraph with a checkpointer — an actual pause (graph.invoke returns a
`__interrupt__` key rather than raising) and a real Command(resume=...)
round-trip, not a stub. This is the part of the LangGraph adapter that's
hardest to get right from documentation alone: interrupt() suspends
*within* the node and LangGraph re-executes the whole node on resume,
which is a fundamentally different control-flow shape than a callback.
"""

import uuid

import pytest

langgraph = pytest.importorskip("langgraph")

from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402
from langgraph.constants import START  # noqa: E402
from langgraph.graph import StateGraph  # noqa: E402
from langgraph.types import Command  # noqa: E402
from typing_extensions import TypedDict  # noqa: E402

from aiactguard.adapters.langgraph_adapter import interrupt_approver, make_guard  # noqa: E402
from aiactguard.core.audit_logger import AuditLogger  # noqa: E402
from aiactguard.policy.schema import ApprovalRequired  # noqa: E402
from aiactguard.storage.sqlite_store import SQLiteAuditStore  # noqa: E402


class _State(TypedDict):
    applicant_id: str
    result: str


def _build_graph(guard):
    def node(state: _State) -> dict:
        guard("check_loan_eligibility", inputs={"applicant_id": state["applicant_id"]})
        return {"result": "eligible"}

    builder = StateGraph(_State)
    builder.add_node("node", node)
    builder.add_edge(START, "node")
    return builder.compile(checkpointer=InMemorySaver())


def _config():
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def test_graph_pauses_on_gated_action_and_resumes_on_approval(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    guard = make_guard(category="essential_services", logger=logger, approvers=[interrupt_approver])
    graph = _build_graph(guard)
    config = _config()

    paused = graph.invoke({"applicant_id": "A123"}, config)
    assert "__interrupt__" in paused

    resumed = graph.invoke(
        Command(resume={"approved": True, "approver_id": "compliance_officer"}), config
    )
    assert resumed["result"] == "eligible"

    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"
    assert record.approved is True


def test_graph_resume_with_denial_raises_approval_required(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    guard = make_guard(category="essential_services", logger=logger, approvers=[interrupt_approver])
    graph = _build_graph(guard)
    config = _config()

    graph.invoke({"applicant_id": "A123"}, config)

    with pytest.raises(ApprovalRequired):
        graph.invoke(Command(resume={"approved": False, "reason": "suspicious"}), config)

    record = logger.query(category="essential_services")[0]
    assert record.approved is False
    assert record.reason == "suspicious"


def test_graph_resume_with_plain_bool_is_accepted(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    guard = make_guard(category="essential_services", logger=logger, approvers=[interrupt_approver])
    graph = _build_graph(guard)
    config = _config()

    graph.invoke({"applicant_id": "A123"}, config)
    resumed = graph.invoke(Command(resume=True), config)

    assert resumed["result"] == "eligible"
    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "langgraph_interrupt"
    assert record.approved is True
