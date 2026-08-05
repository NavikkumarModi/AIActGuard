from __future__ import annotations

from ..storage.base import AuditRecord


def format_record(record: AuditRecord) -> str:
    """Render one audit record as an auditor-readable Markdown block (Art. 13).

    This structures whatever chain-of-reasoning/tool-selection rationale was
    captured alongside the decision facts already in the audit trail — it
    doesn't invent an explanation the system didn't actually produce.
    """
    lines = [
        f"### {record.action}",
        f"- **Timestamp:** {record.timestamp}",
        f"- **Category:** {record.category}",
        f"- **Risk tier:** {record.risk_tier}",
        f"- **Gated:** {'yes' if record.gated else 'no'}",
        f"- **Outcome:** {'approved' if record.approved else 'denied'}",
    ]

    if record.gated:
        lines.append(f"- **Approver:** {record.approver_id or 'n/a'}")
        if record.override:
            lines.append(f"- **Override:** yes — {record.reason or 'no reason recorded'}")
        elif record.reason:
            lines.append(f"- **Reason:** {record.reason}")

    if record.error:
        lines.append(f"- **Error:** {record.error}")

    if record.rationale:
        lines.append("- **Rationale:**")
        for step in record.rationale:
            source = step.get("source", "unknown")
            text = step.get("text", "")
            lines.append(f"  - _{source}_: {text}")

    return "\n".join(lines)
