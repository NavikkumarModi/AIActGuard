from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
from ..core.markdown import MarkdownReport
from ..core.questionnaire import Questionnaire, render_field
from ..policy.schema import PolicyConfig


def generate_iso_42001_mapping(
    logger: AuditLogger,
    *,
    questionnaire: Optional[Questionnaire] = None,
    category: Optional[str] = None,
    policy: Optional[PolicyConfig] = None,
) -> str:
    """Map the same evidence AIActGuard already collects onto representative
    ISO/IEC 42001 AI management system clauses. Same evidence as the NIST
    mapping, different structure — useful for orgs pursuing (or evaluating
    readiness for) ISO 42001 certification. Not the certification itself.
    """
    policy = policy or PolicyConfig.default()
    records = logger.query(category=category, limit=10_000)
    summary = summarize(records)

    out = MarkdownReport("ISO/IEC 42001 mapping")

    out.heading("Clause 4 — Context of the organization")
    out.field("System scope", render_field(questionnaire, "system_name", "System name"))
    out.field("Intended purpose", render_field(questionnaire, "intended_purpose", "Intended purpose"))
    out.blank()

    out.heading("Clause 5 — Leadership & policy")
    out.field("AI policy owner", render_field(questionnaire, "policy_owner", "Policy owner"))
    out.blank()

    out.heading("Clause 6 — Risk assessment & treatment")
    out.field("Risk categories in scope", ", ".join(sorted(summary.by_category)) or "none logged yet")
    if policy.gate_rules:
        for rule in policy.gate_rules:
            scope = ", ".join(rule.categories) if rule.categories else "all categories"
            out.bullet(f"Treatment control: human-approval gate at risk tier >= {rule.min_risk_tier.value} ({scope})")
    out.blank()

    out.heading("Clause 8 — Operational controls")
    out.field("Actions logged", summary.total_actions)
    out.field("Gated actions", f"{summary.gated_count} | **Overrides:** {summary.override_count}")
    out.blank()

    out.heading("Clause 9 — Performance evaluation")
    out.field("Denials", summary.denied_count)
    if summary.earliest_timestamp:
        out.field("Evaluation window", f"{summary.earliest_timestamp} to {summary.latest_timestamp}")
    out.blank()

    out.heading("Clause 10 — Improvement")
    out.field("Corrective action process", render_field(questionnaire, "corrective_action_process", "Corrective action process"))
    out.bullet("See `aiactguard.reports.incident_report` and `aiactguard.reports.post_market_monitoring` for the underlying corrective-action inputs.")

    return out.build()
