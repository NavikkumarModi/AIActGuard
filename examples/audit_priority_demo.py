"""Prioritize human audit attention using the confidence-sequence method
from the user's own research on adaptively-routed agent systems, and
generate the accompanying drift diagnostic report — both read-only over
an existing audit trail. Neither approves, blocks, or skips review for
anything; they only rank what a reviewer should look at first and
surface where risk is concentrating.

Requires: pip install aiactguard[audit-priority]
"""

from aiactguard.audit_priority.findings import AuditFindingStore
from aiactguard.audit_priority.priority import prioritize_for_review
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.reports.drift_diagnostic import generate_drift_diagnostic
from aiactguard.storage.sqlite_store import SQLiteAuditStore

db_path = "audit_priority_demo.db"
logger = AuditLogger(store=SQLiteAuditStore(db_path))
findings = AuditFindingStore(db_path)

# Seed a small audit trail. A real deployment accumulates this over time
# from normal traffic via watch()/an adapter (see
# examples/langchain_quickstart.py); here we log directly with enough
# volume in two bins to actually cross the 5-finding threshold and show
# the ranking differentiate, rather than everything sitting at "not
# enough evidence yet."

risky_ids, safe_ids = [], []

# A high-confidence bin (0.85) where review has found real problems:
# 16 of 20 reviewed so far were true violations, and half of those slipped
# past the gate uncaught (gated=False).
for i in range(20):
    record = logger.log(
        action=f"risky_call_{i}",
        category="essential_services",
        risk_tier="high",
        classifier_confidence=0.85,
        action_exposure_class="irreversible_financial",
        gated=(i % 2 == 0),  # half caught by the gate, half not
        approved=True,
    )
    risky_ids.append(record.record_id)
    findings.record(record.record_id, is_true_violation=i < 16)

# A low-confidence bin (0.15) that's looked safe on every review so far.
for i in range(20):
    record = logger.log(
        action=f"safe_call_{i}",
        category="essential_services",
        risk_tier="minimal",
        classifier_confidence=0.15,
        gated=False,
        approved=True,
    )
    safe_ids.append(record.record_id)
    findings.record(record.record_id, is_true_violation=False)

# A couple of records nobody's reviewed yet — these should rank at the
# very top regardless of confidence, since "no evidence" is the maximal
# uncertainty case, not a free pass.
for i, confidence in enumerate([0.5, 0.55]):
    logger.log(
        action=f"unreviewed_call_{i}",
        category="essential_services",
        risk_tier="limited",
        classifier_confidence=confidence,
        gated=False,
        approved=True,
    )

print("=== Prioritized review queue (highest uncertainty first) ===\n")
ranked = prioritize_for_review(logger.query(limit=100), findings)
for item in ranked[:8]:
    reviewed = "reviewed" if item.already_reviewed else "NOT YET REVIEWED"
    print(f"bin={item.bin:>2}  ucb={item.ucb:.3f}  action={item.record.action:<20} ({reviewed})")
print(f"... {len(ranked) - 8} more")

print("\n=== Drift diagnostic ===\n")
print(generate_drift_diagnostic(logger, findings, questionnaire={"system_name": "Loan Eligibility Assistant"}))
