from __future__ import annotations

from typing import Any, Optional

from ..core.approval import ApprovalContext, ApprovalDecision, Approver
from ..core.audit_logger import AuditLogger
from ..core.guard import GuardCore
from ..core.risk_classifier import RiskClassifier
from ..policy.schema import PolicyConfig


def interrupt_approver(context: ApprovalContext) -> ApprovalDecision:
    """An `Approver` that pauses graph execution via LangGraph's own
    `interrupt()` primitive and resumes with whatever decision a human
    supplies via `Command(resume=...)` — the framework's real human-in-
    the-loop mechanism, not a generic callback. Requires the graph to be
    compiled with a checkpointer (that's `interrupt()`'s own requirement).

    Drop this into `make_guard(..., approvers=[interrupt_approver])`, or
    combine it with other approvers in an escalation chain (e.g. an
    automated approver first, falling back to a human via interrupt).

    The resume value can be a bool, or a dict with approved/approver_id/
    reason/override keys for full control — e.g. to record a reasoned
    override.

    `langgraph` is imported lazily inside this function, not at module
    load time, so `aiactguard.adapters.langgraph_adapter` stays importable
    without `langgraph` installed unless you actually use this approver.
    """
    from langgraph.types import interrupt

    response = interrupt(
        {
            "action": context.action,
            "category": context.category,
            "risk_tier": context.risk_tier.value,
            "payload": context.payload,
        }
    )

    if isinstance(response, bool):
        return ApprovalDecision(approved=response, approver_id="langgraph_interrupt")

    return ApprovalDecision(
        approved=bool(response.get("approved")),
        approver_id=response.get("approver_id", "langgraph_interrupt"),
        reason=response.get("reason"),
        override=bool(response.get("override", False)),
    )


def make_guard(
    *,
    category: str = "general_assistance",
    classifier: Optional[RiskClassifier] = None,
    logger: Optional[AuditLogger] = None,
    policy: Optional[PolicyConfig] = None,
    approvers: Optional[list[Approver]] = None,
    model_version: Optional[str] = None,
):
    """Build a guard callable for use inside a LangGraph node function.

    LangGraph nodes are plain Python functions — there's no universal
    "before every tool call" hook the way LangChain has — so unlike the
    other adapters, you call the returned function yourself at the point
    in your node where the risky action is about to happen.

    Usage:
        guard = make_guard(category="essential_services", approvers=[interrupt_approver])

        def check_eligibility_node(state):
            guard("check_loan_eligibility", inputs={"applicant_id": state["applicant_id"]})
            return {"eligible": True}
    """
    core = GuardCore(
        category=category,
        classifier=classifier,
        logger=logger,
        policy=policy,
        approvers=approvers,
        model_version=model_version,
    )

    def guard_step(
        action: str,
        *,
        text_for_classification: Optional[str] = None,
        inputs: Optional[dict[str, Any]] = None,
    ) -> None:
        core.evaluate_and_log(
            action=action,
            text_for_classification=text_for_classification or action,
            inputs=inputs,
            raise_on_denied=True,
        )

    return guard_step
