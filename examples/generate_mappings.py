"""Generate NIST AI RMF and ISO/IEC 42001 mappings from an audit trail
seeded via @watch — the same evidence, viewed through two frameworks.

Requires: pip install aiactguard (no framework extras needed)
"""

from aiactguard import watch
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.mappings.iso_42001 import generate_iso_42001_mapping
from aiactguard.mappings.nist_ai_rmf import generate_nist_ai_rmf_mapping
from aiactguard.storage.sqlite_store import SQLiteAuditStore

logger = AuditLogger(store=SQLiteAuditStore("mappings_demo_audit.db"))


def compliance_officer(ctx: ApprovalContext) -> ApprovalDecision:
    return ApprovalDecision(approved=True, approver_id="compliance_officer")


@watch(category="essential_services", logger=logger, approvers=[compliance_officer])
def check_loan_eligibility(applicant_id: str) -> str:
    return f"Applicant {applicant_id}: eligible"


for applicant_id in ("A123", "A124"):
    check_loan_eligibility(applicant_id)

questionnaire = {
    "policy_owner": "Head of Compliance",
    "system_name": "Loan Eligibility Assistant",
    "intended_purpose": "Pre-screen loan applicants for a human underwriter's review.",
    "incident_response_process": "See INCIDENT_RESPONSE.md.",
    "corrective_action_process": "Tracked in the compliance team's Jira project.",
}

print(generate_nist_ai_rmf_mapping(logger, questionnaire=questionnaire))
print("\n" + "=" * 80 + "\n")
print(generate_iso_42001_mapping(logger, questionnaire=questionnaire))
