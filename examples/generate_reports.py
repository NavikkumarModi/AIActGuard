"""Instrument a function with @watch, then generate all five Phase 2
compliance-drafting reports from what got logged.

Requires: pip install aiactguard (no framework extras needed)
"""

from aiactguard import watch
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.reports.conformity_checklist import generate_conformity_checklist
from aiactguard.reports.eu_registration import compile_registration_data
from aiactguard.reports.fria import generate_fria
from aiactguard.reports.post_market_monitoring import generate_post_market_monitoring_plan
from aiactguard.reports.technical_documentation import generate_technical_documentation
from aiactguard.storage.sqlite_store import SQLiteAuditStore

logger = AuditLogger(store=SQLiteAuditStore("reports_demo_audit.db"))


def compliance_officer(ctx: ApprovalContext) -> ApprovalDecision:
    return ApprovalDecision(approved=True, approver_id="compliance_officer")


@watch(category="essential_services", logger=logger, approvers=[compliance_officer])
def check_loan_eligibility(applicant_id: str) -> str:
    return f"Applicant {applicant_id}: eligible"


for applicant_id in ("A123", "A124", "A125"):
    check_loan_eligibility(applicant_id)

questionnaire = {
    "system_name": "Loan Eligibility Assistant",
    "intended_purpose": "Pre-screen loan applicants for a human underwriter's review.",
    "deployment_context": "Retail banking, EU customers.",
    "data_governance_summary": "Applicant data sourced from the core banking system; retained 90 days.",
    "human_oversight_measures": "Compliance officer reviews every gated decision before it reaches the applicant.",
    "deployer_name": "Example Bank N.V.",
    "affected_groups": "Retail loan applicants.",
    "fundamental_rights_at_stake": "Non-discrimination; access to financial services.",
    "provider_name": "Example Bank N.V.",
    "contact_email": "compliance@example-bank.example",
    "review_cadence": "Monthly",
    "monitoring_owner": "Head of Compliance",
}

print(generate_technical_documentation(logger, questionnaire=questionnaire))
print("\n" + "=" * 80 + "\n")
print(generate_conformity_checklist(logger, questionnaire=questionnaire).to_markdown())
print("\n" + "=" * 80 + "\n")
print(generate_fria(logger, questionnaire=questionnaire))
print("\n" + "=" * 80 + "\n")
print(generate_post_market_monitoring_plan(logger, questionnaire=questionnaire))
print("\n" + "=" * 80 + "\n")
print(compile_registration_data(logger, questionnaire=questionnaire).to_markdown())
