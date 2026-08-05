from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.explainability import format_record
from ..core.risk_classifier import RiskClassifier
from ..core.audit_summary import summarize
from ..core.questionnaire import Questionnaire, render_field

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

    lines = ["# Technical Documentation (Art. 11 / Annex IV draft)", ""]
    lines.append(
        "> Auto-drafted from the audit trail and the questionnaire supplied to "
        "this generator. Every `NEEDS INPUT` marker below must be filled in "
        "and the whole document reviewed by a human before filing — this "
        "tool drafts, it does not certify."
    )
    lines.append("")

    lines.append("## 1. System overview")
    for key, label in REQUIRED_FIELDS:
        lines.append(f"- **{label}:** {render_field(questionnaire, key, label)}")
    lines.append("")

    lines.append("## 2. Risk classification summary")
    lines.append(f"- **Annex III categories configured:** {', '.join(classifier.categories()) or 'none'}")
    lines.append(f"- **Actions logged:** {summary.total_actions}")
    if summary.by_risk_tier:
        lines.append("- **By risk tier:**")
        for tier, count in sorted(summary.by_risk_tier.items()):
            lines.append(f"  - {tier}: {count}")
    if summary.earliest_timestamp:
        lines.append(f"- **Coverage window:** {summary.earliest_timestamp} to {summary.latest_timestamp}")
    lines.append("")

    lines.append("## 3. Human oversight measures")
    lines.append(f"- **Gated actions:** {summary.gated_count}")
    lines.append(f"- **Approved:** {summary.approved_count} | **Denied:** {summary.denied_count}")
    lines.append(f"- **Overrides logged (with reason):** {summary.override_count}")
    lines.append(
        f"- **Oversight process description:** "
        f"{render_field(questionnaire, 'human_oversight_measures', 'Human oversight measures')}"
    )
    lines.append("")

    lines.append("## 4. Data & performance")
    lines.append(f"- **Data governance:** {render_field(questionnaire, 'data_governance_summary', 'Data governance summary')}")
    if summary.by_category:
        lines.append("- **Actions by category:**")
        for cat, count in sorted(summary.by_category.items()):
            lines.append(f"  - {cat}: {count}")
    lines.append("")

    gated_examples = [r for r in records if r.gated][:3]
    if gated_examples:
        lines.append("## 5. Explainability — worked examples")
        for record in gated_examples:
            lines.append(format_record(record))
            lines.append("")

    return "\n".join(lines)
