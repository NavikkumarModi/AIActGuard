"""Wrap a Claude Agent SDK session with AIActGuard.

Requires: pip install aiactguard claude-agent-sdk

The Claude Agent SDK's hook API has changed shape across releases — verify
`HookMatcher` / `ClaudeAgentOptions` field names against your installed
version if this doesn't run as-is.
"""

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, query

from aiactguard.adapters.claude_agent_sdk_adapter import make_pre_tool_use_hook
from aiactguard.core.approval import ApprovalContext, ApprovalDecision


def prompt_approver(ctx: ApprovalContext) -> ApprovalDecision:
    approved = input(f"Approve {ctx.action} ({ctx.risk_tier.value})? [y/N] ").lower() == "y"
    return ApprovalDecision(approved=approved, approver_id="cli-operator")


# essential_services is a high-risk Annex III category by default, so this
# gate requires human approval before the tool call fires.
guard_hook = make_pre_tool_use_hook(
    category="essential_services",
    approvers=[prompt_approver],
)

options = ClaudeAgentOptions(
    hooks={"PreToolUse": [HookMatcher(hooks=[guard_hook])]},
)


async def main() -> None:
    async for message in query(prompt="Check loan eligibility for applicant A123", options=options):
        print(message)


asyncio.run(main())
