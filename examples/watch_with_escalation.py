"""Use the @watch decorator with a two-approver escalation chain, and an
override that must carry a reason.

Requires: pip install aiactguard
"""

from aiactguard import watch
from aiactguard.core.approval import ApprovalContext, ApprovalDecision


def on_call_engineer(ctx: ApprovalContext) -> ApprovalDecision | None:
    # Declines to decide outside business hours — escalates to the next
    # approver in the chain instead of blocking on a human who isn't there.
    return None


def compliance_officer(ctx: ApprovalContext) -> ApprovalDecision:
    # Approves, overriding the gate's default-deny posture, with a reason
    # (required because the default policy sets require_reason_on_override).
    return ApprovalDecision(
        approved=True,
        approver_id="compliance_officer",
        override=True,
        reason="Manually verified applicant identity via phone call.",
    )


@watch(category="essential_services", approvers=[on_call_engineer, compliance_officer])
def check_loan_eligibility(applicant_id: str) -> str:
    return f"Applicant {applicant_id}: eligible"


result = check_loan_eligibility("A123")
print(result)
