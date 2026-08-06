from __future__ import annotations

from .markdown import MarkdownReport
from ..storage.base import AuditRecord


def format_record(record: AuditRecord) -> str:
    """Render one audit record as an auditor-readable Markdown block (Art. 13).

    This structures whatever chain-of-reasoning/tool-selection rationale was
    captured alongside the decision facts already in the audit trail — it
    doesn't invent an explanation the system didn't actually produce.
    """
    out = (
        MarkdownReport()
        .line(f"### {record.action}")
        .field("Timestamp", record.timestamp)
        .field("Category", record.category)
        .field("Risk tier", record.risk_tier)
        .field("Gated", "yes" if record.gated else "no")
        .field("Outcome", "approved" if record.approved else "denied")
    )

    if record.gated:
        out.field("Approver", record.approver_id or "n/a")
        if record.override:
            out.field("Override", f"yes — {record.reason or 'no reason recorded'}")
        elif record.reason:
            out.field("Reason", record.reason)

    if record.error:
        out.field("Error", record.error)

    if record.rationale:
        out.bullet("**Rationale:**")
        for step in record.rationale:
            out.sub_bullet(f"_{step.get('source', 'unknown')}_: {step.get('text', '')}")

    return out.build()
