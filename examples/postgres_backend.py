"""Use PostgresAuditStore instead of the SQLite default — the production
storage backend for high-volume concurrent agents.

Requires: pip install aiactguard[postgres]
Requires: a reachable Postgres database — set AIACTGUARD_POSTGRES_DSN, or
this defaults to "postgresql:///aiactguard_demo" (a local database you'll
need to create first: `createdb aiactguard_demo`).
"""

import os

from aiactguard import watch
from aiactguard.core.approval import ApprovalContext, ApprovalDecision
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.storage.postgres_store import PostgresAuditStore

dsn = os.environ.get("AIACTGUARD_POSTGRES_DSN", "postgresql:///aiactguard_demo")
logger = AuditLogger(store=PostgresAuditStore(dsn))


def compliance_officer(ctx: ApprovalContext) -> ApprovalDecision:
    return ApprovalDecision(approved=True, approver_id="compliance_officer")


@watch(category="essential_services", logger=logger, approvers=[compliance_officer])
def check_loan_eligibility(applicant_id: str) -> str:
    return f"Applicant {applicant_id}: eligible"


result = check_loan_eligibility("A123")
print(result)

records = logger.query(category="essential_services")
print(f"{len(records)} record(s) in Postgres:")
for record in records:
    print(f"  {record.action} — approved={record.approved} approver={record.approver_id}")
