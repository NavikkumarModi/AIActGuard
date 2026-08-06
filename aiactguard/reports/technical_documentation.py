from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
from ..core.explainability import format_record
from ..core.markdown import MarkdownReport
from ..core.questionnaire import Questionnaire, render_field
from ..core.risk_classifier import RiskClassifier

REQUIRED_FIELDS = (
    ("system_name", "System name"),
    ("intended_purpose", "Intended purpose"),
    ("deployment_context", "Deployment context"),
    ("data_governance_summary", "Data governance summary"),
    ("human_oversight_measures", "Human oversight measures"),
)


def generate_technical_documentation(
    logger: AuditLogger,
    *,
    questionnaire: Optional[Questionnaire] = None,
    category: Optional[str] = None,
    classifier: Optional[RiskClassifier] = None,
) -> str:
    """Draft an Annex IV-style technical documentation file (Art. 11) from
    the audit trail plus a guided questionnaire for what code can't infer
    (system description, intended purpose, deployment context, ...).

    This is a drafting aid, not the technical documentation itself — an
    Annex IV filing needs a human review pass over every section below.
    """
    classifier = classifier or RiskClassifier.default()
    records = logger.query(category=category, limit=10_000)
    summary = summarize(records)

    out = MarkdownReport("Technical Documentation (Art. 11 / Annex IV draft)").note(
        "Auto-drafted from the audit trail and the questionnaire supplied to "
        "this generator. Every `NEEDS INPUT` marker below must be filled in "
        "and the whole document reviewed by a human before filing — this "
        "tool drafts, it does not certify."
    )

    out.heading("1. System overview")
    for key, label in REQUIRED_FIELDS:
        out.field(label, render_field(questionnaire, key, label))
    out.blank()

    out.heading("2. Risk classification summary")
    out.field("Annex III categories configured", ", ".join(classifier.categories()) or "none")
    out.field("Actions logged", summary.total_actions)
    if summary.by_risk_tier:
        out.bullet("**By risk tier:**")
        for tier, count in sorted(summary.by_risk_tier.items()):
            out.sub_bullet(f"{tier}: {count}")
    if summary.earliest_timestamp:
        out.field("Coverage window", f"{summary.earliest_timestamp} to {summary.latest_timestamp}")
    out.blank()

    out.heading("3. Human oversight measures")
    out.field("Gated actions", summary.gated_count)
    out.field("Approved", f"{summary.approved_count} | **Denied:** {summary.denied_count}")
    out.field("Overrides logged (with reason)", summary.override_count)
    out.field(
        "Oversight process description",
        render_field(questionnaire, "human_oversight_measures", "Human oversight measures"),
    )
    out.blank()

    out.heading("4. Data & performance")
    out.field("Data governance", render_field(questionnaire, "data_governance_summary", "Data governance summary"))
    if summary.by_category:
        out.bullet("**Actions by category:**")
        for cat, count in sorted(summary.by_category.items()):
            out.sub_bullet(f"{cat}: {count}")
    out.blank()

    gated_examples = [r for r in records if r.gated][:3]
    if gated_examples:
        out.heading("5. Explainability — worked examples")
        for record in gated_examples:
            out.line(format_record(record))
            out.blank()

    return out.build()
