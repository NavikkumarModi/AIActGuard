from __future__ import annotations

from ..core.markdown import MarkdownReport
from ..core.questionnaire import Questionnaire, missing_fields, render_field
from ..storage.base import AuditRecord

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

    out = MarkdownReport("Serious incident report (Art. 73 draft)")
    if gaps:
        out.note(f"**{len(gaps)} required field(s) missing:** {', '.join(gaps)}. This draft is incomplete until they're filled in.")

    out.heading("1. What happened")
    out.field("Action", record.action)
    out.field("Timestamp", record.timestamp)
    out.field("Category / risk tier", f"{record.category} / {record.risk_tier}")
    out.field("Description", render_field(questionnaire, "incident_description", "What happened"))
    out.blank()

    out.heading("2. Human oversight involved")
    out.field("Gated", "yes" if record.gated else "no")
    out.field("Outcome", "approved" if record.approved else "denied")
    if record.gated:
        out.field("Approver", record.approver_id or "n/a")
        if record.override:
            out.field("Override", f"yes — {record.reason or 'no reason recorded'}")
    if record.error:
        out.field("System-recorded error", record.error)
    out.blank()

    out.heading("3. Harm assessment")
    out.field("Harm caused", render_field(questionnaire, "harm_caused", "Harm caused (if any)"))
    out.field("Affected persons", render_field(questionnaire, "affected_persons", "Affected persons"))
    out.blank()

    out.heading("4. Root cause & corrective actions")
    out.field("Root cause", render_field(questionnaire, "root_cause", "Root cause"))
    out.field("Corrective actions", render_field(questionnaire, "corrective_actions", "Corrective actions taken/planned"))
    out.blank()

    out.note("Draft only — review and complete before filing via the actual incident-reporting process.")

    return out.build()
