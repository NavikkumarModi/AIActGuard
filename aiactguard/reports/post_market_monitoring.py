from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
from ..core.questionnaire import Questionnaire, render_field


def generate_post_market_monitoring_plan(
    logger: AuditLogger,
    *,
    questionnaire: Optional[Questionnaire] = None,
    category: Optional[str] = None,
) -> str:
    """Produce a post-market monitoring plan template (Art. 72), scaffolded
    from the system's risk tier distribution and the incident-like events
    (denials, overrides) already in the audit trail.

    This is a template to operate against, not a substitute for actually
    running the monitoring process it describes.
    """
    records = logger.query(category=category, limit=10_000)
    summary = summarize(records)

    lines = ["# Post-market monitoring plan (Art. 72 draft)", ""]

    lines.append("## 1. Scope")
    lines.append(f"- **System:** {render_field(questionnaire, 'system_name', 'System name')}")
    lines.append(f"- **Monitoring window logged so far:** {summary.earliest_timestamp or 'n/a'} to {summary.latest_timestamp or 'n/a'}")
    lines.append(f"- **Total actions observed:** {summary.total_actions}")
    lines.append("")

    lines.append("## 2. Monitored signals")
    lines.append(f"- **Risk tier distribution:** {summary.by_risk_tier or 'no data yet'}")
    lines.append(f"- **Gated (high-risk) actions:** {summary.gated_count}")
    lines.append(f"- **Denials:** {summary.denied_count}")
    lines.append(f"- **Overrides of a gate decision:** {summary.override_count}")
    lines.append("")

    lines.append("## 3. Incident categories to track going forward")
    lines.append("- Denied actions with no configured approver (escalation chain gap)")
    lines.append("- Overrides without a substantive reason (policy violation — should already be blocked by `require_reason_on_override`)")
    lines.append("- A sustained rise in `high`/`unacceptable`-tier classifications for a previously `limited`/`minimal` category (taxonomy drift)")
    lines.append("")

    lines.append("## 4. Review cadence")
    lines.append(f"- **Cadence:** {render_field(questionnaire, 'review_cadence', 'Review cadence (e.g. weekly/monthly)')}")
    lines.append(f"- **Owner:** {render_field(questionnaire, 'monitoring_owner', 'Monitoring plan owner')}")
    lines.append("")

    lines.append(
        "> Query `AuditLogger.query()` on the cadence above and review the "
        "signals in section 2 against this plan; feed confirmed incidents "
        "into a serious incident report (Art. 73, Phase 3)."
    )

    return "\n".join(lines)
