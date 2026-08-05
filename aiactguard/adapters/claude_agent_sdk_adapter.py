from __future__ import annotations

from typing import Any, Optional

from ..core.approval import Approver
from ..core.audit_logger import AuditLogger
from ..core.guard import GuardCore
from ..core.risk_classifier import RiskClassifier
from ..policy.schema import ApprovalRequired, PolicyConfig


def make_pre_tool_use_hook(
    *,
    category: str = "general_assistance",
    classifier: Optional[RiskClassifier] = None,
    logger: Optional[AuditLogger] = None,
    policy: Optional[PolicyConfig] = None,
    approvers: Optional[list[Approver]] = None,
    model_version: Optional[str] = None,
):
    """Build a `PreToolUse` hook for the Claude Agent SDK that routes each
    tool call through AIActGuard's risk classifier, audit logger, and
    policy-as-code approval gates.

    Wire it in via:
        ClaudeAgentOptions(
            hooks={"PreToolUse": [HookMatcher(hooks=[make_pre_tool_use_hook(category=...)])]}
        )

    This module intentionally does not import `claude_agent_sdk` — the hook
    is a plain async callable matching the SDK's documented `PreToolUse`
    signature (`input_data: dict, tool_use_id: str | None, context`) and
    returns a plain dict, so it has no hard dependency and stays usable even
    if you're pinned to an older/newer SDK release. Verify the returned
    `hookSpecificOutput` shape against your installed `claude-agent-sdk`
    version — this is the part of the SDK's API most likely to shift.
    """
    guard = GuardCore(
        category=category,
        classifier=classifier,
        logger=logger,
        policy=policy,
        approvers=approvers,
        model_version=model_version,
    )

    async def hook(input_data: dict, tool_use_id: Optional[str], context: Any) -> dict:
        tool_name = input_data.get("tool_name", "unknown_tool")
        tool_input = input_data.get("tool_input", {})

        try:
            guard.evaluate_and_log(
                action=tool_name,
                text_for_classification=f"{tool_name} {tool_input}",
                inputs={"tool_input": tool_input, "tool_use_id": tool_use_id},
                raise_on_denied=True,
            )
        except ApprovalRequired as exc:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": str(exc),
                }
            }

        return {}

    return hook
