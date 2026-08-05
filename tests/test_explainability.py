from aiactguard.core.explainability import format_record
from aiactguard.storage.base import AuditRecord


def test_format_record_includes_decision_and_rationale():
    record = AuditRecord(
        action="check_loan_eligibility",
        category="essential_services",
        risk_tier="high",
        gated=True,
        approved=True,
        approver_id="compliance_officer",
        override=True,
        reason="Manually verified applicant identity via phone call.",
        rationale=[{"source": "agent_scratchpad", "text": "Applicant matched KYC record."}],
    )

    report = format_record(record)

    assert "check_loan_eligibility" in report
    assert "compliance_officer" in report
    assert "Manually verified applicant identity via phone call." in report
    assert "Applicant matched KYC record." in report
    assert "approved" in report


def test_format_record_handles_ungated_action_without_rationale():
    record = AuditRecord(
        action="summarize",
        category="general_assistance",
        risk_tier="limited",
        gated=False,
        approved=True,
    )

    report = format_record(record)

    assert "summarize" in report
    assert "Gated:** no" in report
