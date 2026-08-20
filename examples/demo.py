"""The script used to record the README demo — also runnable standalone to
see the full flow yourself. Everything below actually executes: a real
gate decision through the LangChain adapter, a real audit record written
to SQLite, and a real report generated from that audit trail. The only
"scripted" part is the pacing (time.sleep between narration lines) and
that the approver is a canned function playing the reviewer's role for
the recording, rather than a live human typing an answer — a real
deployment would swap it for `input()`-driven approval (see
examples/langchain_quickstart.py) or a real reviewer's decision.

Requires: pip install aiactguard[langchain]
"""

import sys
import time

from langchain_core.tools import tool

from aiactguard.adapters.langchain_adapter import AIActGuardCallbackHandler
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.policy.schema import PolicyConfig
from aiactguard.reports.conformity_checklist import generate_conformity_checklist
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def narrate(text: str, pause: float = 1.1) -> None:
    print(text)
    sys.stdout.flush()
    time.sleep(pause)


@tool
def check_loan_eligibility(applicant_id: str) -> str:
    """Check whether an applicant is eligible for a loan."""
    return f"Applicant {applicant_id}: eligible"


def compliance_officer_review(ctx: ApprovalContext) -> ApprovalDecision:
    narrate(f"  >> GATE TRIGGERED: '{ctx.action}' classified as {ctx.risk_tier.value} risk", 1.3)
    narrate("     routing to compliance_officer for approval...", 1.4)
    narrate("     compliance_officer: reviewing applicant A123's request...", 1.4)
    narrate("     compliance_officer: APPROVED\n", 1.2)
    return ApprovalDecision(approved=True, approver_id="compliance_officer")


def main() -> None:
    narrate("$ python examples/demo.py", 0.6)
    narrate("# A gated tool call through the LangChain adapter, start to finish\n", 1.0)

    narrate(">>> policy.register_action('check_loan_eligibility', 'irreversible_financial')")
    policy = PolicyConfig.default()
    policy.register_action("check_loan_eligibility", "irreversible_financial")
    narrate("    (no default allowed here — this must be declared explicitly)\n", 1.3)

    logger = AuditLogger(store=SQLiteAuditStore("demo_audit.db"))
    handler = AIActGuardCallbackHandler(
        category="essential_services", logger=logger, policy=policy, approvers=[compliance_officer_review]
    )

    narrate(">>> agent calls check_loan_eligibility('A123')...", 1.0)
    result = check_loan_eligibility.run("A123", callbacks=[handler])
    narrate(f"<<< tool result: {result}\n", 1.3)

    record = logger.query(category="essential_services")[0]
    narrate(">>> audit record written (append-only, Art. 12):")
    narrate(f"    action={record.action}  risk_tier={record.risk_tier}  confidence={record.classifier_confidence}")
    narrate(f"    exposure_class={record.action_exposure_class}")
    narrate(f"    approver={record.approver_id}  approved={record.approved}\n", 1.6)

    narrate(">>> generating a conformity readiness checklist from this audit trail...\n", 1.2)
    checklist = generate_conformity_checklist(
        logger,
        questionnaire={
            "system_name": "Loan Eligibility Assistant",
            "intended_purpose": "Pre-screen loan applicants for a human underwriter's review.",
            "data_governance_summary": "Applicant data sourced from the core banking system.",
        },
    )
    print(checklist.to_markdown())


if __name__ == "__main__":
    main()
