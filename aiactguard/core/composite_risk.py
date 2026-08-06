from __future__ import annotations

from dataclasses import dataclass, field

from ..storage.base import AuditRecord
from .markdown import MarkdownReport
from .risk_classifier import RiskTier

_TIER_ORDER = [RiskTier.MINIMAL, RiskTier.LIMITED, RiskTier.HIGH, RiskTier.UNACCEPTABLE]


@dataclass
class PipelineStep:
    name: str
    category: str
    risk_tier: RiskTier


@dataclass
class CompositeRiskResult:
    steps: list[PipelineStep]
    max_individual_tier: RiskTier
    distinct_categories: list[str] = field(default_factory=list)
    composite_tier: RiskTier = RiskTier.MINIMAL
    escalated: bool = False
    reason: str = ""

    def to_markdown(self) -> str:
        out = (
            MarkdownReport("Composite-system risk aggregation")
            .note(
                "Heuristic: flags when a pipeline's category fan-out suggests the "
                "system as a whole may carry more risk than any single step — not "
                "a formal systemic-risk determination."
            )
            .field("Steps analyzed", len(self.steps))
            .field("Distinct Annex III categories", ", ".join(self.distinct_categories) or "none")
            .field("Highest individual step tier", self.max_individual_tier.value)
            .field("Composite tier", self.composite_tier.value)
            .field("Escalated", "yes" if self.escalated else "no")
            .field("Reason", self.reason)
            .blank()
            .heading("Steps")
        )
        for step in self.steps:
            out.bullet(f"`{step.name}` — {step.category} ({step.risk_tier.value})")
        return out.build()


def analyze_pipeline(steps: list[PipelineStep], *, category_fanout_threshold: int = 2) -> CompositeRiskResult:
    """Flag when multiple individually low(er)-risk steps, composed into a
    pipeline, may cross into higher-risk territory as a system — the doc's
    "genuinely novel piece": no existing tool checks for this.

    Heuristic only: if the pipeline spans `>= category_fanout_threshold`
    distinct Annex III categories, the composite tier is bumped one level
    above the highest individual step's tier. A single-category pipeline,
    however long, is never escalated by this rule alone.
    """
    if not steps:
        return CompositeRiskResult(
            steps=[],
            max_individual_tier=RiskTier.MINIMAL,
            distinct_categories=[],
            composite_tier=RiskTier.MINIMAL,
            escalated=False,
            reason="No steps supplied.",
        )

    max_individual_tier = max(steps, key=lambda s: _TIER_ORDER.index(s.risk_tier)).risk_tier
    distinct_categories = sorted({s.category for s in steps})
    fans_out = len(distinct_categories) >= category_fanout_threshold
    max_index = _TIER_ORDER.index(max_individual_tier)

    if fans_out and max_index < len(_TIER_ORDER) - 1:
        composite_tier = _TIER_ORDER[max_index + 1]
        escalated = True
        reason = (
            f"Pipeline spans {len(distinct_categories)} distinct Annex III categories "
            f"({', '.join(distinct_categories)}); composite risk bumped one tier above "
            f"the highest individual step ({max_individual_tier.value} -> {composite_tier.value})."
        )
    elif fans_out:
        composite_tier = max_individual_tier
        escalated = False
        reason = f"Pipeline spans {len(distinct_categories)} categories but the highest step is already at the top tier."
    else:
        composite_tier = max_individual_tier
        escalated = False
        reason = "No cross-category fan-out detected; composite tier equals the highest individual step's tier."

    return CompositeRiskResult(
        steps=steps,
        max_individual_tier=max_individual_tier,
        distinct_categories=distinct_categories,
        composite_tier=composite_tier,
        escalated=escalated,
        reason=reason,
    )


def pipeline_steps_from_records(records: list[AuditRecord]) -> list[PipelineStep]:
    """Convert real audit trail output into pipeline steps, so
    `analyze_pipeline` can run against what actually happened rather than
    only a hand-built scenario."""
    return [PipelineStep(name=r.action, category=r.category, risk_tier=RiskTier(r.risk_tier)) for r in records]
