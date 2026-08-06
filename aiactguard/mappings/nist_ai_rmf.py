from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
from ..core.markdown import MarkdownReport
from ..core.questionnaire import Questionnaire, render_field
from ..policy.schema import PolicyConfig


def generate_nist_ai_rmf_mapping(
    logger: AuditLogger,
    *,
    questionnaire: Optional[Questionnaire] = None,
    category: Optional[str] = None,
    policy: Optional[PolicyConfig] = None,
) -> str:
    """Map the evidence AIActGuard already collects onto NIST AI RMF's four
    functions (Govern, Map, Measure, Manage). This re-buckets existing
    audit-trail and policy-as-code evidence under NIST's structure — it
    doesn't add new controls and it isn't a certification against the
    framework, only a way to see what you already have in NIST's terms.
    Widens the addressable audience to US enterprises without EU exposure.
    """
    policy = policy or PolicyConfig.default()
    records = logger.query(category=category, limit=10_000)
    summary = summarize(records)

    out = MarkdownReport("NIST AI RMF mapping")

    out.heading("Govern")
    out.field("Policy owner", render_field(questionnaire, "policy_owner", "Policy owner"))
    if policy.gate_rules:
        for rule in policy.gate_rules:
            scope = ", ".join(rule.categories) if rule.categories else "all categories"
            out.bullet(f"Human-approval gate policy configured: risk tier >= {rule.min_risk_tier.value} ({scope})")
    else:
        out.bullet("No gate rules configured — Govern function has no policy-as-code evidence yet.")
    out.blank()

    out.heading("Map")
    out.field("Risk categories observed", ", ".join(sorted(summary.by_category)) or "none logged yet")
    out.field("Risk tiers observed", summary.by_risk_tier or "none logged yet")
    out.blank()

    out.heading("Measure")
    out.field("Actions logged", summary.total_actions)
    out.field("Gated actions", f"{summary.gated_count} | **Denied:** {summary.denied_count} | **Overrides:** {summary.override_count}")
    if summary.earliest_timestamp:
        out.field("Measurement window", f"{summary.earliest_timestamp} to {summary.latest_timestamp}")
    out.blank()

    out.heading("Manage")
    out.field("Incident response process", render_field(questionnaire, "incident_response_process", "Incident response process"))
    out.field("Overrides requiring a reason", f"{sum(1 for r in policy.gate_rules if r.require_reason_on_override)}/{len(policy.gate_rules)} gate rule(s)")
    out.bullet("See `aiactguard.reports.incident_report` for drafting incident reports from flagged records.")

    return out.build()
