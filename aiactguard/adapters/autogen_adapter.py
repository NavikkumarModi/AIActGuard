from __future__ import annotations

from typing import Any, Optional

try:
    from autogen_core import FunctionCall
    from autogen_core.tool_agent import ToolException
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The AutoGen adapter requires the 'autogen' extra: "
        "pip install aiactguard[autogen]"
    ) from exc

from ..core.approval import Approver
from ..core.audit_logger import AuditLogger
from ..core.guard import GuardCore
from ..core.risk_classifier import RiskClassifier
from ..policy.schema import ApprovalRequired, PolicyConfig


class AIActGuardInterventionHandler:
    """AutoGen Core intervention handler that routes each tool call (a
    `FunctionCall` message) through AIActGuard's risk classifier, audit
    logger, and policy-as-code approval gates — no changes to the
    underlying agent or its tools required.

    Wire it in via:
        from autogen_core import SingleThreadedAgentRuntime
        runtime = SingleThreadedAgentRuntime(
            intervention_handlers=[AIActGuardInterventionHandler(category="essential_services")]
        )

    On denial, raises `autogen_core.tool_agent.ToolException` — the same
    exception AutoGen's own tool-approval cookbook uses — rather than
    returning `DropMessage`, so the caller gets an actual reason instead of
    a silent drop.

    Implements the `InterventionHandler` protocol structurally
    (`on_send`/`on_publish`/`on_response`); doesn't subclass it since it's
    a `typing.Protocol`, not a base class.
    """

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

    async def on_send(self, message: Any, *, message_context: Any, recipient: Any) -> Any:
        if isinstance(message, FunctionCall):
            try:
                self.guard.evaluate_and_log(
                    action=message.name,
                    text_for_classification=f"{message.name} {message.arguments}",
                    inputs={"arguments": message.arguments, "call_id": message.id},
                    raise_on_denied=True,
                )
            except ApprovalRequired as exc:
                raise ToolException(call_id=message.id, content=str(exc), name=message.name) from exc
        return message

    async def on_publish(self, message: Any, *, message_context: Any) -> Any:
        return message

    async def on_response(self, message: Any, *, sender: Any, recipient: Any) -> Any:
        return message
