"""The script used to record the README demo — also runnable standalone to
see the full flow yourself. Everything below actually executes: two real
gate decisions through the LangChain adapter (one approved, one denied),
real audit records written to SQLite, and a real report generated from
that audit trail. The only "scripted" part is the pacing (time.sleep
between narration lines) and that the approvers are canned functions
playing the reviewer's role for the recording, rather than a live human
typing an answer — a real deployment would swap them for `input()`-driven
approval (see examples/langchain_quickstart.py) or a real reviewer's
decision.

Requires: pip install aiactguard[langchain]
"""

import sys
import time

from langchain_core.tools import tool

from aiactguard.adapters.langchain_adapter import AIActGuardCallbackHandler
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.policy.schema import ApprovalRequired, PolicyConfig
from aiactguard.reports.conformity_checklist import generate_conformity_checklist
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def narrate(text: str, pause: float = 1.0) -> None:
    print(text)
    sys.stdout.flush()
    time.sleep(pause)


@tool
def check_loan_eligibility(applicant_id: str) -> str:
    """Check whether an applicant is eligible for a loan."""
    return f"Applicant {applicant_id}: eligible"


def compliance_officer_approves(ctx: ApprovalContext) -> ApprovalDecision:
    narrate(f"  >> GATE TRIGGERED: '{ctx.action}' classified as {ctx.risk_tier.value} risk", 1.2)
    narrate("     routing to compliance_officer for approval...", 1.3)
    narrate("     compliance_officer: reviewing applicant A123's request...", 1.3)
    narrate("     compliance_officer: APPROVED\n", 1.1)
    return ApprovalDecision(approved=True, approver_id="compliance_officer")


def compliance_officer_denies(ctx: ApprovalContext) -> ApprovalDecision:
    narrate(f"  >> GATE TRIGGERED: '{ctx.action}' classified as {ctx.risk_tier.value} risk", 1.2)
    narrate("     routing to compliance_officer for approval...", 1.3)
    narrate("     compliance_officer: reviewing applicant B456's request...", 1.3)
    narrate("     compliance_officer: applicant ID does not match records on file", 1.3)
    narrate("     compliance_officer: DENIED\n", 1.1)
    return ApprovalDecision(
        approved=False,
        approver_id="compliance_officer",
        reason="Applicant ID does not match records on file.",
    )


def main() -> None:
    narrate("$ python examples/demo.py", 0.5)
    narrate("# Two gated tool calls through the LangChain adapter: one approved, one denied\n", 1.0)

    narrate(">>> policy.register_action('check_loan_eligibility', 'irreversible_financial')")
    policy = PolicyConfig.default()
    policy.register_action("check_loan_eligibility", "irreversible_financial")
    narrate("    (no default allowed here — this must be declared explicitly)\n", 1.2)

    logger = AuditLogger(store=SQLiteAuditStore("demo_audit.db"))

    # === Scenario 1: a legitimate applicant, approved ===
    narrate(">>> SCENARIO 1: a legitimate applicant\n", 0.9)
    approving_handler = AIActGuardCallbackHandler(
        category="essential_services", logger=logger, policy=policy, approvers=[compliance_officer_approves]
    )
    narrate(">>> agent calls check_loan_eligibility('A123')...", 0.9)
    result = check_loan_eligibility.run("A123", callbacks=[approving_handler])
    narrate(f"<<< tool result: {result}\n", 1.2)

    approved_record = logger.query(category="essential_services")[0]
    narrate(">>> audit record written (append-only, Art. 12):")
    narrate(
        f"    action={approved_record.action}  risk_tier={approved_record.risk_tier}  "
        f"confidence={approved_record.classifier_confidence}"
    )
    narrate(f"    exposure_class={approved_record.action_exposure_class}")
    narrate(f"    approver={approved_record.approver_id}  approved={approved_record.approved}\n", 1.5)

    # === Scenario 2: a flagged applicant, denied — the tool never runs ===
    narrate(">>> SCENARIO 2: a flagged applicant\n", 0.9)
    denying_handler = AIActGuardCallbackHandler(
        category="essential_services", logger=logger, policy=policy, approvers=[compliance_officer_denies]
    )
    narrate(">>> agent calls check_loan_eligibility('B456')...", 0.9)
    narrate("    (LangChain logs a warning below when the callback raises — that's the", 0.9)
    narrate("     denial genuinely propagating through LangChain's own internals)", 1.2)
    try:
        check_loan_eligibility.run("B456", callbacks=[denying_handler])
    except ApprovalRequired:
        narrate("<<< BLOCKED — the tool call never executed\n", 1.4)

    denied_record = [r for r in logger.query(category="essential_services") if not r.approved][0]
    narrate(">>> audit record for the blocked attempt:")
    narrate(f"    action={denied_record.action}  approved={denied_record.approved}")
    narrate(f"    approver={denied_record.approver_id}")
    narrate(f"    reason={denied_record.reason}\n", 1.6)

    # === Report generated from both records ===
    narrate(">>> generating a conformity readiness checklist from this audit trail...\n", 1.1)
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
