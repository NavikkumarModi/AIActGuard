"""Validates make_pre_tool_use_hook against claude_agent_sdk's real typed
hook input/output shapes (PreToolUseHookInput, HookContext, and
SyncHookJSONOutput's hookSpecificOutput field) rather than the hand-built
dicts used in tests/test_claude_agent_sdk_adapter.py. These are all
TypedDicts (plain dicts at runtime), confirmed by inspecting
claude_agent_sdk.types directly, so this cross-checks field names
(tool_name/tool_input, permissionDecision/permissionDecisionReason)
against the installed SDK's actual contract without needing a live
query() call (which needs an Anthropic API key/CLI this environment
doesn't have).
"""

import asyncio

import pytest

claude_agent_sdk = pytest.importorskip("claude_agent_sdk")

from claude_agent_sdk.types import HookContext, PreToolUseHookInput  # noqa: E402

from aiactguard.adapters.claude_agent_sdk_adapter import make_pre_tool_use_hook  # noqa: E402
from aiactguard.core.approval import ApprovalContext, ApprovalDecision  # noqa: E402
from aiactguard.core.audit_logger import AuditLogger  # noqa: E402
from aiactguard.storage.sqlite_store import SQLiteAuditStore  # noqa: E402


def _logger(tmp_path):
    return AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))


def _input_data(**overrides) -> PreToolUseHookInput:
    base: PreToolUseHookInput = {
        "session_id": "s1",
        "transcript_path": "/tmp/transcript",
        "cwd": "/tmp",
        "permission_mode": "default",
        "agent_id": "a1",
        "agent_type": "main",
        "hook_event_name": "PreToolUse",
        "tool_name": "check_loan_eligibility",
        "tool_input": {"applicant_id": "A123"},
        "tool_use_id": "tu1",
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


def _context() -> HookContext:
    return {"signal": None}


def test_real_typed_input_allows_and_logs_when_approved(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = _logger(tmp_path)
    hook = make_pre_tool_use_hook(category="essential_services", logger=logger, approvers=[approve])

    result = asyncio.run(hook(_input_data(), "tu1", _context()))

    assert result == {}
    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"


def test_real_typed_input_denies_with_correct_output_shape(tmp_path):
    logger = _logger(tmp_path)
    hook = make_pre_tool_use_hook(category="essential_services", logger=logger, approvers=[])

    result = asyncio.run(hook(_input_data(), "tu1", _context()))

    output = result["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert "permissionDecisionReason" in output
