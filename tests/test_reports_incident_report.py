from aiactguard.reports.incident_report import draft_incident_report
from aiactguard.storage.base import AuditRecord


def test_missing_questionnaire_fields_are_flagged():
    record = AuditRecord(action="check_loan_eligibility", category="essential_services", risk_tier="high", approved=False, gated=True)
    report = draft_incident_report(record, questionnaire={})

    assert "required field(s) missing" in report
    assert "NEEDS INPUT: What happened" in report


def test_report_includes_override_and_reason():
    record = AuditRecord(
        action="check_loan_eligibility",
        category="essential_services",
        risk_tier="high",
        approved=True,
        gated=True,
        approver_id="compliance_officer",
        override=True,
        reason="Manually verified applicant identity via phone call.",
    )
    report = draft_incident_report(
        record,
        questionnaire={
            "incident_description": "Override used to approve a flagged applicant.",
            "harm_caused": "None.",
            "affected_persons": "Applicant A123.",
            "root_cause": "Automated check flagged a false positive.",
            "corrective_actions": "Tune the risk taxonomy.",
        },
    )

    assert "compliance_officer" in report
    assert "Manually verified applicant identity via phone call." in report
    assert "Override used to approve a flagged applicant." in report
