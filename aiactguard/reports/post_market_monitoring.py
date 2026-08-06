from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
from ..core.markdown import MarkdownReport
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

    out = MarkdownReport("Post-market monitoring plan (Art. 72 draft)")

    out.heading("1. Scope")
    out.field("System", render_field(questionnaire, "system_name", "System name"))
    out.field("Monitoring window logged so far", f"{summary.earliest_timestamp or 'n/a'} to {summary.latest_timestamp or 'n/a'}")
    out.field("Total actions observed", summary.total_actions)
    out.blank()

    out.heading("2. Monitored signals")
    out.field("Risk tier distribution", summary.by_risk_tier or "no data yet")
    out.field("Gated (high-risk) actions", summary.gated_count)
    out.field("Denials", summary.denied_count)
    out.field("Overrides of a gate decision", summary.override_count)
    out.blank()

    out.heading("3. Incident categories to track going forward")
    out.bullet("Denied actions with no configured approver (escalation chain gap)")
    out.bullet("Overrides without a substantive reason (policy violation — should already be blocked by `require_reason_on_override`)")
    out.bullet("A sustained rise in `high`/`unacceptable`-tier classifications for a previously `limited`/`minimal` category (taxonomy drift)")
    out.blank()

    out.heading("4. Review cadence")
    out.field("Cadence", render_field(questionnaire, "review_cadence", "Review cadence (e.g. weekly/monthly)"))
    out.field("Owner", render_field(questionnaire, "monitoring_owner", "Monitoring plan owner"))
    out.blank()

    out.note(
        "Query `AuditLogger.query()` on the cadence above and review the "
        "signals in section 2 against this plan; feed confirmed incidents "
        "into a serious incident report (Art. 73, Phase 3)."
    )

    return out.build()
