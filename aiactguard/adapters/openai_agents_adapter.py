from __future__ import annotations

import asyncio
from typing import Any, Optional

try:
    from agents import RunHooks
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The OpenAI Agents SDK adapter requires the 'openai-agents' extra: "
        "pip install aiactguard[openai-agents]"
    ) from exc

from ..core.approval import Approver
from ..core.audit_logger import AuditLogger
from ..core.guard import GuardCore
from ..core.risk_classifier import RiskClassifier
from ..policy.schema import PolicyConfig


class AIActGuardRunHooks(RunHooks):
    """OpenAI Agents SDK `RunHooks` that route each local tool call through
    AIActGuard's risk classifier, audit logger, and policy-as-code approval
    gates — no changes to the underlying agent or its tools required.

    Usage:
        result = await Runner.run(
            agent, "...", hooks=AIActGuardRunHooks(category="essential_services", approvers=[...])
        )

    Denial raises `ApprovalRequired` from `on_tool_start`. Verified against
    a real `Runner.run()` call (with a fake `Model`, no API key needed)
    that the SDK's tool-execution machinery does not swallow this — it
    catches and re-raises it wrapped in `agents.exceptions.UserError`.
    Catch `agents.exceptions.UserError` (or its `AgentsException` base)
    around `Runner.run()`, not `ApprovalRequired` directly.

    The SDK also has its own native tool-approval primitive (mark a tool
    `needs_approval=True`, inspect `RunResult.interruptions`, resume via
    `ToolContext.approve_tool`/`reject_tool`) — a LangGraph-`interrupt()`-
    style mechanism. This adapter doesn't use it because it requires
    redeclaring each tool as `needs_approval=True`, which isn't a drop-in
    integration; `RunHooks` observes every tool call without touching how
    tools are defined, consistent with every other adapter in this project.
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

    async def on_tool_start(self, context: Any, agent: Any, tool: Any) -> None:
        tool_name = getattr(tool, "name", None) or getattr(context, "tool_name", "unknown_tool")
        tool_arguments = getattr(context, "tool_arguments", "")

        # GuardCore does a blocking SQLite write; running it in a thread
        # keeps this coroutine from stalling the event loop on every gated
        # tool call (same fix applied to the Claude Agent SDK adapter).
        await asyncio.to_thread(
            self.guard.evaluate_and_log,
            action=tool_name,
            text_for_classification=f"{tool_name} {tool_arguments}",
            inputs={"tool_arguments": tool_arguments, "tool_call_id": getattr(context, "tool_call_id", None)},
            raise_on_denied=True,
        )

    async def on_tool_end(self, context: Any, agent: Any, tool: Any, result: object) -> None:
        # The gate decision is logged on tool start, the only point at
        # which execution can still be stopped; tool output isn't
        # correlated back into that record, matching the LangChain and
        # Claude Agent SDK adapters.
        pass
