"""A worked example of the plugin architecture: a toy pharma/GxP module —
literally the example the project plan itself suggests as a natural
community contribution.

Requires: pip install aiactguard
"""

from dataclasses import dataclass
from typing import Any, Optional

from aiactguard import plugins
from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.audit_summary import summarize
from aiactguard.core.questionnaire import Questionnaire, render_field
from aiactguard.storage.sqlite_store import SQLiteAuditStore


@dataclass
class GxPComputerizedSystemPlugin:
    """Maps audit-trail evidence onto a GxP computerized-system-validation
    style summary (21 CFR Part 11 / EU Annex 11 flavored) — a jurisdiction-
    and industry-specific module of exactly the kind Phase 4's plugin
    architecture is meant to make easy to contribute."""

    name: str = "gxp_computerized_system_summary"
    description: str = "Pharma GxP computerized-system-validation evidence summary"

    def generate(
        self,
        logger: AuditLogger,
        *,
        questionnaire: Optional[Questionnaire] = None,
        **kwargs: Any,
    ) -> str:
        records = logger.query(limit=10_000)
        summary = summarize(records)

        lines = ["# GxP computerized system summary (community plugin draft)", ""]
        lines.append(f"- **System name:** {render_field(questionnaire, 'system_name', 'System name')}")
        lines.append(f"- **Validation owner (QA):** {render_field(questionnaire, 'validation_owner', 'Validation owner (QA)')}")
        lines.append(f"- **Audit trail entries reviewed:** {summary.total_actions}")
        lines.append(f"- **Electronic-record change events (gated/override):** {summary.gated_count} / {summary.override_count}")
        lines.append("")
        lines.append("> Community plugin draft — not part of AIActGuard core; adapt to your actual GxP SOPs before use.")
        return "\n".join(lines)


plugin = GxPComputerizedSystemPlugin()

if __name__ == "__main__":
    plugins.register(plugin)
    print("Registered plugins:", plugins.list_plugins())

    logger = AuditLogger(store=SQLiteAuditStore("gxp_demo_audit.db"))
    output = plugins.get("gxp_computerized_system_summary").generate(
        logger,
        questionnaire={"system_name": "Batch Release Assistant", "validation_owner": "QA Lead"},
    )
    print(output)
