from __future__ import annotations

from ..storage.base import AuditRecord
from ._questionnaire import Questionnaire, missing_fields, render_field

REQUIRED_FIELDS = (
    ("incident_description", "What happened"),
    ("harm_caused", "Harm caused (if any)"),
    ("affected_persons", "Affected persons"),
    ("root_cause", "Root cause"),
    ("corrective_actions", "Corrective actions taken/planned"),
)


def draft_incident_report(record: AuditRecord, *, questionnaire: Questionnaire) -> str:
    """Turn a flagged incident — a gate override, a denied action, a
    user-reported harm — into a structured draft matching a serious
    incident report format (Art. 73), for human review before filing.

    `record` is the flagged AuditRecord; `questionnaire` supplies what only
    a human reviewing the incident knows (harm assessment, root cause,
    corrective actions).
    """
    gaps = missing_fields(questionnaire, list(REQUIRED_FIELDS))

    lines = ["# Serious incident report (Art. 73 draft)", ""]
    if gaps:
        lines.append(f"> **{len(gaps)} required field(s) missing:** {', '.join(gaps)}. This draft is incomplete until they're filled in.")
        lines.append("")

    lines.append("## 1. What happened")
    lines.append(f"- **Action:** {record.action}")
    lines.append(f"- **Timestamp:** {record.timestamp}")
    lines.append(f"- **Category / risk tier:** {record.category} / {record.risk_tier}")
    lines.append(f"- **Description:** {render_field(questionnaire, 'incident_description', 'What happened')}")
    lines.append("")

    lines.append("## 2. Human oversight involved")
    lines.append(f"- **Gated:** {'yes' if record.gated else 'no'}")
    lines.append(f"- **Outcome:** {'approved' if record.approved else 'denied'}")
    if record.gated:
        lines.append(f"- **Approver:** {record.approver_id or 'n/a'}")
        if record.override:
            lines.append(f"- **Override:** yes — {record.reason or 'no reason recorded'}")
    if record.error:
        lines.append(f"- **System-recorded error:** {record.error}")
    lines.append("")

    lines.append("## 3. Harm assessment")
    lines.append(f"- **Harm caused:** {render_field(questionnaire, 'harm_caused', 'Harm caused (if any)')}")
    lines.append(f"- **Affected persons:** {render_field(questionnaire, 'affected_persons', 'Affected persons')}")
    lines.append("")

    lines.append("## 4. Root cause & corrective actions")
    lines.append(f"- **Root cause:** {render_field(questionnaire, 'root_cause', 'Root cause')}")
    lines.append(f"- **Corrective actions:** {render_field(questionnaire, 'corrective_actions', 'Corrective actions taken/planned')}")
    lines.append("")

    lines.append("> Draft only — review and complete before filing via the actual incident-reporting process.")

    return "\n".join(lines)
