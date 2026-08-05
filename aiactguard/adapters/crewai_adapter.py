from __future__ import annotations

from typing import Any, Callable, Optional

from ..core.approval import Approver
from ..core.audit_logger import AuditLogger
from ..core.guard import GuardCore
from ..core.risk_classifier import RiskClassifier
from ..policy.schema import PolicyConfig


def _extract_tool_call(step: Any) -> tuple[str, str]:
    """Best-effort extraction of (tool_name, tool_input) from a CrewAI step
    object. CrewAI's step-callback payload shape (AgentAction / ToolResult /
    a plain dict, depending on version) isn't stable across releases, so
    this reads defensively instead of importing crewai's types directly."""
    if isinstance(step, dict):
        tool_name = step.get("tool") or step.get("tool_name") or "unknown_tool"
        tool_input = step.get("tool_input") or step.get("input") or ""
    else:
        tool_name = getattr(step, "tool", None) or getattr(step, "tool_name", None) or "unknown_tool"
        tool_input = getattr(step, "tool_input", None) or getattr(step, "input", None) or ""
    return str(tool_name), str(tool_input)


def make_step_callback(
    *,
    category: str = "general_assistance",
    classifier: Optional[RiskClassifier] = None,
    logger: Optional[AuditLogger] = None,
    policy: Optional[PolicyConfig] = None,
    approvers: Optional[list[Approver]] = None,
    model_version: Optional[str] = None,
) -> Callable[[Any], None]:
    """Build a CrewAI `step_callback` that routes each tool call through
    AIActGuard's risk classifier, audit logger, and policy-as-code approval
    gates — no changes to the underlying agent or its tools required.

    Wire it in via `Agent(..., step_callback=guard_callback)` or
    `Crew(..., step_callback=guard_callback)`. Raising `ApprovalRequired`
    inside the callback propagates out of CrewAI's step loop and halts
    that step, which is the current (Phase 1) mechanism for "pausing"
    execution — CrewAI has no native pause/resume hook to route into yet.

    Only steps that carry a tool call are classified/gated; other step
    types (e.g. a plain `AgentFinish`) are ignored.
    """
    guard = GuardCore(
        category=category,
        classifier=classifier,
        logger=logger,
        policy=policy,
        approvers=approvers,
        model_version=model_version,
    )

    def step_callback(step: Any) -> None:
        tool_name, tool_input = _extract_tool_call(step)
        if tool_name == "unknown_tool" and not tool_input:
            return  # not a tool-call step (e.g. AgentFinish) — nothing to gate

        guard.evaluate_and_log(
            action=tool_name,
            text_for_classification=f"{tool_name} {tool_input}",
            inputs={"tool_input": tool_input},
            raise_on_denied=True,
        )

    return step_callback
