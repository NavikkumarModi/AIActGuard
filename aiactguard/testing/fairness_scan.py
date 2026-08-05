from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..core.audit_logger import AuditLogger
from ..storage.base import AuditRecord


@dataclass
class GroupOutcome:
    group: str
    approved: bool


@dataclass
class FairnessScanResult:
    """A statistical disparity check on runtime decisions grouped by a
    caller-supplied proxy attribute — NOT a determination that the system
    is or isn't discriminatory, and NOT training-data governance (out of
    scope for this module; see the doc's own scope note for Art. 10)."""

    threshold: float
    selection_rates: dict[str, float] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    disparate_impact_ratio: Optional[float] = None
    flagged: bool = False

    def to_markdown(self) -> str:
        lines = [
            "# Bias & fairness scan (Art. 10 draft)",
            "",
            "> Statistical check on runtime decisions grouped by whatever proxy "
            "attribute was supplied to this scan — it does not know about real "
            "protected characteristics unless you told it, and it does not "
            "cover training-data bias.",
            "",
            f"**Threshold (four-fifths-rule style):** {self.threshold}",
        ]
        if self.disparate_impact_ratio is not None:
            lines.append(f"**Disparate impact ratio (min/max selection rate):** {self.disparate_impact_ratio:.2f}")
            lines.append(f"**Flagged:** {'yes — below threshold' if self.flagged else 'no'}")
        else:
            lines.append("**Disparate impact ratio:** n/a (fewer than 2 groups with data)")
        lines.append("")
        lines.append("## Selection rates by group")
        for group, rate in sorted(self.selection_rates.items()):
            lines.append(f"- {group}: {rate:.0%} approved ({self.counts.get(group, 0)} decision(s))")
        return "\n".join(lines)


def compute_disparate_impact(outcomes: list[GroupOutcome], *, threshold: float = 0.8) -> FairnessScanResult:
    if not outcomes:
        return FairnessScanResult(threshold=threshold)

    counts: Counter[str] = Counter()
    approvals: Counter[str] = Counter()
    for outcome in outcomes:
        counts[outcome.group] += 1
        if outcome.approved:
            approvals[outcome.group] += 1

    selection_rates = {group: approvals[group] / counts[group] for group in counts}

    if len(selection_rates) < 2:
        return FairnessScanResult(threshold=threshold, selection_rates=selection_rates, counts=dict(counts))

    max_rate = max(selection_rates.values())
    min_rate = min(selection_rates.values())
    ratio = (min_rate / max_rate) if max_rate > 0 else 1.0

    return FairnessScanResult(
        threshold=threshold,
        selection_rates=selection_rates,
        counts=dict(counts),
        disparate_impact_ratio=ratio,
        flagged=ratio < threshold,
    )


def scan_audit_trail(
    logger: AuditLogger,
    *,
    group_key: Callable[[AuditRecord], Optional[str]],
    category: Optional[str] = None,
    threshold: float = 0.8,
) -> FairnessScanResult:
    """Run a disparate-impact scan over the audit trail. `group_key` extracts
    the proxy group label from each record (return None to exclude a record
    from the scan) — this is where you decide what proxy attribute to check,
    e.g. reading it back out of `record.inputs`.
    """
    records = logger.query(category=category, limit=10_000)
    outcomes = []
    for record in records:
        group = group_key(record)
        if group is not None:
            outcomes.append(GroupOutcome(group=group, approved=record.approved))

    return compute_disparate_impact(outcomes, threshold=threshold)
