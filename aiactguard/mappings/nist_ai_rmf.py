from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
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

    lines = ["# NIST AI RMF mapping", ""]

    lines.append("## Govern")
    lines.append(f"- **Policy owner:** {render_field(questionnaire, 'policy_owner', 'Policy owner')}")
    if policy.gate_rules:
        for rule in policy.gate_rules:
            scope = ", ".join(rule.categories) if rule.categories else "all categories"
            lines.append(f"- Human-approval gate policy configured: risk tier >= {rule.min_risk_tier.value} ({scope})")
    else:
        lines.append("- No gate rules configured — Govern function has no policy-as-code evidence yet.")
    lines.append("")

    lines.append("## Map")
    lines.append(f"- **Risk categories observed:** {', '.join(sorted(summary.by_category)) or 'none logged yet'}")
    lines.append(f"- **Risk tiers observed:** {summary.by_risk_tier or 'none logged yet'}")
    lines.append("")

    lines.append("## Measure")
    lines.append(f"- **Actions logged:** {summary.total_actions}")
    lines.append(f"- **Gated actions:** {summary.gated_count} | **Denied:** {summary.denied_count} | **Overrides:** {summary.override_count}")
    if summary.earliest_timestamp:
        lines.append(f"- **Measurement window:** {summary.earliest_timestamp} to {summary.latest_timestamp}")
    lines.append("")

    lines.append("## Manage")
    lines.append(f"- **Incident response process:** {render_field(questionnaire, 'incident_response_process', 'Incident response process')}")
    lines.append(f"- **Overrides requiring a reason:** {sum(1 for r in policy.gate_rules if r.require_reason_on_override)}/{len(policy.gate_rules)} gate rule(s)")
    lines.append("- See `aiactguard.reports.incident_report` for drafting incident reports from flagged records.")

    return "\n".join(lines)
