from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
from ..core.questionnaire import Questionnaire


@dataclass
class ChecklistItem:
    requirement: str
    article: str
    status: str  # "met" | "gap"
    evidence: str


@dataclass
class ConformityChecklistResult:
    items: list[ChecklistItem]

    @property
    def gaps(self) -> list[ChecklistItem]:
        return [i for i in self.items if i.status == "gap"]

    def to_markdown(self) -> str:
        lines = [
            "# Conformity readiness checklist (pre-assessment aid)",
            "",
            "> This is a gap-analysis against logged evidence, not a conformity "
            "assessment — it doesn't determine whether the system actually "
            "conforms, only whether the supporting evidence this generator can "
            "see is in place.",
            "",
        ]
        for item in self.items:
            mark = "x" if item.status == "met" else " "
            lines.append(f"- [{mark}] **{item.requirement}** ({item.article}) — {item.evidence}")
        if self.gaps:
            lines.append("")
            lines.append(f"**{len(self.gaps)} gap(s) found** — see unchecked items above.")
        return "\n".join(lines)


def generate_conformity_checklist(
    logger: AuditLogger,
    *,
    questionnaire: Optional[Questionnaire] = None,
) -> ConformityChecklistResult:
    """Check logged evidence against a set of Annex IV/VI-style requirements
    and flag what's missing. A pre-assessment aid, not the assessment itself
    (Art. 43) — conformity assessment requires formal procedures this tool
    doesn't perform.
    """
    questionnaire = questionnaire or {}
    records = logger.query(limit=10_000)
    summary = summarize(records)

    items = [
        ChecklistItem(
            requirement="Audit trail covers logged actions",
            article="Art. 12",
            status="met" if summary.total_actions > 0 else "gap",
            evidence=f"{summary.total_actions} action(s) logged"
            if summary.total_actions
            else "No audit records found — instrument the agent with watch()/an adapter first",
        ),
        ChecklistItem(
            requirement="Risk classification applied to high-risk actions",
            article="Art. 6, Annex III",
            status="met" if summary.by_risk_tier else "gap",
            evidence=f"Risk tiers observed: {', '.join(sorted(summary.by_risk_tier)) or 'none'}",
        ),
        ChecklistItem(
            requirement="Human oversight gates configured for high-risk actions",
            article="Art. 14",
            status="met" if summary.gated_count > 0 else "gap",
            evidence=f"{summary.gated_count} gated action(s) logged",
        ),
        ChecklistItem(
            requirement="Override decisions carry a recorded reason",
            article="Art. 14",
            status="met" if summary.override_count == 0 or questionnaire.get("overrides_reviewed") else "gap",
            evidence=f"{summary.override_count} override(s) logged"
            + ("" if summary.override_count == 0 else " — confirm these were human-reviewed"),
        ),
        ChecklistItem(
            requirement="System description documented",
            article="Annex IV",
            status="met" if questionnaire.get("system_name") and questionnaire.get("intended_purpose") else "gap",
            evidence="Provided via questionnaire" if questionnaire.get("system_name") else "Missing system_name/intended_purpose",
        ),
        ChecklistItem(
            requirement="Data governance summary documented",
            article="Annex IV",
            status="met" if questionnaire.get("data_governance_summary") else "gap",
            evidence="Provided via questionnaire" if questionnaire.get("data_governance_summary") else "Missing data_governance_summary",
        ),
        ChecklistItem(
            requirement="Post-market monitoring plan drafted",
            article="Art. 72",
            status="met" if questionnaire.get("post_market_monitoring_plan_drafted") else "gap",
            evidence="Confirmed via questionnaire" if questionnaire.get("post_market_monitoring_plan_drafted") else "Run generate_post_market_monitoring_plan() and confirm here",
        ),
        ChecklistItem(
            requirement="Fundamental Rights Impact Assessment drafted (if applicable)",
            article="Art. 27",
            status="met" if questionnaire.get("fria_drafted") else "gap",
            evidence="Confirmed via questionnaire" if questionnaire.get("fria_drafted") else "Run generate_fria() if this system is a banking/insurance/public-service deployer",
        ),
    ]

    return ConformityChecklistResult(items=items)
