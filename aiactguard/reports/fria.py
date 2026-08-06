from __future__ import annotations

from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
from ..core.markdown import MarkdownReport
from ..core.questionnaire import Questionnaire, missing_fields, render_field
from ..policy.schema import PolicyConfig

REQUIRED_FIELDS = (
    ("deployer_name", "Deployer name"),
    ("deployment_context", "Deployment context"),
    ("affected_groups", "Groups of natural persons likely affected"),
    ("fundamental_rights_at_stake", "Fundamental rights potentially at stake"),
)


def generate_fria(
    logger: AuditLogger,
    *,
    questionnaire: Questionnaire,
    category: Optional[str] = None,
    policy: Optional[PolicyConfig] = None,
) -> str:
    """Pre-fill a Fundamental Rights Impact Assessment draft (Art. 27) from
    the system's risk classification and deployment context. Required for
    deployers in banking, insurance, and public-service high-risk use cases.

    The parts a FRIA actually needs — who's affected, what rights are at
    stake, the deployment context — can't be inferred from code and must
    come from the questionnaire; this only pre-fills the parts the system
    already knows about itself.
    """
    policy = policy or PolicyConfig.default()
    records = logger.query(category=category, limit=10_000)
    summary = summarize(records)

    gaps = missing_fields(questionnaire, list(REQUIRED_FIELDS))

    out = MarkdownReport("Fundamental Rights Impact Assessment (Art. 27 draft)")
    if gaps:
        out.note(f"**{len(gaps)} required field(s) missing:** {', '.join(gaps)}. This draft is incomplete until they're filled in.")

    out.heading("1. Deployer & deployment context")
    for key, label in (("deployer_name", "Deployer name"), ("deployment_context", "Deployment context")):
        out.field(label, render_field(questionnaire, key, label))
    out.blank()

    out.heading("2. Affected persons and rights")
    out.field("Groups likely affected", render_field(questionnaire, "affected_groups", "Groups of natural persons likely affected"))
    out.field("Fundamental rights at stake", render_field(questionnaire, "fundamental_rights_at_stake", "Fundamental rights potentially at stake"))
    out.blank()

    out.heading("3. Risk classification (from the system)")
    if summary.by_risk_tier:
        for tier, count in sorted(summary.by_risk_tier.items()):
            out.bullet(f"{tier}: {count} action(s) logged")
    else:
        out.bullet("No audit records found for this category yet.")
    out.blank()

    out.heading("4. Mitigation measures (from policy-as-code)")
    if policy.gate_rules:
        for rule in policy.gate_rules:
            scope = ", ".join(rule.categories) if rule.categories else "all categories"
            out.bullet(
                f"Human approval gate at risk tier >= {rule.min_risk_tier.value} ({scope}); "
                f"override requires reason: {rule.require_reason_on_override}"
            )
    else:
        out.bullet("No gate rules configured — a FRIA-relevant system should generally have at least one.")
    out.blank()

    out.note(
        "This draft covers what the system can evidence about itself. The "
        "deployer's legal/compliance function must review and complete it "
        "before it's usable as an actual FRIA filing."
    )

    return out.build()
