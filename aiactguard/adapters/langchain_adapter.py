from __future__ import annotations

from typing import Any, Optional

try:
    from langchain_core.agents import AgentAction
    from langchain_core.callbacks.base import BaseCallbackHandler
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The LangChain adapter requires the 'langchain' extra: "
        "pip install aiactguard[langchain]"
    ) from exc

from ..core.approval import Approver
from ..core.audit_logger import AuditLogger
from ..core.guard import GuardCore
from ..core.risk_classifier import RiskClassifier
from ..policy.schema import PolicyConfig


class AIActGuardCallbackHandler(BaseCallbackHandler):
    """LangChain callback that routes every tool call through AIActGuard's
    risk classifier, audit logger, and policy-as-code approval gates —
    no changes to the underlying agent or its tools required.

    Also captures the agent's chain-of-thought for each tool call (the
    `.log` text LangChain attaches to `AgentAction`) as explainability
    rationale (Art. 13) on the corresponding audit record.

    Usage:
        guard = AIActGuardCallbackHandler(
            category="essential_services",
            approvers=[team_lead_approver, compliance_officer_approver],
        )
        agent_executor.invoke({"input": "..."}, config={"callbacks": [guard]})
    """

    # LangChain's CallbackManager swallows exceptions raised inside a
    # callback by default (it only logs a warning) unless the handler opts
    # in via this flag. Without it, ApprovalRequired would never actually
    # stop a gated tool call from executing — verified against a real
    # langchain_core callback dispatch, not just a unit-test stub.
    raise_error = True

    def __init__(
        self,
        *,
        category: str = "general_assistance",
        classifier: Optional[RiskClassifier] = None,
        logger: Optional[AuditLogger] = None,
        policy: Optional[PolicyConfig] = None,
        approvers: Optional[list[Approver]] = None,
        model_version: Optional[str] = None,
    ):
        self.guard = GuardCore(
            category=category,
            classifier=classifier,
            logger=logger,
            policy=policy,
            approvers=approvers,
            model_version=model_version,
        )
        self._pending_rationale: Optional[str] = None

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        self._pending_rationale = getattr(action, "log", None)

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        rationale = None
        if self._pending_rationale:
            rationale = [{"source": "agent_scratchpad", "text": self._pending_rationale}]
            self._pending_rationale = None

        self.guard.evaluate_and_log(
            action=tool_name,
            text_for_classification=f"{tool_name} {input_str}",
            inputs={"input_str": input_str},
            rationale=rationale,
            raise_on_denied=True,
        )

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        # The gate decision + rationale are logged on tool start, which is
        # the only point at which execution can still be stopped; tool
        # output isn't correlated back into that record in Phase 1.
        pass
