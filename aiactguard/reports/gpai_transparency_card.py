from __future__ import annotations

from collections import Counter
from typing import Optional

from ..core.audit_logger import AuditLogger
from ._questionnaire import Questionnaire, render_field

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

    lines = ["# GPAI transparency card (Art. 53 draft)", ""]

    lines.append("## 1. Model identity")
    for key, label in (("model_name", "Model name"), ("provider", "Provider")):
        lines.append(f"- **{label}:** {render_field(questionnaire, key, label)}")
    lines.append("")

    lines.append("## 2. Capabilities, limitations, and known risks")
    lines.append(f"- **Capabilities:** {render_field(questionnaire, 'capabilities', 'Capabilities')}")
    lines.append(f"- **Known limitations:** {render_field(questionnaire, 'known_limitations', 'Known limitations')}")
    lines.append(f"- **Known risks:** {render_field(questionnaire, 'known_risks', 'Known risks')}")
    lines.append("")

    lines.append("## 3. Observed usage (from the audit trail)")
    if usage:
        for model_version, count in usage.most_common():
            lines.append(f"- {model_version}: {count} logged call(s)")
    else:
        lines.append("- No `model_version` recorded on any audit record yet — pass `model_version=` when constructing your adapter/GuardCore.")
    lines.append("")

    lines.append("> Summarizes this deployment's own use of the model; does not substitute for the model provider's own transparency documentation.")

    return "\n".join(lines)
