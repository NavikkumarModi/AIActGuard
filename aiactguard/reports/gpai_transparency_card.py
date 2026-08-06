from __future__ import annotations

from collections import Counter
from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.markdown import MarkdownReport
from ..core.questionnaire import Questionnaire, render_field

REQUIRED_FIELDS = (
    ("model_name", "Model name"),
    ("provider", "Provider"),
    ("capabilities", "Capabilities"),
    ("known_limitations", "Known limitations"),
    ("known_risks", "Known risks"),
)


def generate_gpai_transparency_card(
    logger: AuditLogger,
    *,
    questionnaire: Optional[Questionnaire] = None,
    category: Optional[str] = None,
) -> str:
    """Generate a model transparency summary (Art. 53) for a team building
    *on top of* a general-purpose AI model — this documents your own usage
    of the model (which model, how often, for what), not the GPAI
    provider's own systemic-risk obligations (out of scope; those apply to
    the frontier model provider, not agent builders — see the README).
    """
    records = logger.query(category=category, limit=10_000)
    usage = Counter(r.model_version for r in records if r.model_version)

    out = MarkdownReport("GPAI transparency card (Art. 53 draft)")

    out.heading("1. Model identity")
    for key, label in (("model_name", "Model name"), ("provider", "Provider")):
        out.field(label, render_field(questionnaire, key, label))
    out.blank()

    out.heading("2. Capabilities, limitations, and known risks")
    out.field("Capabilities", render_field(questionnaire, "capabilities", "Capabilities"))
    out.field("Known limitations", render_field(questionnaire, "known_limitations", "Known limitations"))
    out.field("Known risks", render_field(questionnaire, "known_risks", "Known risks"))
    out.blank()

    out.heading("3. Observed usage (from the audit trail)")
    if usage:
        for model_version, count in usage.most_common():
            out.bullet(f"{model_version}: {count} logged call(s)")
    else:
        out.bullet("No `model_version` recorded on any audit record yet — pass `model_version=` when constructing your adapter/GuardCore.")
    out.blank()

    out.note("Summarizes this deployment's own use of the model; does not substitute for the model provider's own transparency documentation.")

    return out.build()
