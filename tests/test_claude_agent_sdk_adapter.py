import asyncio

from aiactguard.adapters.claude_agent_sdk_adapter import make_pre_tool_use_hook
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_hook_allows_ungated_tool_call(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    hook = make_pre_tool_use_hook(category="general_assistance", logger=logger)

    result = asyncio.run(hook({"tool_name": "summarize", "tool_input": {"doc": "x"}}, "tool-1", None))

    assert result == {}
    records = logger.query(category="general_assistance")
    assert len(records) == 1


def test_hook_denies_gated_tool_call_without_approver(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    hook = make_pre_tool_use_hook(category="essential_services", logger=logger, approvers=[])

    result = asyncio.run(
        hook({"tool_name": "check_loan_eligibility", "tool_input": {"applicant_id": "A123"}}, "tool-1", None)
    )

    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    record = logger.query(category="essential_services")[0]
    assert record.approved is False


def test_hook_allows_gated_tool_call_via_configured_approver(tmp_path):
    def approve(ctx: ApprovalContext) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    hook = make_pre_tool_use_hook(category="essential_services", logger=logger, approvers=[approve])

    result = asyncio.run(
        hook({"tool_name": "check_loan_eligibility", "tool_input": {"applicant_id": "A123"}}, "tool-1", None)
    )

    assert result == {}
    record = logger.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"
