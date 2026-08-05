"""Draft a serious incident report from a denied gate, and a GPAI
transparency card from logged model usage.

Requires: pip install aiactguard (no framework extras needed)
"""

from aiactguard import watch
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.reports.gpai_transparency_card import generate_gpai_transparency_card
from aiactguard.reports.incident_report import draft_incident_report
from aiactguard.storage.sqlite_store import SQLiteAuditStore

logger = AuditLogger(store=SQLiteAuditStore("incident_demo_audit.db"))


@watch(category="essential_services", logger=logger, approvers=[], model_version="internal-loan-screening-v1")
def check_loan_eligibility(applicant_id: str) -> str:
    return f"Applicant {applicant_id}: eligible"

try:
    check_loan_eligibility("A999")
except Exception:
    pass  # the denial is what we want logged — see incident report below

denied_record = next(r for r in logger.query(category="essential_services") if not r.approved)

incident_questionnaire = {
    "incident_description": "Loan eligibility check for applicant A999 was denied because no approver was configured for the essential_services gate.",
    "harm_caused": "None — the applicant's request was simply not processed; no incorrect decision was made.",
    "affected_persons": "Applicant A999.",
    "root_cause": "The essential_services gate was deployed without an approver/escalation chain configured.",
    "corrective_actions": "Configure at least one approver for essential_services before re-enabling this integration.",
}

print(draft_incident_report(denied_record, questionnaire=incident_questionnaire))
print("\n" + "=" * 80 + "\n")

transparency_questionnaire = {
    "model_name": "internal-loan-screening-v1",
    "provider": "Example Bank N.V. (in-house)",
    "capabilities": "Rule-based eligibility pre-screening from applicant metadata.",
    "known_limitations": "Does not account for applicants with no prior credit history.",
    "known_risks": "May systematically under-approve thin-file applicants; see the fairness scan example.",
}

print(generate_gpai_transparency_card(logger, questionnaire=transparency_questionnaire))
