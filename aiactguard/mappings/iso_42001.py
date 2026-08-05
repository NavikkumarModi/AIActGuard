from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
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

    lines = ["# ISO/IEC 42001 mapping", ""]

    lines.append("## Clause 4 — Context of the organization")
    lines.append(f"- **System scope:** {render_field(questionnaire, 'system_name', 'System name')}")
    lines.append(f"- **Intended purpose:** {render_field(questionnaire, 'intended_purpose', 'Intended purpose')}")
    lines.append("")

    lines.append("## Clause 5 — Leadership & policy")
    lines.append(f"- **AI policy owner:** {render_field(questionnaire, 'policy_owner', 'Policy owner')}")
    lines.append("")

    lines.append("## Clause 6 — Risk assessment & treatment")
    lines.append(f"- **Risk categories in scope:** {', '.join(sorted(summary.by_category)) or 'none logged yet'}")
    if policy.gate_rules:
        for rule in policy.gate_rules:
            scope = ", ".join(rule.categories) if rule.categories else "all categories"
            lines.append(f"- Treatment control: human-approval gate at risk tier >= {rule.min_risk_tier.value} ({scope})")
    lines.append("")

    lines.append("## Clause 8 — Operational controls")
    lines.append(f"- **Actions logged:** {summary.total_actions}")
    lines.append(f"- **Gated actions:** {summary.gated_count} | **Overrides:** {summary.override_count}")
    lines.append("")

    lines.append("## Clause 9 — Performance evaluation")
    lines.append(f"- **Denials:** {summary.denied_count}")
    if summary.earliest_timestamp:
        lines.append(f"- **Evaluation window:** {summary.earliest_timestamp} to {summary.latest_timestamp}")
    lines.append("")

    lines.append("## Clause 10 — Improvement")
    lines.append(f"- **Corrective action process:** {render_field(questionnaire, 'corrective_action_process', 'Corrective action process')}")
    lines.append("- See `aiactguard.reports.incident_report` and `aiactguard.reports.post_market_monitoring` for the underlying corrective-action inputs.")

    return "\n".join(lines)
